"""One thin client over four LLM providers: Anthropic, OpenAI, Gemini, Ollama.

Every other module only ever calls `complete()` or `complete_json()`. Provider
differences (auth, request shape, vision format, JSON mode) are confined to
this file so the rest of the app never has to know which provider is active.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

# Pinned default model per provider. Check each provider's docs before
# bumping these — a student's config can always override with MODEL=.
DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-5",
    "openai": "gpt-6-astra",
    "gemini": "gemini-3.8-flash",
    "ollama": "llama3.1",
}

MAX_RETRIES_ON_BAD_JSON = 1


class LLMError(Exception):
    """Raised with a message that is safe to show directly in the UI."""


@dataclass
class LLMConfig:
    provider: str  # anthropic | openai | gemini | ollama
    api_key: str = ""
    model: str = ""
    ollama_base_url: str = "http://localhost:11434"
    temperature: float = 0.4

    def resolved_model(self) -> str:
        return self.model.strip() if self.model.strip() else DEFAULT_MODELS[self.provider]


def complete(config: LLMConfig, prompt: str, images: list[bytes] | None = None) -> str:
    """Send `prompt` (plus optional raw image bytes) and return the text reply.

    `images` are PNG/JPEG bytes, sent for providers with vision support. Used
    for transcribing scanned diplomas/transcripts without a local OCR
    dependency.
    """
    try:
        if config.provider == "anthropic":
            return _complete_anthropic(config, prompt, images)
        if config.provider == "openai":
            return _complete_openai(config, prompt, images)
        if config.provider == "gemini":
            return _complete_gemini(config, prompt, images)
        if config.provider == "ollama":
            return _complete_ollama(config, prompt, images)
    except LLMError:
        raise
    except Exception as exc:  # provider SDK error -> friendly message
        raise LLMError(_friendly_error(config.provider, exc)) from exc

    raise LLMError(f"Unknown provider '{config.provider}'.")


def complete_json(config: LLMConfig, prompt: str, schema_hint: str, images: list[bytes] | None = None) -> dict:
    """Like `complete()`, but parses the reply as JSON.

    `schema_hint` is plain-text guidance appended to the prompt describing
    the expected JSON shape (not a formal JSON Schema — kept simple so
    students can read and edit prompts in `prompts/`). On malformed JSON,
    retries once with the parse error fed back to the model, then raises a
    friendly LLMError.
    """
    full_prompt = f"{prompt}\n\n{schema_hint}\n\nRespond with valid JSON only. No prose, no markdown fences."

    last_error = None
    for attempt in range(MAX_RETRIES_ON_BAD_JSON + 1):
        raw = complete(config, full_prompt, images)
        try:
            return _parse_json(raw)
        except (json.JSONDecodeError, ValueError) as exc:
            last_error = exc
            full_prompt = (
                f"{prompt}\n\n{schema_hint}\n\n"
                "Respond with valid JSON only. No prose, no markdown fences.\n\n"
                f"Your previous reply could not be parsed as JSON ({exc}). "
                "Reply again with corrected, valid JSON only."
            )

    raise LLMError(
        "The model returned a response that could not be read as data, even after a retry. "
        "Try again, or switch to a different model in Advanced settings."
    )


def _parse_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("no JSON object found in reply")
    return json.loads(text[start : end + 1])


def _friendly_error(provider: str, exc: Exception) -> str:
    text = str(exc).lower()
    if "api key" in text or "authentication" in text or "401" in text:
        return f"{provider.title()} rejected the API key. Check it in Setup and try again."
    if "rate limit" in text or "429" in text:
        return f"{provider.title()} rate-limited this request. Wait a moment and try again."
    if "connection" in text or "timeout" in text or "timed out" in text:
        return f"Could not reach {provider.title()}. Check your internet connection (and, for Ollama, that it is running)."
    return f"{provider.title()} returned an error: {exc}"


# --- Anthropic -----------------------------------------------------------


def _complete_anthropic(config: LLMConfig, prompt: str, images: list[bytes] | None) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=config.api_key)
    content = _anthropic_content(prompt, images)
    # Current Anthropic models (Claude 5 family) control response character via
    # reasoning effort rather than `temperature`, which the API no longer accepts,
    # and default to extended thinking that otherwise eats most of max_tokens
    # before any visible text is written (seen directly: a 4096-token budget
    # produced ~3700 thinking tokens and a truncated, unparsable JSON bundle).
    # Thinking is disabled so the full budget goes to visible output. max_tokens
    # is set well above what a synthetic test profile needed (~3800 for the
    # seven-document bundle) because a real student's fuller history produces a
    # bigger bundle; Sonnet 5 supports up to 128k here, so there's no cost or
    # latency downside to a generous ceiling — it only caps a worst case.
    response = client.messages.create(
        model=config.resolved_model(),
        max_tokens=16000,
        thinking={"type": "disabled"},
        messages=[{"role": "user", "content": content}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def _anthropic_content(prompt: str, images: list[bytes] | None) -> list[dict]:
    content: list[dict] = []
    for img in images or []:
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": _guess_image_media_type(img),
                    "data": _b64(img),
                },
            }
        )
    content.append({"type": "text", "text": prompt})
    return content


# --- OpenAI (also used for Ollama's OpenAI-compatible endpoint) ----------


def _complete_openai(config: LLMConfig, prompt: str, images: list[bytes] | None) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=config.api_key)
    return _openai_chat(client, config, prompt, images)


def _complete_ollama(config: LLMConfig, prompt: str, images: list[bytes] | None) -> str:
    from openai import OpenAI

    client = OpenAI(base_url=f"{config.ollama_base_url.rstrip('/')}/v1", api_key="ollama")
    if images:
        raise LLMError(
            "This model was asked to read an image, but Ollama vision support depends on the "
            "model you pulled. Skip image files or use a vision-capable Ollama model."
        )
    return _openai_chat(client, config, prompt, images)


def _openai_chat(client, config: LLMConfig, prompt: str, images: list[bytes] | None) -> str:
    content: list[dict] = [{"type": "text", "text": prompt}]
    for img in images or []:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:{_guess_image_media_type(img)};base64,{_b64(img)}"},
            }
        )
    response = client.chat.completions.create(
        model=config.resolved_model(),
        temperature=config.temperature,
        messages=[{"role": "user", "content": content}],
    )
    return response.choices[0].message.content or ""


# --- Gemini ----------------------------------------------------------------


def _complete_gemini(config: LLMConfig, prompt: str, images: list[bytes] | None) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=config.api_key)
    parts: list = []
    for img in images or []:
        parts.append(types.Part.from_bytes(data=img, mime_type=_guess_image_media_type(img)))
    parts.append(prompt)

    response = client.models.generate_content(
        model=config.resolved_model(),
        contents=parts,
        config=types.GenerateContentConfig(temperature=config.temperature),
    )
    return response.text or ""


# --- shared helpers ----------------------------------------------------------


def _b64(data: bytes) -> str:
    import base64

    return base64.b64encode(data).decode("ascii")


def _guess_image_media_type(data: bytes) -> str:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/png"
