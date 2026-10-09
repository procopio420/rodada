"""Configurable real HTTP image-provider gateway. No fake runtime fallback."""
import base64
import io
import json
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from django.conf import settings
from PIL import Image


@dataclass(frozen=True)
class GeneratedAsset:
    content: bytes
    provider: str
    model: str
    usage: dict


class CatalogIconGenerator(Protocol):
    def generate(self, *, context, prompt, style_version, idempotency_key) -> GeneratedAsset: ...


def validate_image(content, mime=None):
    if len(content) > 5 * 1024 * 1024:
        raise ValueError("IMAGE_TOO_LARGE")
    try:
        with Image.open(io.BytesIO(content)) as image:
            if image.format not in ("PNG", "WEBP", "JPEG"):
                raise ValueError("INVALID_IMAGE_FORMAT")
            actual = Image.MIME[image.format]
            if mime and actual != mime:
                raise ValueError("INVALID_IMAGE_MIME")
            width, height = image.size
            if width != height or not 128 <= width <= 2048:
                raise ValueError("INVALID_IMAGE_DIMENSIONS")
            image.load()
            output = io.BytesIO()
            image.convert("RGBA").save(output, format="PNG")
            return output.getvalue()
    except (OSError, Image.DecompressionBombError) as exc:
        raise ValueError("INVALID_IMAGE") from exc


class HttpIconGenerator:
    def generate(self, *, context, prompt, style_version, idempotency_key):
        endpoint = settings.RODADA_ICON_PROVIDER_URL
        if not endpoint.startswith("https://") or not settings.RODADA_ICON_PROVIDER_KEY:
            raise RuntimeError("ICON_PROVIDER_NOT_CONFIGURED")
        payload = {"product_context": context, "prompt": prompt, "style_version": style_version,
                   "model": settings.RODADA_ICON_PROVIDER_MODEL, "size": "1024x1024", "background": "transparent"}
        request = urllib.request.Request(endpoint, data=json.dumps(payload).encode(), headers={
            "Content-Type": "application/json", "Authorization": "Bearer " + settings.RODADA_ICON_PROVIDER_KEY,
            "Idempotency-Key": str(idempotency_key)}, method="POST")
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read(8 * 1024 * 1024 + 1)
        if len(raw) > 8 * 1024 * 1024:
            raise ValueError("PROVIDER_RESPONSE_TOO_LARGE")
        result = json.loads(raw)
        content = validate_image(base64.b64decode(result["image_base64"], validate=True))
        return GeneratedAsset(content, str(result["provider"])[:100], str(result["model"])[:100], result.get("usage", {}))
