"""Validated application configuration loaded from environment variables."""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from dotenv import load_dotenv


load_dotenv()
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")


def _value(env: Mapping[str, str], name: str, default: str) -> str:
    return str(env.get(name, default)).strip()


def _boolean(env: Mapping[str, str], name: str, default: bool) -> bool:
    raw = _value(env, name, str(default)).lower()
    if raw in {"true", "1", "yes", "on"}:
        return True
    if raw in {"false", "0", "no", "off"}:
        return False
    raise ValueError(f"{name} must be true or false, got {raw!r}")


def _integer(
    env: Mapping[str, str], name: str, default: int, *, minimum: int = 0
) -> int:
    raw = _value(env, name, str(default))
    try:
        parsed = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc
    if parsed < minimum:
        raise ValueError(f"{name} must be at least {minimum}, got {parsed}")
    return parsed


def _floating(
    env: Mapping[str, str],
    name: str,
    default: float,
    *,
    minimum: float,
    maximum: float,
) -> float:
    raw = _value(env, name, str(default))
    try:
        parsed = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number, got {raw!r}") from exc
    if not minimum <= parsed <= maximum:
        raise ValueError(
            f"{name} must be between {minimum} and {maximum}, got {parsed}"
        )
    return parsed


def _choice(
    env: Mapping[str, str], name: str, default: str, choices: set[str]
) -> str:
    raw = _value(env, name, default).lower()
    if raw not in choices:
        allowed = ", ".join(sorted(choices))
        raise ValueError(f"{name} must be one of {allowed}, got {raw!r}")
    return raw


def _weights(env: Mapping[str, str]) -> tuple[float, float]:
    raw = _value(env, "HYBRID_WEIGHTS", "0.5,0.5")
    try:
        values = tuple(float(item.strip()) for item in raw.split(","))
    except ValueError as exc:
        raise ValueError("HYBRID_WEIGHTS must contain two numbers") from exc
    if len(values) != 2 or any(
        not math.isfinite(value) or value < 0 for value in values
    ):
        raise ValueError("HYBRID_WEIGHTS must contain two non-negative numbers")
    total = sum(values)
    if total <= 0:
        raise ValueError("HYBRID_WEIGHTS must have a positive total")
    return values[0] / total, values[1] / total


@dataclass(frozen=True)
class AppSettings:
    base_dir: Path
    documents_dir: Path
    vectorstore_dir: Path
    embedding_model: str
    use_gpu: bool
    gpu_device: str
    directml_adapter_preference: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    similarity_threshold: float
    retrieval_mode: str
    hybrid_weights: tuple[float, float]
    enable_query_expansion: bool
    enable_hyde: bool
    max_query_variants: int
    strict_grounding: bool
    fallback_to_top_k_if_below_threshold: bool
    llm_provider: str
    llm_model: str
    llm_temperature: float
    max_tokens: int
    openai_api_key: str | None
    ollama_base_url: str
    ollama_model: str


def load_settings(env: Mapping[str, str] | None = None) -> AppSettings:
    """Build validated settings, optionally from an explicit mapping for tests."""
    values = os.environ if env is None else env
    base_dir = Path(__file__).resolve().parent
    chunk_size = _integer(values, "CHUNK_SIZE", 1000, minimum=1)
    chunk_overlap = _integer(values, "CHUNK_OVERLAP", 200, minimum=0)
    if chunk_overlap >= chunk_size:
        raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")

    return AppSettings(
        base_dir=base_dir,
        documents_dir=base_dir / "documents",
        vectorstore_dir=base_dir / "chroma_db",
        embedding_model=_value(
            values, "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        ),
        use_gpu=_boolean(values, "USE_GPU", False),
        gpu_device=_choice(
            values,
            "GPU_DEVICE",
            "cpu",
            {"cpu", "cuda", "directml", "dml", "intel", "mps", "xpu"},
        ),
        directml_adapter_preference=_value(
            values, "DIRECTML_ADAPTER_PREFERENCE", "intel"
        ),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        top_k=_integer(values, "TOP_K", 5, minimum=1),
        similarity_threshold=_floating(
            values, "SIMILARITY_THRESHOLD", 0.3, minimum=0.0, maximum=1.0
        ),
        retrieval_mode=_choice(
            values, "RETRIEVAL_MODE", "standard", {"standard", "hybrid"}
        ),
        hybrid_weights=_weights(values),
        enable_query_expansion=_boolean(values, "ENABLE_QUERY_EXPANSION", False),
        enable_hyde=_boolean(values, "ENABLE_HYDE", False),
        max_query_variants=_integer(values, "MAX_QUERY_VARIANTS", 4, minimum=1),
        strict_grounding=_boolean(values, "STRICT_GROUNDING", False),
        fallback_to_top_k_if_below_threshold=_boolean(
            values, "FALLBACK_TO_TOP_K_IF_BELOW_THRESHOLD", True
        ),
        llm_provider=_choice(
            values, "LLM_PROVIDER", "ollama", {"ollama", "openai"}
        ),
        llm_model=_value(values, "LLM_MODEL", "gpt-4o-mini"),
        llm_temperature=_floating(
            values, "LLM_TEMPERATURE", 0.3, minimum=0.0, maximum=2.0
        ),
        max_tokens=_integer(values, "MAX_TOKENS", 1000, minimum=1),
        openai_api_key=values.get("OPENAI_API_KEY") or None,
        ollama_base_url=_value(
            values, "OLLAMA_BASE_URL", "http://localhost:11434"
        ),
        ollama_model=_value(values, "OLLAMA_MODEL", "llama3.2:1b"),
    )


SETTINGS = load_settings()
SETTINGS.documents_dir.mkdir(parents=True, exist_ok=True)
SETTINGS.vectorstore_dir.mkdir(parents=True, exist_ok=True)

# Backward-compatible constants used by the existing modules.
BASE_DIR = str(SETTINGS.base_dir)
DOCUMENTS_DIR = str(SETTINGS.documents_dir)
VECTORSTORE_DIR = str(SETTINGS.vectorstore_dir)
EMBEDDING_MODEL = SETTINGS.embedding_model
USE_GPU = SETTINGS.use_gpu
GPU_DEVICE = SETTINGS.gpu_device
DIRECTML_ADAPTER_PREFERENCE = SETTINGS.directml_adapter_preference
CHUNK_SIZE = SETTINGS.chunk_size
CHUNK_OVERLAP = SETTINGS.chunk_overlap
TOP_K = SETTINGS.top_k
SIMILARITY_THRESHOLD = SETTINGS.similarity_threshold
RETRIEVAL_MODE = SETTINGS.retrieval_mode
HYBRID_WEIGHTS = list(SETTINGS.hybrid_weights)
ENABLE_QUERY_EXPANSION = SETTINGS.enable_query_expansion
ENABLE_HYDE = SETTINGS.enable_hyde
MAX_QUERY_VARIANTS = SETTINGS.max_query_variants
STRICT_GROUNDING = SETTINGS.strict_grounding
FALLBACK_TO_TOP_K_IF_BELOW_THRESHOLD = SETTINGS.fallback_to_top_k_if_below_threshold
LLM_PROVIDER = SETTINGS.llm_provider
LLM_MODEL = SETTINGS.llm_model
LLM_TEMPERATURE = SETTINGS.llm_temperature
MAX_TOKENS = SETTINGS.max_tokens
OPENAI_API_KEY = SETTINGS.openai_api_key
OLLAMA_BASE_URL = SETTINGS.ollama_base_url
OLLAMA_MODEL = SETTINGS.ollama_model
