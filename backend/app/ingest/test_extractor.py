from evidence.evidence_model import Evidence, EvidenceType
from typing import List, Optional
import os
import re


class TestContext:
    def __init__(self, name: str, start_line: int):
        self.name = name
        self.start_line = start_line
        self.current_endpoint: Optional[str] = None
        self.last_request_line: Optional[int] = None


# ---------- Helpers ----------
# NOTE: This extractor intentionally targets Python tests using the `requests` library.

REQUEST_PATTERN = re.compile(
    r'(?:requests|client)\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']',
    re.IGNORECASE,
)

ASSERT_PATTERNS = [
    re.compile(r'assert\s+.*status_code\s*==\s*(\d+)'),
    re.compile(r'response\.status_code\s*==\s*(\d+)'),
    re.compile(r'assertEqual\([^,]*status_code[^,]*,\s*(\d+)\)'),
    re.compile(r'assertEquals\([^,]*status_code[^,]*,\s*(\d+)\)'),
    re.compile(r'expect.*status.*toBe\((\d+)\)'),
]

TEST_DEF_PATTERN = re.compile(r'def\s+(test_[a-zA-Z0-9_]+)\s*\(')

MAX_ASSERT_DISTANCE = 5  # lines


def normalize_path(path: str) -> str:
    """
    Normalize concrete paths to a conservative parameterized form.
    No semantic inference is performed.
    """
    # Strip f-string variable references like {self.base_url}, {base_url}, etc.
    path = re.sub(r'\{[^}]*base_url[^}]*\}', '', path)
    
    # Strip scheme + host
    path = re.sub(r'^https?://[^/]+', '', path)

    # Strip query string
    path = path.split('?', 1)[0]

    # Replace UUIDs
    path = re.sub(
        r'/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-'
        r'[0-9a-fA-F]{4}-[0-9a-fA-F]{12}',
        '/{id}',
        path,
    )

    # Replace numeric segments
    path = re.sub(r'/\d+', '/{id}', path)

    # Ensure path starts with /
    if not path.startswith('/'):
        path = '/' + path
        
    # Clean up any double slashes
    path = re.sub(r'/+', '/', path)

    return path


# ---------- Main Extraction ----------

def extract_test_evidence(file_path: str, content: str) -> List[Evidence]:
    evidence_list: List[Evidence] = []
    seen_evidence = set()

    lines = content.splitlines()
    current_test: Optional[TestContext] = None

    for line_num, raw_line in enumerate(lines, 1):
        line = raw_line.strip()

        # ---- Detect new test function ----
        test_match = TEST_DEF_PATTERN.match(line)
        if test_match:
            test_name = test_match.group(1)
            current_test = TestContext(test_name, line_num)
            continue

        if current_test is None:
            continue

        # ---- Detect request call ----
        request_match = REQUEST_PATTERN.search(line)
        if request_match:
            method, url_expr = request_match.groups()
            path = normalize_path(url_expr)

            current_test.current_endpoint = f"{method.upper()} {path}"
            current_test.last_request_line = line_num
            continue

        # ---- Detect assertions ----
        if current_test.current_endpoint is None:
            continue

        # Enforce proximity to request
        if (
            current_test.last_request_line is None
            or line_num - current_test.last_request_line > MAX_ASSERT_DISTANCE
        ):
            continue

        for pattern in ASSERT_PATTERNS:
            match = pattern.search(line)
            if not match:
                continue

            status_code = match.group(1)

            evidence_key = (
                current_test.current_endpoint,
                status_code,
                current_test.name,
                line_num,
            )
            if evidence_key in seen_evidence:
                break

            seen_evidence.add(evidence_key)

            evidence_list.append(
                Evidence(
                    type=EvidenceType.TEST_ASSERTION,
                    endpoint=current_test.current_endpoint,
                    observation=f"observed HTTP {status_code} in test",
                    source_file=os.path.basename(file_path),
                    source_location=(
                        f"{current_test.name} [line {line_num}]"
                    ),
                    raw_snippet=raw_line.strip(),
                )
            )

            # Reset endpoint after first assertion to prevent leakage
            current_test.current_endpoint = None
            current_test.last_request_line = None
            break

    return evidence_list