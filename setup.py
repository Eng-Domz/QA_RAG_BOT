"""
Setup and validation script.
Run this before first use to check dependencies and configuration.
"""
import os
import sys
import importlib
from pathlib import Path


def check_python_version():
    """Check Python version >= 3.9"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9+ required (3.10-3.11 recommended)")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """Check if required packages are installed"""
    print("\nChecking dependencies...")
    required = [
        ("langchain", "langchain"),
        ("langchain_core", "langchain-core"),
        ("langchain_community", "langchain-community"),
        ("langchain_chroma", "langchain-chroma"),
        ("langchain_text_splitters", "langchain-text-splitters"),
        ("chromadb", "chromadb"),
        ("sentence_transformers", "sentence-transformers"),
    ]

    optional = [
        "openai",
        "tiktoken",
    ]

    all_ok = True
    for module, package in required:
        try:
            importlib.import_module(module)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - not installed")
            all_ok = False

    for package in optional:
        try:
            importlib.import_module(package)
            print(f"  ✅ {package} (optional)")
        except ImportError:
            print(f"  ⚠️  {package} (optional) - not installed")

    return all_ok


def check_configuration():
    """Check if .env file exists"""
    print("\nChecking configuration...")
    env_path = Path(".env")

    if env_path.exists():
        print("✅ .env file found")

        # Check content
        with open(env_path) as f:
            content = f.read()
            if "OPENAI_API_KEY" in content and "=" in content.split("OPENAI_API_KEY")[1][:20]:
                print("✅ OPENAI_API_KEY found")
            else:
                print("ℹ️  Using Ollama (local LLM) - no API key needed")
            return True
    else:
        print("⚠️  .env file not found")
        print("   Using default settings (Ollama)")
        return True


def check_documents():
    """Check if documents directory exists and has files"""
    print("\nChecking documents...")
    docs_path = Path("documents")

    if not docs_path.exists():
        docs_path.mkdir()
        print(f"✅ Created documents directory: {docs_path.absolute()}")
        print("   Add your documents here (.pdf, .txt, .md)")
        return False

    files = list(docs_path.rglob("*"))
    files = [f for f in files if f.is_file()]

    if files:
        print(f"✅ Found {len(files)} document(s):")
        for f in files:
            print(f"   - {f.name}")
        return True
    else:
        print(f"⚠️  No documents in {docs_path.absolute()}")
        print("   Add documents before running main.py")
        return False


def print_next_steps(all_ok):
    """Print next steps"""
    print("\n" + "="*60)
    if all_ok:
        print("✅ Setup complete! Ready to run.")
        print("\nRun the bot:")
        print("  python main.py")
        print("\nOr with rebuild:")
        print("  python main.py --rebuild")
    else:
        print("⚠️  Setup incomplete. Please fix the issues above.")
        print("\nInstall dependencies:")
        print("  pip install -r requirements.txt")
    print("="*60)


def main():
    """Run all checks"""
    print("="*60)
    print("📦 QA Bot Setup")
    print("="*60)

    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Configuration", check_configuration),
        ("Documents", check_documents),
    ]

    results = []
    for name, check_fn in checks:
        try:
            result = check_fn()
            results.append(result)
        except Exception as e:
            print(f"❌ Error in {name}: {e}")
            results.append(False)

    all_ok = all(results)
    print_next_steps(all_ok)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
