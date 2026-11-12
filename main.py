"""
Main entry point for the QA Bot.
Run this to ingest documents and start the interactive session.
"""
import os
import sys
from pathlib import Path

from config import DOCUMENTS_DIR, USE_GPU, GPU_DEVICE, LLM_PROVIDER
from document_loader import DocumentProcessor
from vectorstore import VectorStoreManager
from qa_chain import QABot


def _has_real_openai_key() -> bool:
    """Return True only when a non-placeholder OpenAI API key is configured."""
    value = (os.environ.get("OPENAI_API_KEY") or "").strip()
    invalid_values = {"", "your-api-key-here", "none", "null", "changeme"}
    return value.lower() not in invalid_values


def _configure_console_output() -> None:
    """Keep CLI output printable in Windows consoles and redirected streams."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


def _provider_flags(provider: str, has_openai_key: bool) -> tuple[bool, bool]:
    """Resolve provider flags without silently changing an explicit choice."""
    if provider == "openai":
        if not has_openai_key:
            raise ValueError(
                "LLM_PROVIDER=openai requires a non-placeholder OPENAI_API_KEY"
            )
        return True, False
    if provider == "ollama":
        return False, True
    raise ValueError(f"Unsupported LLM provider: {provider}")


def ingest_documents(
    force_rebuild: bool = False, allow_empty_sync: bool = False
):
    """
    Process documents and create the vector store.

    Args:
        force_rebuild: If True, delete existing vector store and rebuild
    """
    # Check for documents
    if not os.path.exists(DOCUMENTS_DIR):
        os.makedirs(DOCUMENTS_DIR)
        print(f"Created documents folder: {DOCUMENTS_DIR}")
        print("Please add your documents (.pdf, .txt, .md, .docx) to this folder.")
        print("Then run this script again.")
        return None

    # List documents
    files = [f for f in Path(DOCUMENTS_DIR).rglob("*") if f.is_file()]
    if not files:
        if allow_empty_sync:
            if force_rebuild:
                raise ValueError("--rebuild and --sync-empty cannot be used together")
            print("No documents found; synchronizing the persisted index to empty.")
            store = VectorStoreManager(use_gpu=USE_GPU, gpu_device=GPU_DEVICE)
            store.create_or_load([], force_rebuild=False)
            return store
        print(f"No documents found in {DOCUMENTS_DIR}")
        print("Please add documents and try again.")
        return None

    print(f"Found {len(files)} files in {DOCUMENTS_DIR}")

    # Process documents
    processor = DocumentProcessor()
    documents = processor.process(DOCUMENTS_DIR)

    if not documents:
        print("No documents were successfully processed.")
        return None

    # Create vector store
    store = VectorStoreManager(use_gpu=USE_GPU, gpu_device=GPU_DEVICE)
    if USE_GPU:
        print(f"Using GPU for embeddings: {store.embedding_device_label}")
    store.create_or_load(documents, force_rebuild=force_rebuild)

    stats = store.get_collection_stats()
    print(f"\nVector Store Stats: {stats}")

    return store


def interactive_mode(bot: QABot):
    """
    Run interactive question-answering session.
    """
    print("\n" + "="*60)
    print("QA Bot is ready!")
    print("="*60)
    print("Commands:")
    print("  /quit or /q  - Exit")
    print("  /debug       - Show retrieved documents for debugging")
    print("  /sources     - Show source documents with answer")
    print("="*60 + "\n")

    show_sources = False

    while True:
        try:
            question = input("\nQuestion: ").strip()

            if not question:
                continue

            if question.lower() in ["/quit", "/q", "exit", "quit"]:
                print("Goodbye!")
                break

            if question.lower() == "/debug":
                question = input("Enter question to debug: ").strip()
                bot.debug_retrieval(question)
                continue

            if question.lower() == "/sources":
                show_sources = not show_sources
                print(f"Source display: {'ON' if show_sources else 'OFF'}")
                continue

            # Get answer
            print("\nThinking...")
            result = bot.ask(question)

            print(f"\nAnswer: {result['answer']}")
            print(f"\nContext: {result.get('context_info', '')}")

            if show_sources:
                print("\nSources:")
                for i, source in enumerate(result['sources'], 1):
                    metadata = source["metadata"]
                    print(
                        f"   {i}. "
                        f"{metadata.get('source_path', metadata.get('source_file', 'Unknown'))}"
                    )

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


def main() -> int:
    """
    Main function to run the QA Bot.
    """
    _configure_console_output()
    print("Document QA Bot")
    print("="*60)

    # Check arguments
    force_rebuild = "--rebuild" in sys.argv
    allow_empty_sync = "--sync-empty" in sys.argv

    # Step 1: Ingest documents
    print("\nStep 1: Loading documents...")
    store = ingest_documents(
        force_rebuild=force_rebuild, allow_empty_sync=allow_empty_sync
    )

    if store is None:
        print("\nPlease add documents and restart.")
        print(f"   Documents folder: {DOCUMENTS_DIR}")
        return 1

    if store.get_collection_stats().get("document_count", 0) == 0:
        print("Persisted index is now empty. Add documents before asking questions.")
        return 0

    # Step 2: Initialize QA Chain
    print("\nStep 2: Initializing QA chain...")

    # Determine which LLM to use.
    # Default is Ollama (free/local). Use OpenAI only when explicitly selected.
    llm_provider = LLM_PROVIDER
    has_openai_key = _has_real_openai_key()

    try:
        use_openai, use_ollama = _provider_flags(llm_provider, has_openai_key)
        bot = QABot(store, use_openai=use_openai, use_ollama=use_ollama)
        bot.initialize_chain()
    except Exception as e:
        print(f"\nFailed to initialize LLM: {e}")
        print("\nOptions:")
        print("  1. (PAID) Set OPENAI_API_KEY environment variable")
        print("  2. (FREE) Install Ollama:")
        print("     - Download from https://ollama.ai")
        print("     - Run: ollama pull llama3.2")
        print("     - Make sure Ollama is running in the background")
        return 1

    # Step 3: Start interactive mode
    interactive_mode(bot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
