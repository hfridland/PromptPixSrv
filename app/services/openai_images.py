import base64
from io import BytesIO

from openai import OpenAI
from app.config import settings


def edit_image(image: bytes, command: str, model: str = "gpt-image-1.5") -> bytes:
    source = BytesIO(image)
    source.name = "source.png" if image.startswith(b"\x89PNG") else (
        "source.webp" if image.startswith(b"RIFF") else "source.jpg"
    )
    result = OpenAI(api_key=settings.openai_api_key).images.edit(
        model=model,
        image=source,
        prompt=command,
    )
    if not result.data or not result.data[0].b64_json:
        raise ValueError("OpenAI did not return image data")
    return base64.b64decode(result.data[0].b64_json, validate=True)
