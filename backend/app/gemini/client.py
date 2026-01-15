from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

# ------------- EVIRONMENT VARIABLES -------------
_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not _GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in environment variables.")
# -----------------------------------------------

#--------------Client Initialization--------------
_client: genai.Client | None = None

def get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=_GEMINI_API_KEY)
    return _client
#-------------------------------------------------