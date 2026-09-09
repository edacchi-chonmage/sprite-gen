# SPDX-License-Identifier: Apache-2.0
"""Images API transport contracts without paid calls."""

import base64
import hashlib
import io
import json
from email.parser import BytesParser
from urllib.error import HTTPError

import pytest
from PIL import Image

from sprite_gen import gen
from sprite_gen.gen import openai_provider as adapter
from sprite_gen.gen.base import GenRequest, GenTimeoutError


def png():
    out = io.BytesIO()
    Image.new("RGBA", (2, 2), (255, 0, 0, 0)).save(out, "PNG")
    return out.getvalue()


class Response:
    headers = {"x-request-id": "req-test"}

    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self):
        return json.dumps(self.data).encode()


def install(monkeypatch, payload=None):
    monkeypatch.setenv("OPENAI_API_KEY", "secret-test-key")
    calls = []

    def send(req, timeout):
        calls.append(req)
        return Response(payload if payload is not None else {
            "data": [{"b64_json": base64.b64encode(png()).decode()}],
            "usage": {"total_tokens": 42}, "model": "served-model",
        })

    monkeypatch.setattr(adapter, "urlopen", send)
    return calls


def test_generation_transport_and_report(monkeypatch, tmp_path):
    calls = install(monkeypatch)
    result = gen.generate_image("openai", "one sprite", tmp_path / "out.png")
    assert len(calls) == 1
    assert calls[0].full_url.endswith("/generations")
    body = json.loads(calls[0].data)
    assert body == {"model": adapter.DEFAULT_MODEL, "prompt": "one sprite", "n": 1,
                    "quality": "high", "size": "auto", "output_format": "png"}
    assert result.out.read_bytes() == png()
    assert result.model == "served-model"
    assert result.extra["request_id"] == "req-test"
    assert result.extra["usage"] == {"total_tokens": 42}
    assert "secret-test-key" not in json.dumps(result.to_dict())


def test_edit_attaches_exact_reference_bytes_and_native_alpha(monkeypatch, tmp_path):
    calls = install(monkeypatch)
    refs = [tmp_path / "identity.png", tmp_path / "guide.png"]
    for ref in refs:
        ref.write_bytes(png())
    request = GenRequest("run cycle", tmp_path / "raw.png", refs=refs,
                         model="gpt-image-2.5-sunburst", native_alpha=True)
    result = adapter.OpenAIProvider().generate(request, tmp_path)
    req = calls[0]
    assert req.full_url.endswith("/edits")
    message = BytesParser().parsebytes(
        f"Content-Type: {req.get_header('Content-type')}\r\nMIME-Version: 1.0\r\n\r\n".encode() + req.data
    )
    parts = message.get_payload()
    images = [p for p in parts if p.get_param("name", header="content-disposition") == "image[]"]
    assert [p.get_payload(decode=True) for p in images] == [ref.read_bytes() for ref in refs]
    fields = {p.get_param("name", header="content-disposition"): p.get_payload(decode=True)
              for p in parts if p not in images}
    assert fields["background"] == b"transparent"
    assert fields["n"] == b"1"
    assert [r["sha256"] for r in result.extra["references"]] == [hashlib.sha256(png()).hexdigest()] * 2


def test_transport_timeout_is_not_retried(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "secret-test-key")
    calls = []

    def fail(*args, **kwargs):
        calls.append(1)
        raise TimeoutError("secret-test-key")

    monkeypatch.setattr(adapter, "urlopen", fail)
    with pytest.raises(SystemExit, match="no automatic retry") as exc:
        gen.generate_image("openai", "sprite", tmp_path / "out.png")
    assert not isinstance(exc.value, GenTimeoutError)
    assert "secret-test-key" not in str(exc.value)
    assert len(calls) == 1
    assert not (tmp_path / "out.png").exists()


def test_http_error_does_not_expose_response_or_retry(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "secret-test-key")
    calls = []

    def fail(*args, **kwargs):
        calls.append(1)
        raise HTTPError("url", 429, "secret-test-key", {"x-request-id": "req-error"},
                        io.BytesIO(b"secret-test-key"))

    monkeypatch.setattr(adapter, "urlopen", fail)
    with pytest.raises(SystemExit, match="HTTP 429") as exc:
        gen.generate_image("openai", "sprite", tmp_path / "out.png")
    assert "secret-test-key" not in str(exc.value)
    assert "req-error" in str(exc.value)
    assert len(calls) == 1


@pytest.mark.parametrize("payload", [{}, {"data": [{"b64_json": "bad!"}]},
                                    {"data": [{"b64_json": base64.b64encode(b"not PNG").decode()}]}])
def test_invalid_image_is_not_published(monkeypatch, tmp_path, payload):
    install(monkeypatch, payload)
    with pytest.raises(SystemExit, match="no valid PNG"):
        gen.generate_image("openai", "sprite", tmp_path / "out.png")
    assert not (tmp_path / "out.png").exists()


def test_missing_key_fails_before_transport(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(SystemExit, match="OPENAI_API_KEY is required"):
        adapter.OpenAIProvider().generate(GenRequest("sprite", tmp_path / "raw.png"), tmp_path)


def test_openai_is_explicitly_registered_and_defaults_unchanged():
    from sprite_gen.gen import gen_set
    import argparse
    parser = argparse.ArgumentParser()
    gen_set.add_arguments(parser)
    assert parser.parse_args(["--run-dir", ".", "--provider", "openai"]).provider == "openai"
    assert gen.HARD_DEFAULT_PROVIDER == "codex"
    assert gen._make_provider("codex", keep_session=False).name == "codex"
    assert gen._make_provider("grok", keep_session=False).name == "grok"


def test_cli_creates_report_directory_before_paid_request(monkeypatch, tmp_path):
    report = tmp_path / "new" / "reports" / "generation.json"
    calls = install(monkeypatch)
    transport = adapter.urlopen

    def send(req, timeout):
        assert report.parent.is_dir(), "report destination must exist before sending"
        return transport(req, timeout)

    monkeypatch.setattr(adapter, "urlopen", send)
    assert gen.run(provider="openai", prompt="sprite", out=tmp_path / "out.png", report=report) == 0
    assert len(calls) == 1
    saved = json.loads(report.read_text())
    assert saved["extra"]["request_id"] == "req-test"
    assert saved["extra"]["usage"] == {"total_tokens": 42}


def test_invalid_report_parent_fails_before_paid_request(monkeypatch, tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("not a directory")
    calls = install(monkeypatch)
    with pytest.raises(OSError):
        gen.run(provider="openai", prompt="sprite", out=tmp_path / "out.png",
                report=blocker / "report.json")
    assert calls == []
