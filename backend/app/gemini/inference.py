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


#--------------Semantic Description Generation Function----------------------
def generate_semantic_description(
    behavioral_unit_data: dict,
    model: str = "gemini-2.5-flash"
) -> str:
    """
    Generate human-readable semantic descriptions of behavioral contradictions.
    
    Args:
        behavioral_unit_data: Dictionary containing endpoint, assertions, sources, and conflicts
        
    Returns:
        Human-readable description of the contradictions and findings
    """
    prompt = f"""
Analyze the following API behavioral analysis data and generate a clear, intuitive description of the findings.

Data:
{json.dumps(behavioral_unit_data, indent=2)}

Generate a natural language summary that explains:
1. What endpoint this is about
2. What each source (README, API spec, tests) claims should happen
3. Where the contradictions are and why they matter
4. The risk implications

Use this format:
- Start with "For endpoint [ENDPOINT]:"
- Use phrases like "the README states that...", "the API specification expects...", "the test files verify..."
- Clearly highlight contradictions with "However" or "In contrast"
- End with a risk assessment

Make it conversational and easy to understand for developers who need to resolve these issues.

Return only the description text, no JSON or formatting.
"""

    system_instruction = (
        "You are an expert API documentation analyst. Generate clear, human-readable "
        "explanations of API behavioral contradictions that help developers understand "
        "and resolve inconsistencies between documentation, specifications, and tests. "
        "Be specific about what each source says and why the contradictions matter."
    )

    client = get_client()
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.3  # Slightly more creative for natural language
        )
    )

    if not response or not response.text:
        return "Unable to generate semantic description"

    return response.text.strip()
#------------------------------------------------------------