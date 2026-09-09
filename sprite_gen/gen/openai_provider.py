# SPDX-License-Identifier: Apache-2.0
"""OpenAI Images API adapter; one paid request, with no automatic retries."""

from __future__ import annotations

import base64
import binascii
import hashlib
import io
import json
import mimetypes
import os
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from PIL import Image

from .base import GEN_TIMEOUT_SECONDS, TRANSPARENCY_NATIVE, GenRequest, ProviderRun

DEFAULT_MODEL = "gpt-image-2.5-sunburst"
API_ROOT = "https://api.openai.com/v1/images"


def _multipart(fields: dict, refs: list[Path]) -> tuple[bytes, str, list[dict]]:
    boundary = "sprite-gen-" + uuid.uuid4().hex
    chunks = []
    evidence = []
    for key, value in fields.items():
        chunks.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode()
        )
    for index, ref in enumerate(refs):
        data = ref.read_bytes()
        mime = mimetypes.guess_type(ref.name)[0] or "application/octet-stream"
        chunks.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="image[]"; filename="reference-{index}{ref.suffix}"\r\nContent-Type: {mime}\r\n\r\n'.encode()
        )
        chunks.extend([data, b"\r\n"])
        evidence.append({"path": str(ref), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}", evidence


class OpenAIProvider:
    name = "openai"
    transparency = TRANSPARENCY_NATIVE

    def generate(self, request: GenRequest, workdir: Path) -> ProviderRun:
        key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not key:
            raise SystemExit("openai-gen: OPENAI_API_KEY is required")
        if request.aspect_ratio:
            raise SystemExit("openai-gen: --aspect-ratio is unsupported; describe the layout in the prompt (size=auto)")
        model = request.model or DEFAULT_MODEL
        fields = {
            "model": model, "prompt": request.prompt, "n": 1,
            "quality": "high", "size": "auto", "output_format": "png",
        }
        if request.native_alpha:
            fields["background"] = "transparent"
        if request.refs:
            body, content_type, refs = _multipart(fields, request.refs)
            endpoint = "edits"
        else:
            body = json.dumps(fields).encode()
            content_type, refs, endpoint = "application/json", [], "generations"
        transport = Request(
            f"{API_ROOT}/{endpoint}", data=body, method="POST",
            headers={"Authorization": f"Bearer {key}", "Content-Type": content_type},
        )
        started = time.monotonic()
        try:
            with urlopen(transport, timeout=GEN_TIMEOUT_SECONDS) as response:
                request_id = response.headers.get("x-request-id")
                payload = json.loads(response.read())
        except HTTPError as exc:
            # Do not print server bodies/exception strings: they can reflect secrets.
            request_id = exc.headers.get("x-request-id") if exc.headers else None
            raise SystemExit(f"openai-gen: HTTP {exc.code}; request_id={request_id}; no automatic retry") from None
        except (TimeoutError, URLError, OSError):
            # GenTimeoutError would cause the caller to send a second paid request.
            raise SystemExit("openai-gen: transport failed; completion/billing may be unknown; no automatic retry") from None
        except (ValueError, UnicodeError):
            raise SystemExit("openai-gen: invalid API response; no automatic retry") from None
        try:
            data = base64.b64decode(payload["data"][0]["b64_json"], validate=True)
            with Image.open(io.BytesIO(data)) as image:
                if image.format != "PNG":
                    raise ValueError("not PNG")
                image.verify()
        except (KeyError, IndexError, TypeError, ValueError, OSError, binascii.Error):
            raise SystemExit("openai-gen: response contains no valid PNG; no automatic retry") from None
        request.raw.parent.mkdir(parents=True, exist_ok=True)
        request.raw.write_bytes(data)
        actual_model = payload.get("model") or model
        return ProviderRun(
            provider=self.name, elapsed_seconds=time.monotonic() - started,
            model=actual_model,
            extra={
                "endpoint": f"/v1/images/{endpoint}", "requested_model": model,
                "model": actual_model,
                "model_source": "response" if payload.get("model") else "request",
                "usage": payload.get("usage"), "request_id": request_id,
                "references": refs, "quality": "high", "size": "auto",
            },
        )
