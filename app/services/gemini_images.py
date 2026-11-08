"""Gemini image editing using the Google Gemini REST API (stdlib only)."""
import base64
import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import settings

logger = logging.getLogger(__name__)
GEMINI_IMAGE_MODELS = {"gemini-2.5-flash-image"}

def edit_image(image: bytes, command: str, model: str = "gemini-2.5-flash-image") -> bytes:
    if model not in GEMINI_IMAGE_MODELS:
        raise ValueError("Unsupported Gemini image model")
    if image.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    elif image.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
    elif image[:4] == b"RIFF" and image[8:12] == b"WEBP":
        mime = "image/webp"
    else:
        raise ValueError("Unsupported source image format")
    payload = {
        "contents": [{"role": "user", "parts": [
            {"text": command},
            {"inline_data": {"mime_type": mime, "data": base64.b64encode(image).decode("ascii")}},
        ]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    req = Request(url, data=json.dumps(payload).encode("utf-8"),
                  headers={"Content-Type": "application/json", "x-goog-api-key": settings.gemini_api_key},
                  method="POST")
    try:
        with urlopen(req, timeout=180) as response:
            result = json.load(response)
    except HTTPError as exc:
        logger.error("Gemini HTTP error %s", exc.code)
        raise RuntimeError(f"Gemini API returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError("Gemini API network error") from exc
    for candidate in result.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"], validate=True)
    raise RuntimeError("Gemini did not return an image (possibly refused the request)")
