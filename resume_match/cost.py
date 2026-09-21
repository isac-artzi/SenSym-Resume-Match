"""A rough token-count and dollar-cost estimate, shown before generation.

Deliberately approximate (PRD §6: "a clear 'this is an estimate' label") —
this counts characters, not real tokens, and uses per-job token constants
observed empirically rather than re-deriving the actual prompts. Good enough
to warn a student before a big batch, not a substitute for provider billing.
"""

from __future__ import annotations

from resume_match import ingest
from resume_match.llm import LLMConfig

# $ per million tokens, (input, output), for each provider's pinned default
# model (see llm.DEFAULT_MODELS). Checked directly against each provider's
# pricing page in September 2026 — like the model IDs themselves, recheck
# before trusting this months later; model pricing moves at least as often
# as model names do.
PROVIDER_PRICING = {
    "anthropic": (2.00, 10.00),  # Claude Sonnet 5
    "openai": (10.00, 50.00),  # GPT-6 Astra
    "gemini": (0.75, 3.75),  # Gemini 3.8 Flash, standard tier
    "ollama": (0.0, 0.0),  # runs on your own hardware, no per-token cost
}

CHARS_PER_TOKEN = 4  # standard rough heuristic for English text

# Empirically observed per-job token usage (extended thinking disabled, see
# llm.py) across analyze_job, generate_bundle, and fidelity_check. The
# bundle call dominates since it writes all seven documents in one response.
BASE_INPUT_TOKENS_PER_JOB = 5_300
BASE_OUTPUT_TOKENS_PER_JOB = 4_500

# Flat estimate for transcribing one scanned image (input image tokens, plus
# output transcription text) — that needs its own model call, which this
# estimate deliberately avoids making just to produce a number.
IMAGE_INPUT_TOKENS = 1_200
IMAGE_OUTPUT_TOKENS = 300


def estimate_tokens(
    credential_files: list[tuple[str, bytes]], job_files: list[tuple[str, bytes]]
) -> dict:
    """Estimate input/output token totals for a batch without calling any model.

    Text is extracted with the same parsers used for real generation (cheap —
    no network or model calls involved); images are counted but not sent for
    transcription here.
    """
    credential_result, _ = ingest.gather_credentials(credential_files, llm_config=None)
    credential_chars = len(credential_result.combined_text())
    num_images = sum(1 for w in credential_result.warnings if "transcribe images" in w)

    credential_tokens = credential_chars // CHARS_PER_TOKEN
    profile_input = credential_tokens + 400
    profile_output = min(max(credential_tokens // 2, 600), 2500)

    job_input_tokens = 0
    for name, data in job_files:
        job_result = ingest.ingest_files([(name, data)])
        text = job_result.sources[0].text if job_result.sources else ""
        job_input_tokens += len(text) // CHARS_PER_TOKEN

    n_jobs = len(job_files)
    input_tokens = (
        profile_input + job_input_tokens + n_jobs * BASE_INPUT_TOKENS_PER_JOB + num_images * IMAGE_INPUT_TOKENS
    )
    output_tokens = profile_output + n_jobs * BASE_OUTPUT_TOKENS_PER_JOB + num_images * IMAGE_OUTPUT_TOKENS
    return {"input_tokens": input_tokens, "output_tokens": output_tokens, "num_images": num_images}


def estimate_cost(
    llm_config: LLMConfig, credential_files: list[tuple[str, bytes]], job_files: list[tuple[str, bytes]]
) -> dict:
    """Estimate the USD cost of generating for `job_files`. See estimate_tokens()."""
    tokens = estimate_tokens(credential_files, job_files)
    input_price, output_price = PROVIDER_PRICING.get(llm_config.provider, (0.0, 0.0))
    cost_usd = (tokens["input_tokens"] / 1_000_000) * input_price + (tokens["output_tokens"] / 1_000_000) * output_price
    return {**tokens, "cost_usd": cost_usd}
