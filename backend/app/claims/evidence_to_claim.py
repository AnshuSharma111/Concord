import re
from typing import List, Optional, Tuple, Dict, Union
from pydantic import BaseModel, Field
from claims.claim_model import ArtifactSource, Claim, ClaimCategory
from evidence.evidence_model import Evidence, EvidenceType

# --- Updated Models for Transparency ---

class ClaimRejection(BaseModel):
    evidence_id: str
    phase: str
    reason: str
    raw_data: str

class ClaimSkeleton(BaseModel):
    category: ClaimCategory
    endpoint: str
    source: ArtifactSource
    raw_observation: str
# --- The Pipeline Engine ---

class DeterministicClaimGenerator:
    def __init__(self):
        # Phase 1: Branching Policy
        self.POLICY = {
            EvidenceType.SPEC_RESPONSE: [ClaimCategory.OUTPUT_GUARANTEE, ClaimCategory.ERROR_SEMANTICS],
            EvidenceType.SPEC_SECURITY: [ClaimCategory.INPUT_PRECONDITION],
            EvidenceType.TEST_ASSERTION: [ClaimCategory.OUTPUT_GUARANTEE, ClaimCategory.ERROR_SEMANTICS],
            EvidenceType.SPEC_PARAMETER: [ClaimCategory.INPUT_PRECONDITION],
            EvidenceType.README_STATEMENT: [ClaimCategory.OUTPUT_GUARANTEE, ClaimCategory.ERROR_SEMANTICS, ClaimCategory.INPUT_PRECONDITION],
            EvidenceType.SPEC_SCHEMA_REF: [ClaimCategory.OUTPUT_GUARANTEE],
            EvidenceType.SPEC_REQUEST_BODY: [ClaimCategory.INPUT_PRECONDITION]
        }

        # Phase 2: Category-Scoped Assertions (The Namespace Rule)
        self.ASSERTION_TEMPLATES = {
            ClaimCategory.OUTPUT_GUARANTEE: [
                (r"(?i)returns (?:HTTP )?(\d{3})", lambda m: f"OUT_HTTP_{m.group(1)}"),
                (r"(?i)observed HTTP (\d{3}) in test", lambda m: f"OUT_HTTP_{m.group(1)}"),
                (r"(?i)documents possible response (\d{3})", lambda m: f"OUT_HTTP_{m.group(1)}"),
                (r"(?i)defines response (\d{3})", lambda m: f"OUT_HTTP_{m.group(1)}"),
                (r"(?i)json body", lambda _: "OUT_RETURNS_JSON"),
                (r"(?i)schema references (#/.*)", lambda m: f"OUT_SCHEMA_{m.group(1).replace('/', '_').replace('#', 'COMPONENTS')}"),
                (r"(?i)request body", lambda _: "OUT_REQ_BODY_DEFINED"),
                (r"(?i)user data", lambda _: "OUT_USER_DATA"),
            ],
            ClaimCategory.ERROR_SEMANTICS: [
                (r"(?i)observed HTTP (\d{3}) in test", lambda m: f"ERR_HTTP_{m.group(1)}"),
                (r"(?i)documents possible response (\d{3})", lambda m: f"ERR_HTTP_{m.group(1)}"),
                (r"(?i)defines response (\d{3})", lambda m: f"ERR_HTTP_{m.group(1)}"),
                (r"(?i)returns (?:HTTP )?(\d{3})", lambda m: f"ERR_HTTP_{m.group(1)}"),
                (r"(?i)(\d{3})", lambda m: f"ERR_HTTP_{m.group(1)}"),
                (r"(?i)not found", lambda _: "ERR_TYPE_NOT_FOUND"),
                (r"(?i)unauthorized", lambda _: "ERR_TYPE_UNAUTHORIZED"),
                (r"(?i)invalid", lambda _: "ERR_TYPE_INVALID_INPUT"),
                (r"(?i)lacks permission", lambda _: "ERR_TYPE_FORBIDDEN"),
                (r"(?i)already exists", lambda _: "ERR_TYPE_CONFLICT"),
            ],
            ClaimCategory.INPUT_PRECONDITION: [
                (r"(?i)requires auth", lambda _: "PRE_AUTH_REQUIRED"),
                (r"(?i)parameter ([\w_]+)", lambda m: f"PRE_REQ_PARAM_{m.group(1).upper()}"),
                (r"(?i)defines parameter '([^']+)' in (\w+)", lambda m: f"PRE_REQ_PARAM_{m.group(1).upper()}"),
                (r"(?i)request body", lambda _: "PRE_REQ_BODY"),
                (r"(?i)defines request body", lambda _: "PRE_REQ_BODY"),
                (r"(?i)authentication", lambda _: "PRE_AUTH_REQUIRED"),
            ]
        }

        # Phase 3: Condition Normalization Map
        self.CONDITION_NORMALIZER = {
            "is missing": "NOT_EXISTS",
            "does not exist": "NOT_EXISTS",
            "exists": "EXISTS",
            "is valid": "VALID",
            "is authenticated": "AUTH_TRUE"
        }

    def _determine_source(self, ev: Evidence) -> ArtifactSource:
        """Map evidence type to correct artifact source."""
        if ev.type in [EvidenceType.README_STATEMENT]:
            return ArtifactSource.README
        elif ev.type in [EvidenceType.SPEC_RESPONSE, EvidenceType.SPEC_PARAMETER, 
                         EvidenceType.SPEC_SECURITY, EvidenceType.SPEC_SCHEMA_REF,
                         EvidenceType.SPEC_REQUEST_BODY]:
            return ArtifactSource.API_SPEC
        elif ev.type in [EvidenceType.TEST_ASSERTION]:
            return ArtifactSource.TEST
        else:
            # Fallback based on source_file extension
            if ev.source_file.endswith(('.md', '.txt')):
                return ArtifactSource.README
            elif ev.source_file.endswith(('.yaml', '.yml', '.json')):
                return ArtifactSource.API_SPEC
            else:
                return ArtifactSource.TEST

    # --- Phase 0: Admission Control (Identity Guard) ---
    def _admit(self, ev: Evidence) -> Tuple[bool, Optional[str], Optional[ClaimRejection]]:
        # Handle None or empty endpoints
        if not ev.endpoint or not ev.endpoint.strip():
            return False, None, ClaimRejection(
                evidence_id=ev.source_location, phase="P0_ADMISSION", 
                reason="EMPTY_ENDPOINT", raw_data=str(ev.endpoint)
            )
        
        # Clean and normalize endpoint
        endpoint = ev.endpoint.strip()
        
        # More flexible endpoint pattern that handles multiple separators
        pattern = r"^(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+\/.*"
        if not re.match(pattern, endpoint, re.IGNORECASE):
            return False, None, ClaimRejection(
                evidence_id=ev.source_location, phase="P0_ADMISSION", 
                reason="MALFORMED_ENDPOINT_IDENTITY", raw_data=endpoint
            )
        
        # Consistent Path Normalization ({userId} -> {id})
        normalized_path = re.sub(r"\{[^}]*\}", "{id}", endpoint.upper())
        return True, normalized_path, None

    # --- Phase 2: Assertion (Closed World + Namespace) ---
    def _canonicalize_assertion(self, skel: ClaimSkeleton) -> Tuple[Optional[str], Optional[ClaimRejection]]:
        templates = self.ASSERTION_TEMPLATES.get(skel.category, [])
        for pattern, transform in templates:
            match = re.search(pattern, skel.raw_observation)
            if match:
                return transform(match), None
        
        return None, ClaimRejection(
            evidence_id=f"Skel_{skel.category}", phase="P2_ASSERTION", 
            reason="UNMAPPABLE_OBSERVATION", raw_data=skel.raw_observation
        )

    # --- Phase 3: Condition Extraction (Safe & Normalized) ---
    def _extract_condition(self, raw_text: str) -> Optional[str]:
        # Pattern: (Subject) (Predicate)
        pattern = r"(?i)(?:if|when) ([\w\s]+) (is missing|does not exist|exists|is valid|is authenticated)"
        match = re.search(pattern, raw_text)
        if match:
            subject = match.group(1).strip().replace(" ", "_").upper()
            raw_predicate = match.group(2).lower()
            normalized_predicate = self.CONDITION_NORMALIZER.get(raw_predicate, "UNKNOWN")
            return f"{subject}_{normalized_predicate}"
        return None

    def process(self, evidence_list: List[Evidence]) -> Tuple[List[Claim], List[ClaimRejection]]:
        emitted_claims = []
        rejections = []

        for ev in evidence_list:
            # Phase 0
            is_admitted, canonical_endpoint, rejection = self._admit(ev)
            if not is_admitted:
                rejections.append(rejection)
                continue

            # Phase 1: Skeleton Branching
            categories = self.POLICY.get(ev.type, [])
            source = self._determine_source(ev)

            for cat in categories:
                if canonical_endpoint is not None:
                    skel = ClaimSkeleton(
                        category=cat, endpoint=canonical_endpoint,
                        source=source, raw_observation=ev.observation
                    )

                    # Phase 2: Assertion
                    assertion, rejection = self._canonicalize_assertion(skel)
                    if not assertion:
                        rejections.append(rejection)
                        continue

                    # Phase 3: Condition
                    condition = self._extract_condition(skel.raw_observation)

                    # Phase 4: Materialization
                    emitted_claims.append(Claim(
                        category=skel.category,
                        endpoint=skel.endpoint,
                        condition=condition,
                        assertion=assertion,
                        source=skel.source,
                        confidence=0.9 if source != ArtifactSource.README else 0.7
                    ))

        return emitted_claims, rejections