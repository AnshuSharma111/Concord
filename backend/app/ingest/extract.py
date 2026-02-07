from claims.claim_model import ArtifactSource
from evidence.evidence_model import Evidence, EvidenceType
from ingest.readme_extractor import extract_readme_evidence
from ingest.spec_extractor import extract_spec_evidence
from ingest.test_extractor import extract_test_evidence
from typing import List
import os

#----------------Function to extract evidence from files-----------------------
def extract_evidence_from_file(file_path: str, file_type: ArtifactSource) -> List[Evidence]:
    """
    Extract evidence from files based on their type (README, API_SPEC, TEST).
    
    Args:
        file_path: Absolute path to the file to process
        file_type: Type of artifact (README, API_SPEC, TEST)
        
    Returns:
        List of Evidence objects extracted from the file
    """
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
        return extract_readme_evidence(file_path, content)
    elif file_type == ArtifactSource.API_SPEC:
        return extract_spec_evidence(file_path, content)
    elif file_type == ArtifactSource.TEST:
        return extract_test_evidence(file_path, content)
    else:
        return []
#----------------Function to extract evidence from files-----------------------