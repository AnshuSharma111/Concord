from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

#--------------Enum for Evidence Types--------------#
class EvidenceType(str, Enum):
    TEST_ASSERTION = "test_assertion"
    SPEC_RESPONSE = "spec_response"
    SPEC_PARAMETER = "spec_parameter"
    README_STATEMENT = "readme_statement"
    SPEC_SCHEMA_REF = "spec_schema_ref"
    SPEC_REQUEST_BODY = "spec_request_body"
    SPEC_SECURITY = "spec_security"
#--------------Enum for Evidence Types--------------#

#------------------Evidence Model-------------------#
class Evidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    # class members
    type: EvidenceType
    endpoint: str
    observation: str
    """
    Literal observed behavior, e.g.
    'returns HTTP 404'
    """
    source_file: str
    source_location: str
    """
    e.g. 'lines 42-44' or JSON pointer
    """
    raw_snippet: Optional[str]
#------------------Evidence Model-------------------#