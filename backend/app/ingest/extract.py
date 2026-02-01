from backend.app.claims.claim_model import ArtifactSource
from backend.app.evidence.evidence_model import Evidence, EvidenceType
from backend.app.gemini import generate_structured
from typing import List
import os
import re
import json
import yaml

#----------------Function to extract evidence from files-----------------------
def extract_evidence_from_file(file_path: str, file_type: ArtifactSource) -> List[Evidence]:
    # File does not exist
    if not os.path.exists(file_path):
        return []
    
    # unable to read file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except (IOError, UnicodeDecodeError):
        return []
    
    # no content
    if not content.strip():
        return []
    
    # Dispatch to specific extraction logic based on file type
    if file_type == ArtifactSource.README:
        return _extract_readme_evidence(file_path, content)
    elif file_type == ArtifactSource.API_SPEC:
        return _extract_spec_evidence(file_path, content)
    elif file_type == ArtifactSource.TEST:
        return _extract_test_evidence(file_path, content)
    else:
        return []
#----------------Function to extract evidence from files-----------------------

#----------------Function to extract evidence from README files-----------------------
def _extract_readme_evidence(file_path: str, content: str) -> List[Evidence]:
    # debug statement
    print(f"Extracting README evidence from {file_path}")

    evidence_list = []
    lines = content.split('\n')
    
    # Find sections that might contain API behavior descriptions
    api_sections = _find_api_sections(lines)
    
    for section in api_sections:
        start_line, end_line, section_content = section
        
        # Use Gemini to extract structured claims from the section
        prompt = f"""
        Analyze this README section and extract API behavior claims:
        
        Section content:
        {section_content}
        
        Extract literal statements that explicitly describe observable API behavior.
        Do not summarize, infer, or combine statements.
        Each extracted observation must correspond directly to a contiguous snippet of text.

        Focus on:
        - HTTP status codes and error conditions
        - Input validation and preconditions
        - Output formats and guarantees
        - Endpoint existence claims
        
        Return a JSON array of objects with:
        - endpoint: canonical endpoint (e.g., "GET /users/{{id}}")
        - observation: specific behavior (e.g., "returns HTTP 404 when user not found")
        - raw_snippet: exact text from the document

        DO NOT WRAP THE OUTPUT IN ADDITIONAL TEXT OR MARKDOWN (Ex : No ````json` OR SIMILAR). JUST RETURN THE RAW JSON ARRAY.
        """
        
        system_instruction = """You are an expert at extracting API behavioral claims from documentation. 
        Only extract concrete, testable statements about observable behavior. 
        Ignore implementation details, setup instructions, or vague descriptions.
        Use canonical endpoint formats with path parameters in curly braces."""
        
        try:
            # Debug Statement
            print(f"Invoking Gemini for README section starting at line {start_line}")

            result = generate_structured(prompt, system_instruction)
            if isinstance(result, list):
                for item in result:
                    if all(k in item for k in ['endpoint', 'observation', 'raw_snippet']):
                        evidence = Evidence(
                            type=EvidenceType.README_STATEMENT,
                            endpoint=item['endpoint'],
                            observation=item['observation'],
                            source_file=os.path.basename(file_path),
                            source_location=f"lines {start_line}-{end_line}",
                            raw_snippet=item['raw_snippet']
                        )
                        evidence_list.append(evidence)
                
                # Debug Statement
                print(f"Successfully extracted {len(result)} claims using Gemini from README section.")
        except Exception as e:
            # Debug Statement
            print(f"Error during Gemini extraction: {e}. Resorting to fallback method.")

            # Fallback to simple pattern matching if AI fails
            evidence_list.extend(_extract_readme_fallback(file_path, section_content, start_line))
    
    return evidence_list
#----------------Function to extract evidence from README files-----------------------

#-------------------Function to extract evidence from API spec files-----------------------
def _extract_spec_evidence(file_path: str, content: str) -> List[Evidence]:
    """Extract evidence from OpenAPI/Swagger specification files."""
    evidence_list = []
    
    # Debug Statement
    print(f"Extracting SPEC evidence from {file_path}")

    try:
        # Try to parse as YAML first, then JSON
        try:
            spec_data = yaml.safe_load(content)
        except yaml.YAMLError:
            spec_data = json.loads(content)
        
        if not isinstance(spec_data, dict):
            return []
            
        paths = spec_data.get('paths', {})
        
        for path, path_obj in paths.items():
            if not isinstance(path_obj, dict):
                continue
                
            for method, operation in path_obj.items():
                if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
                    continue
                    
                endpoint = f"{method.upper()} {path}"
                
                # Extract response evidence
                responses = operation.get('responses', {})
                for status_code, response_obj in responses.items():
                    if isinstance(response_obj, dict):
                        description = response_obj.get('description', '')
                        if description:
                            evidence = Evidence(
                                type=EvidenceType.SPEC_RESPONSE,
                                endpoint=endpoint,
                                observation = f"returns HTTP {status_code}",
                                source_file=os.path.basename(file_path),
                                source_location=f"paths.{path}.{method}.responses.{status_code}",
                                raw_snippet=json.dumps(response_obj, indent=2)
                            )
                            evidence_list.append(evidence)
                
                # Extract parameter evidence
                parameters = operation.get('parameters', [])
                for i, param in enumerate(parameters):
                    if isinstance(param, dict):
                        param_name = param.get('name', '')
                        required = param.get('required', False)
                        param_type = param.get('type', param.get('schema', {}).get('type', ''))
                        
                        if param_name:
                            observation = f"parameter '{param_name}' is {'required' if required else 'optional'}"
                            if param_type:
                                observation += f" of type {param_type}"
                                
                            evidence = Evidence(
                                type=EvidenceType.SPEC_PARAMETER,
                                endpoint=endpoint,
                                observation=observation,
                                source_file=os.path.basename(file_path),
                                source_location=f"paths.{path}.{method}.parameters[{i}]",
                                raw_snippet=json.dumps(param, indent=2)
                            )
                            evidence_list.append(evidence)
                            
    except (json.JSONDecodeError, yaml.YAMLError, AttributeError):
        pass
    
    return evidence_list
#-------------------Function to extract evidence from API spec files-----------------------

#-------------------Function to extract evidence from test files-----------------------
def _extract_test_evidence(file_path: str, content: str) -> List[Evidence]:
    evidence_list = []
    lines = content.split('\n')
    
    # Pattern to match HTTP status assertions and similar test patterns
    test_patterns = [
        r'assert.*status.*==\s*(\d+)',
        r'expect.*status.*toBe\((\d+)\)',
        r'should.*return.*(\d+)',
        r'response\.status_code.*==\s*(\d+)',
        r'\.status_code\s*==\s*(\d+)',
        r'assertEqual.*status.*(\d+)',
        r'assertEquals.*status.*(\d+)',
    ]
    
    endpoint_patterns = [
        r'["\']([A-Z]+)\s+([/\w{}.-]+)["\']',  # "GET /users/{id}"
        r'\.([a-z]+)\(["\']([/\w{}.-]+)["\']',  # .get("/users")
        r'request\(["\']([A-Z]+)["\'].*["\']([/\w{}.-]+)["\']',  # request("GET", "/users")
    ]
    
    current_endpoint = None
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        
        # Try to extract endpoint from current line
        for pattern in endpoint_patterns:
            match = re.search(pattern, line)
            if match:
                if len(match.groups()) == 2:
                    method, path = match.groups()
                    current_endpoint = f"{method.upper()} {path}"
                elif len(match.groups()) == 1:
                    # For patterns like .get("/path"), assume GET
                    path = match.groups()[0]
                    current_endpoint = f"GET {path}"
        
        # Look for test assertions
        for pattern in test_patterns:
            match = re.search(pattern, line)
            if match and current_endpoint:
                status_code = match.group(1)
                
                # Create evidence for the assertion
                evidence = Evidence(
                    type=EvidenceType.TEST_ASSERTION,
                    endpoint=current_endpoint,
                    observation=f"returns HTTP {status_code}",
                    source_file=os.path.basename(file_path),
                    source_location=f"line {line_num}",
                    raw_snippet=line
                )
                evidence_list.append(evidence)
    
    return evidence_list
#-------------------Function to extract evidence from test files-----------------------

#-------------------Function to find API-related sections in README files-----------------------
from typing import List, Tuple

def _find_api_sections(lines: List[str]) -> List[Tuple[int, int, str]]:
    sections = []
    section_lines = []
    section_start = 1
    in_api_section = False
    section_root_level = 0
    
    # Configuration
    API_KEYWORDS = {
        'api', 'endpoint', 'route', 'request', 'response', 'http', 'rest',
        'usage', 'examples', 'curl', 'fetch', 'ajax', 'status', 'error',
        'get', 'post', 'put', 'delete', 'patch'
    }
    SIGNAL_THRESHOLD = 1  # Adjusted to 1 for standard docs, can be 2 for strictness

    def classify_header(line: str) -> Tuple[int, bool]:
        """Returns (level, is_pseudo_header). Level 0 = not a header."""
        stripped = line.lstrip()
        if stripped.startswith('#'):
            level = len(stripped) - len(stripped.lstrip('#'))
            return level, False
        if line.strip().endswith(':'):
            # Pseudo-headers (like "Usage:") are given a very high level 
            # so they never 'outrank' and kill a real Markdown section.
            return 10_000, True
        return 0, False

    def get_api_signal(line: str) -> int:
        """Counts keyword occurrences to determine intent strength."""
        line_lower = line.lower()
        return sum(1 for kw in API_KEYWORDS if kw in line_lower)

    def is_killer_header(level: int, root_level: int, signal: int) -> bool:
        """Determines if a header should terminate the current API block."""
        return level > 0 and level <= root_level and signal < SIGNAL_THRESHOLD

    for i, line in enumerate(lines, 1):
        level, is_pseudo = classify_header(line)
        api_signal = get_api_signal(line)
        
        # --- PHASE 1: EXIT LOGIC ---
        if in_api_section:
            if is_killer_header(level, section_root_level, api_signal):
                # Save the completed section (excluding the current killer header)
                sections.append((section_start, i-1, '\n'.join(section_lines)))
                section_lines = []
                in_api_section = False
                section_root_level = 0
            else:
                # Still in the section; we'll append this line later 
                # unless a NEW section starts on this same line.
                pass

        # --- PHASE 2: START LOGIC ---
        # Note: 'not in_api_section' ensures we don't restart 
        # on every sub-header like '## GET'
        if not in_api_section:
            if level > 0 and api_signal >= SIGNAL_THRESHOLD:
                in_api_section = True
                section_start = i
                section_root_level = level
                # Pseudo-headers don't define the root level for termination 
                # unless they are the only thing there.
                if is_pseudo and level == 10_000:
                    section_root_level = 999 

        # --- PHASE 3: BUFFERING ---
        if in_api_section:
            section_lines.append(line)

    # Final cleanup
    if in_api_section and section_lines:
        sections.append((section_start, len(lines), '\n'.join(section_lines)))

    print(f"identified Sections: {sections}")
    return sections
#-------------------Function to find API-related sections in README files-----------------------

#----------------Function to extract evidence from README files (fallback)-----------------------
def _extract_readme_fallback(file_path: str, content: str, start_line: int) -> List[Evidence]:
    evidence_list = []
    lines = content.split('\n')
    
    # Simple patterns for common API documentation phrases
    patterns = [
        (r'returns?\s+(?:HTTP\s+)?(\d+)', lambda m: f"returns HTTP {m.group(1)}"),
        (r'responds?\s+with\s+(?:HTTP\s+)?(\d+)', lambda m: f"returns HTTP {m.group(1)}"),
        (r'status\s+code\s+(\d+)', lambda m: f"returns HTTP {m.group(1)}"),
        (r'([A-Z]+)\s+([/\w{}.-]+)', lambda m: f"endpoint exists")
    ]
    
    for i, line in enumerate(lines):
        for pattern, formatter in patterns:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                # Try to extract endpoint from surrounding context
                endpoint = _extract_endpoint_from_context(lines, i)
                if endpoint:
                    evidence = Evidence(
                        type=EvidenceType.README_STATEMENT,
                        endpoint=endpoint,
                        observation=formatter(match),
                        source_file=os.path.basename(file_path),
                        source_location=f"line {start_line + i}",
                        raw_snippet=line.strip()
                    )
                    evidence_list.append(evidence)
    
    return evidence_list
#-----------------Function to extract evidence from README files (fallback)-----------------------

#----------------Function to extract endpoint from context-----------------------
def _extract_endpoint_from_context(lines: List[str], current_line: int) -> str | None:
    # Look in nearby lines for endpoint patterns
    search_range = range(max(0, current_line - 5), min(len(lines), current_line + 6))
    
    endpoint_patterns = [
        r'([A-Z]+)\s+([/\w{}.-]+)',  # GET /users/{id}
        r'`([A-Z]+)\s+([/\w{}.-]+)`',  # `GET /users/{id}`
        r'/([a-zA-Z][/\w{}.-]*)',  # /users/123
    ]
    
    for i in search_range:
        line = lines[i]
        for pattern in endpoint_patterns:
            match = re.search(pattern, line)
            if match:
                if len(match.groups()) == 2:
                    method, path = match.groups()
                    return f"{method.upper()} {path}"
                elif len(match.groups()) == 1:
                    path = match.groups()[0]
                    if not path.startswith('/'):
                        path = '/' + path
                    return f"GET {path}"  # Default to GET
    
    return None
#----------------Function to extract endpoint from context-----------------------