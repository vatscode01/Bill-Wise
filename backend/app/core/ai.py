from openai import OpenAI
from app.core.config import settings
from app.schemas.extraction import ExtractedBillData

def get_openai_client() -> OpenAI:
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set in environment variables")
    return OpenAI(api_key=settings.openai_api_key)

def extract_bill_data_from_text(text: str) -> ExtractedBillData:
    client = get_openai_client()
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that extracts bill and invoice information from text. "
                           "If a field is not found or ambiguous, leave it as null. "
                           "For billing_period, try to extract a string like 'July 2026' or 'Q3 2026'."
            },
            {
                "role": "user", 
                "content": f"Extract the bill details from the following text:\n\n{text}"
            }
        ],
        response_format=ExtractedBillData,
    )
    return response.choices[0].message.parsed

def extract_bill_data_from_image(base64_image: str, mime_type: str = "image/jpeg") -> ExtractedBillData:
    client = get_openai_client()
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that extracts bill and invoice information from images. "
                           "If a field is not found or ambiguous, leave it as null. "
                           "For billing_period, try to extract a string like 'July 2026' or 'Q3 2026'."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract the bill details from this image:"},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
                ]
            }
        ],
        response_format=ExtractedBillData,
    )
    return response.choices[0].message.parsed
