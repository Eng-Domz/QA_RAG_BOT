"""ASCII-safe setup validation for the supported Python 3.11 baseline."""

from __future__ import annotations

import importlib
import shutil
import sys
from pathlib import Path


REQUIRED_MODULES = [
    ("langchain", "langchain"),
    ("langchain_core", "langchain-core"),
    ("langchain_community", "langchain-community"),
    ("langchain_chroma", "langchain-chroma"),
    ("langchain_text_splitters", "langchain-text-splitters"),
    ("chromadb", "chromadb"),
    ("sentence_transformers", "sentence-transformers"),
    ("rank_bm25", "rank-bm25"),
]


def check_python_version() -> bool:
    print("Checking Python version...")
    version = sys.version_info
    if (version.major, version.minor) != (3, 11):
        print(
            f"[FAIL] Python 3.11 is required; found "
            f"{version.major}.{version.minor}.{version.micro}"
        )
        return False
    print(f"[OK] Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies() -> bool:
    print("\nChecking dependencies...")
    all_ok = True
    for module, package in REQUIRED_MODULES:
        try:
            importlib.import_module(module)
            print(f"  [OK] {package}")
        except ImportError:
            print(f"  [FAIL] {package} is not installed")
            all_ok = False
    return all_ok


def check_configuration() -> bool:
    print("\nChecking configuration...")
    try:
        import config

        print(f"[OK] LLM provider: {config.LLM_PROVIDER}")
        print(f"[OK] Retrieval mode: {config.RETRIEVAL_MODE}")
        return True
    except (ImportError, ValueError) as exc:
        print(f"[FAIL] Invalid configuration: {exc}")
        return False


def check_documents() -> bool:
    print("\nChecking documents...")
    documents = Path("documents")
    documents.mkdir(exist_ok=True)
    files = [path for path in documents.rglob("*") if path.is_file()]
    if not files:
        print(f"[FAIL] No documents found in {documents.resolve()}")
        return False
    print(f"[OK] Found {len(files)} document(s)")
    return True


def report_provider_prerequisite() -> None:
    print("\nChecking runtime provider...")
    try:
        from config import LLM_PROVIDER, OPENAI_API_KEY
    except (ImportError, ValueError):
        return
    if LLM_PROVIDER == "ollama":
        if shutil.which("ollama"):
            print("[OK] Ollama executable found")
        else:
            print(
                "[INFO] Ollama is not on PATH. Install it and pull the configured "
                "model before running generation."
            )
    elif OPENAI_API_KEY:
        print("[OK] OPENAI_API_KEY is configured")
    else:
        print("[INFO] OPENAI_API_KEY is required when LLM_PROVIDER=openai")


def main() -> int:
    print("=" * 60)
    print("QA Bot Setup Validation")
    print("=" * 60)
    checks = [
        check_python_version(),
        check_dependencies(),
        check_configuration(),
        check_documents(),
    ]
    report_provider_prerequisite()
    print("\n" + "=" * 60)
    if all(checks):
        print("[OK] Setup checks passed. Runtime provider must also be available.")
        return 0
    print("[FAIL] Setup is incomplete. See the messages above.")
    print("Install dependencies with: python -m pip install -r requirements.txt")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
