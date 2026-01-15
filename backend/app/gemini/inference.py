from .client import get_client
from google.genai import types

#--------------Text Generation Function--------------
def generate_text(
        prompt: str, 
        system_instruction: str = "", 
        model: str = "gemini-2.5-flash",
        temperature: float = 0.0,
        top_p: float = 0.95
)-> str | None:
    try:
        client = get_client()
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=temperature,
                top_p=top_p
            )
        )
    except Exception as e:
        raise RuntimeError(f"Gemini generation failed: {e}")
    
    if not response or not response.text:
        raise RuntimeError("Gemini generation returned no text.")

    return response.text
#-----------------------------------------------------