"""Load, validate, and generate `resume_match.env`.

The config never touches disk on the server in cloud mode — it is parsed
into a plain dict and held in `st.session_state`. Local mode may load
`resume_match.env` from the repo root if the student put one there.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

PROVIDERS = ["anthropic", "openai", "gemini", "ollama"]

# (key, comment, default) in the order they should appear in a generated file
FIELDS = [
    ("LLM_PROVIDER", "anthropic | openai | gemini | ollama", "anthropic"),
    ("API_KEY", "leave blank for ollama", ""),
    ("MODEL", "optional; provider default used if blank", ""),
    ("OLLAMA_BASE_URL", "ollama only", "http://localhost:11434"),
    ("CREDENTIALS_DIR", "local mode", ""),
    ("JOBS_DIR", "local mode", ""),
    ("OUTPUT_DIR", "local mode", ""),
    ("DRIVE_CREDENTIALS_URL", "cloud mode, optional; deferred to v1.1", ""),
    ("DRIVE_JOBS_URL", "cloud mode, optional; deferred to v1.1", ""),
    ("STUDENT_NAME", "optional", ""),
    ("TARGET_ROLE", "optional", ""),
    ("TONE", 'optional, e.g. "confident but understated"', ""),
    ("RESUME_MAX_PAGES", "optional", "1"),
    ("AVOID", 'optional, e.g. "buzzwords, the word synergy"', ""),
]

SECTION_BREAKS = {
    "LLM_PROVIDER": "--- AI provider ---",
    "CREDENTIALS_DIR": "--- Folders (local mode) ---",
    "DRIVE_CREDENTIALS_URL": "--- Folders (cloud mode, optional; deferred to v1.1) ---",
    "STUDENT_NAME": "--- Student preferences (all optional) ---",
}


@dataclass
class AppConfig:
    values: dict = field(default_factory=dict)

    def get(self, key: str, default: str = "") -> str:
        return self.values.get(key, default) or default

    @property
    def provider(self) -> str:
        return self.get("LLM_PROVIDER", "anthropic")

    @property
    def api_key(self) -> str:
        return self.get("API_KEY")

    @property
    def model(self) -> str:
        return self.get("MODEL")

    @property
    def ollama_base_url(self) -> str:
        return self.get("OLLAMA_BASE_URL", "http://localhost:11434")

    def credentials_dir(self) -> Path | None:
        value = self.get("CREDENTIALS_DIR")
        return Path(value).expanduser() if value else None

    def jobs_dir(self) -> Path | None:
        value = self.get("JOBS_DIR")
        return Path(value).expanduser() if value else None

    def output_dir(self) -> Path | None:
        value = self.get("OUTPUT_DIR")
        return Path(value).expanduser() if value else None

    def preferences_text(self) -> str:
        lines = []
        if self.get("STUDENT_NAME"):
            lines.append(f"Student name: {self.get('STUDENT_NAME')}")
        if self.get("TARGET_ROLE"):
            lines.append(f"Target role: {self.get('TARGET_ROLE')}")
        if self.get("TONE"):
            lines.append(f"Preferred tone: {self.get('TONE')}")
        if self.get("RESUME_MAX_PAGES"):
            lines.append(f"Resume max pages: {self.get('RESUME_MAX_PAGES')}")
        if self.get("AVOID"):
            lines.append(f"Avoid: {self.get('AVOID')}")
        return "\n".join(lines)


def parse_env_text(text: str) -> dict:
    """Parse simple `KEY=value` lines. Blank lines and `#` comments are ignored."""
    values = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.split("#", 1)[0].strip() if "#" in value else value.strip()
        values[key] = value
    return values


def load_env_file(path: Path) -> dict | None:
    """Read `resume_match.env` from `path` if it exists, else return None."""
    if not path.exists():
        return None
    return parse_env_text(path.read_text(encoding="utf-8"))


def generate_env_text(values: dict) -> str:
    """Render a config dict back out as a commented `.env` file the student can re-upload."""
    lines = []
    for key, comment, default in FIELDS:
        if key in SECTION_BREAKS:
            if lines:
                lines.append("")
            lines.append(f"# {SECTION_BREAKS[key]}")
        value = values.get(key, default)
        suffix = f"  # {comment}" if comment else ""
        lines.append(f"{key}={value}{suffix}")
    return "\n".join(lines) + "\n"


def detect_mode(config: AppConfig) -> str:
    """Local mode if both configured folders exist on this machine; cloud mode otherwise."""
    credentials_dir = config.credentials_dir()
    jobs_dir = config.jobs_dir()
    if credentials_dir and jobs_dir and credentials_dir.is_dir() and jobs_dir.is_dir():
        return "local"
    return "cloud"


def validate(config: AppConfig) -> list[str]:
    """Return a list of human-readable problems; empty list means ready to generate."""
    problems = []
    if config.provider not in PROVIDERS:
        problems.append(f"Unknown provider '{config.provider}'.")
    if config.provider != "ollama" and not config.api_key:
        problems.append("An API key is required for this provider.")
    return problems
