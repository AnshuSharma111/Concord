from evidence.evidence_model import Evidence, EvidenceType
from gemini import generate_structured
from typing import List, Tuple
import os
import re


def extract_readme_evidence(file_path: str, content: str) -> List[Evidence]:
    """
    Extract evidence from README files using conservative heuristics
    and LLM-assisted literal claim extraction.
    """
    print(f"Extracting README evidence from {file_path}")

    evidence_list: List[Evidence] = []
    lines = content.split('\n')

    api_sections = _find_api_sections(lines)

    for start_line, end_line, section_content in api_sections:
        prompt = f"""
Analyze the following README section and extract API behavior claims.

Section content:
{section_content}

Rules:
- Only extract literal, testable statements about observable API behavior.
- Do NOT summarize, infer, combine, or generalize.
- Each claim must correspond to a contiguous snippet of text.
- The raw_snippet MUST be copied verbatim from the section content.
- If the section does not explicitly mention an endpoint, return an empty array.

Focus on:
- HTTP status codes and error conditions
- Input validation and preconditions
- Output formats and guarantees
- Explicit endpoint behavior descriptions

Return a JSON array of objects with:
- endpoint: canonical endpoint (e.g., "GET /users/{{id}}")
- observation: specific behavior (e.g., "returns HTTP 404 when user not found")
- raw_snippet: exact verbatim text from the document

Return ONLY the raw JSON array. No markdown (e.g. ```JSON). No commentary.
"""

        system_instruction = (
            "You extract literal API behavioral claims from documentation. "
            "Only emit claims that are explicitly stated. "
            "Never infer missing details. "
            "Use canonical endpoint formats with path parameters in curly braces."
        )

        try:
            print(f"Invoking Gemini for README section lines {start_line}-{end_line}")
            result = generate_structured(prompt, system_instruction)
        except Exception as e:
            print(f"Gemini invocation failed: {e}. Using fallback extractor.")
            evidence_list.extend(
                _extract_readme_fallback(file_path, section_content, start_line)
            )
            continue

        if not isinstance(result, list):
            continue

        for item in result:
            if not all(k in item for k in ("endpoint", "observation", "raw_snippet")):
                continue

            raw_snippet = item["raw_snippet"]

            # Hard provenance check: snippet must be verbatim
            if raw_snippet not in section_content:
                continue

            evidence_list.append(
                Evidence(
                    type=EvidenceType.README_STATEMENT,
                    endpoint=item["endpoint"],
                    observation=item["observation"],
                    source_file=os.path.basename(file_path),
                    source_location=f"lines {start_line}-{end_line}",
                    raw_snippet=raw_snippet,
                )
            )

    return evidence_list


def _find_api_sections(lines: List[str]) -> List[Tuple[int, int, str]]:
    """
    Identify README sections likely to contain API behavior descriptions.
    Conservative by design: prefers precision over recall.
    """
    sections = []
    section_lines: List[str] = []
    section_start = 1
    in_api_section = False
    section_root_level = 0

    API_KEYWORDS = {
        "api", "endpoint", "route", "request", "response", "http", "rest",
        "status", "error", "get", "post", "put", "delete", "patch"
    }

    API_ROOT_HEADERS = {
        "api", "endpoints", "routes", "rest api", "http api"
    }

    # Also match headers that contain API keywords
    def is_api_header(header_text: str) -> bool:
        """Check if header indicates an API section."""
        # Exact matches
        if header_text in API_ROOT_HEADERS:
            return True
        # Contains 'api' keyword
        if "api" in header_text:
            return True
        # Contains multiple API keywords
        api_count = sum(1 for kw in API_KEYWORDS if kw in header_text)
        return api_count >= 2

    SIGNAL_THRESHOLD = 2

    def classify_header(line: str) -> Tuple[int, bool]:
        stripped = line.lstrip()
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            return level, False
        if line.strip().endswith(":"):
            return 10_000, True
        return 0, False

    def get_api_signal(line: str) -> int:
        line_lower = line.lower()
        return sum(1 for kw in API_KEYWORDS if kw in line_lower)

    def is_killer_header(level: int, root_level: int, signal: int) -> bool:
        return level > 0 and level <= root_level and signal < SIGNAL_THRESHOLD

    for i, line in enumerate(lines, 1):
        level, is_pseudo = classify_header(line)
        api_signal = get_api_signal(line)
        header_text = line.lower().strip("# ").strip(":")

        # Exit logic
        if in_api_section:
            if is_killer_header(level, section_root_level, api_signal):
                sections.append(
                    (section_start, i - 1, "\n".join(section_lines))
                )
                section_lines = []
                in_api_section = False
                section_root_level = 0

        # Start logic
        if not in_api_section:
            if (
                level > 0
                and (
                    is_api_header(header_text)
                    or api_signal >= SIGNAL_THRESHOLD
                )
            ):
                in_api_section = True
                section_start = i
                section_root_level = level
                if is_pseudo:
                    section_root_level = 999

        # Buffering
        if in_api_section:
            section_lines.append(line)

    if in_api_section and section_lines:
        sections.append(
            (section_start, len(lines), "\n".join(section_lines))
        )

    print(f"Identified {len(sections)} API-like README sections")
    return sections


def _extract_readme_fallback(
    file_path: str, content: str, start_line: int
) -> List[Evidence]:
    """
    Conservative fallback extractor.
    Only emits evidence for explicitly stated behavior.
    """
    evidence_list: List[Evidence] = []
    lines = content.split("\n")

    patterns = [
        (r"returns?\s+(?:HTTP\s+)?(\d+)", lambda m: f"returns HTTP {m.group(1)}"),
        (r"responds?\s+with\s+(?:HTTP\s+)?(\d+)", lambda m: f"returns HTTP {m.group(1)}"),
        (r"status\s+code\s+(\d+)", lambda m: f"returns HTTP {m.group(1)}"),
    ]

    for i, line in enumerate(lines):
        for pattern, formatter in patterns:
            for match in re.finditer(pattern, line, re.IGNORECASE):
                endpoint = _extract_endpoint_from_context(lines, i)
                if not endpoint:
                    continue

                evidence_list.append(
                    Evidence(
                        type=EvidenceType.README_STATEMENT,
                        endpoint=endpoint,
                        observation=formatter(match),
                        source_file=os.path.basename(file_path),
                        source_location=f"line {start_line + i}",
                        raw_snippet=line.strip(),
                    )
                )

    return evidence_list


def _extract_endpoint_from_context(
    lines: List[str], current_line: int
) -> str | None:
    """
    Attempt to extract an explicitly stated endpoint from nearby context.
    Does NOT infer HTTP methods.
    """
    search_range = range(
        max(0, current_line - 5),
        min(len(lines), current_line + 6),
    )

    endpoint_patterns = [
        r"`([A-Z]+)\s+([/\w{}.-]+)`",
        r"([A-Z]+)\s+([/\w{}.-]+)",
    ]

    for i in search_range:
        for pattern in endpoint_patterns:
            match = re.search(pattern, lines[i])
            if match and len(match.groups()) == 2:
                method, path = match.groups()
                return f"{method.upper()} {path}"

    return None