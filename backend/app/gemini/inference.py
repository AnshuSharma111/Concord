from .client import get_client
from google.genai import types
import json

#--------------Text Generation Function----------------------
def generate_structured(
    prompt: str,
    system_instruction: str,
    model: str = "gemini-2.5-flash"
) -> dict:
    client = get_client()
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.0
        )
    )

    if not response or not response.text:
        raise RuntimeError("Empty Gemini response")

    # Debug Statement
    print(f"Gemini response received: {response.text}")

    response_text = response.text
    # Cleanse the output for a valid JSON
    if response_text.startswith("```json") or response_text.startswith("```JSON"):
        response_text = response_text.replace("```json", "").replace("```", "").strip()
    
    if response_text.startswith("```"):
        response_text = response_text.replace("```", "").strip()
    
    if response_text.endswith("```"):
        response_text = response_text[:-3].strip()
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        raise RuntimeError("Gemini returned non-JSON output")
#------------------------------------------------------------