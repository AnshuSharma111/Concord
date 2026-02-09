from evidence.evidence_model import Evidence, EvidenceType
from typing import List
import os
import json
import yaml


def extract_spec_evidence(file_path: str, content: str) -> List[Evidence]:
    """
    Extract literal, structural evidence from OpenAPI / Swagger specifications.
    This extractor is deterministic and does not infer runtime behavior.
    """
    evidence_list: List[Evidence] = []
    seen: set[tuple] = set()

    def emit(evidence: Evidence):
        key = (
            evidence.type,
            evidence.endpoint,
            evidence.source_location,
            evidence.observation,
        )
        if key in seen:
            return
        seen.add(key)
        evidence_list.append(evidence)

    # --- Parse spec (YAML first, JSON fallback) ---
    try:
        try:
            spec = yaml.safe_load(content)
        except yaml.YAMLError:
            spec = json.loads(content)
    except (yaml.YAMLError, json.JSONDecodeError):
        return []

    if not isinstance(spec, dict):
        return []

    paths = spec.get("paths")
    if not isinstance(paths, dict):
        return []

    HTTP_METHODS = {"get", "post", "put", "delete", "patch", "head", "options"}
    source_file = os.path.basename(file_path)

    for path, path_obj in paths.items():
        if not isinstance(path_obj, dict):
            continue

        # --- Path-level parameters ---
        path_parameters = path_obj.get("parameters", [])
        if not isinstance(path_parameters, list):
            path_parameters = []

        for method, operation in path_obj.items():
            if not isinstance(method, str):
                continue

            method_lc = method.lower()
            if method_lc not in HTTP_METHODS:
                continue

            if not isinstance(operation, dict):
                continue

            endpoint = f"{method_lc.upper()} {path}"
            source_base = f"paths.{path}.{method_lc}"

            # --- Operation-level $ref ---
            if "$ref" in operation:
                emit(
                    Evidence(
                        type=EvidenceType.SPEC_SCHEMA_REF,
                        endpoint=endpoint,
                        observation=f"operation references {operation['$ref']}",
                        source_file=source_file,
                        source_location=f"{source_base}.$ref",
                        raw_snippet=operation["$ref"],
                    )
                )
                continue  # referenced operation replaces inline definition

            # --- Path-level parameters (applied to operation) ---
            for i, param in enumerate(path_parameters):
                if not isinstance(param, dict):
                    continue

                name = param.get("name")
                location = param.get("in")

                if name and location:
                    emit(
                        Evidence(
                            type=EvidenceType.SPEC_PARAMETER,
                            endpoint=endpoint,
                            observation=f"uses path-level parameter '{name}' in {location}",
                            source_file=source_file,
                            source_location=f"paths.{path}.parameters[{i}]",
                            raw_snippet=yaml.safe_dump(param, sort_keys=False),
                        )
                    )

            # --- Operation-level parameters ---
            parameters = operation.get("parameters", [])
            if isinstance(parameters, list):
                for i, param in enumerate(parameters):
                    if not isinstance(param, dict):
                        continue

                    name = param.get("name")
                    location = param.get("in")

                    if name and location:
                        emit(
                            Evidence(
                                type=EvidenceType.SPEC_PARAMETER,
                                endpoint=endpoint,
                                observation=f"defines parameter '{name}' in {location}",
                                source_file=source_file,
                                source_location=f"{source_base}.parameters[{i}]",
                                raw_snippet=yaml.safe_dump(param, sort_keys=False),
                            )
                        )

                    schema = param.get("schema")
                    if isinstance(schema, dict) and "$ref" in schema:
                        emit(
                            Evidence(
                                type=EvidenceType.SPEC_SCHEMA_REF,
                                endpoint=endpoint,
                                observation=(
                                    f"parameter '{name}' schema references {schema['$ref']}"
                                ),
                                source_file=source_file,
                                source_location=f"{source_base}.parameters[{i}].schema.$ref",
                                raw_snippet=schema["$ref"],
                            )
                        )

            # --- Responses (OpenAPI 2 & 3) ---
            responses = operation.get("responses", {})
            if isinstance(responses, dict):
                for status_code, response_obj in responses.items():
                    if not isinstance(response_obj, dict):
                        continue

                    # Include description in observation to capture condition information
                    description = response_obj.get("description", "")
                    if description:
                        observation = f"documents possible response {status_code}: {description}"
                    else:
                        observation = f"documents possible response {status_code}"

                    emit(
                        Evidence(
                            type=EvidenceType.SPEC_RESPONSE,
                            endpoint=endpoint,
                            observation=observation,
                            source_file=source_file,
                            source_location=f"{source_base}.responses.{status_code}",
                            raw_snippet=yaml.safe_dump(response_obj, sort_keys=False),
                        )
                    )

                    # OpenAPI 3: content → schema
                    content_obj = response_obj.get("content", {})
                    if isinstance(content_obj, dict):
                        for mime, media in content_obj.items():
                            if not isinstance(media, dict):
                                continue
                            schema = media.get("schema")
                            if isinstance(schema, dict) and "$ref" in schema:
                                emit(
                                    Evidence(
                                        type=EvidenceType.SPEC_SCHEMA_REF,
                                        endpoint=endpoint,
                                        observation=(
                                            f"response {status_code} schema references "
                                            f"{schema['$ref']}"
                                        ),
                                        source_file=source_file,
                                        source_location=(
                                            f"{source_base}.responses.{status_code}"
                                            f".content.{mime}.schema.$ref"
                                        ),
                                        raw_snippet=schema["$ref"],
                                    )
                                )

                    # OpenAPI 2: schema directly under response
                    schema = response_obj.get("schema")
                    if isinstance(schema, dict) and "$ref" in schema:
                        emit(
                            Evidence(
                                type=EvidenceType.SPEC_SCHEMA_REF,
                                endpoint=endpoint,
                                observation=(
                                    f"response {status_code} schema references "
                                    f"{schema['$ref']}"
                                ),
                                source_file=source_file,
                                source_location=(
                                    f"{source_base}.responses.{status_code}.schema.$ref"
                                ),
                                raw_snippet=schema["$ref"],
                            )
                        )

            # --- Request Body (OpenAPI 3, non-HEAD only) ---
            if method_lc != "head":
                request_body = operation.get("requestBody")
                if isinstance(request_body, dict):
                    emit(
                        Evidence(
                            type=EvidenceType.SPEC_REQUEST_BODY,
                            endpoint=endpoint,
                            observation="defines request body",
                            source_file=source_file,
                            source_location=f"{source_base}.requestBody",
                            raw_snippet=yaml.safe_dump(request_body, sort_keys=False),
                        )
                    )

                    content_obj = request_body.get("content", {})
                    if isinstance(content_obj, dict):
                        for mime, media in content_obj.items():
                            if not isinstance(media, dict):
                                continue
                            schema = media.get("schema")
                            if isinstance(schema, dict) and "$ref" in schema:
                                emit(
                                    Evidence(
                                        type=EvidenceType.SPEC_SCHEMA_REF,
                                        endpoint=endpoint,
                                        observation=(
                                            f"request body schema references "
                                            f"{schema['$ref']}"
                                        ),
                                        source_file=source_file,
                                        source_location=(
                                            f"{source_base}.requestBody.content."
                                            f"{mime}.schema.$ref"
                                        ),
                                        raw_snippet=schema["$ref"],
                                    )
                                )

            # --- Security ---
            security = operation.get("security")
            if isinstance(security, list):
                emit(
                    Evidence(
                        type=EvidenceType.SPEC_SECURITY,
                        endpoint=endpoint,
                        observation="defines security requirements",
                        source_file=source_file,
                        source_location=f"{source_base}.security",
                        raw_snippet=yaml.safe_dump(security, sort_keys=False),
                    )
                )

    return evidence_list