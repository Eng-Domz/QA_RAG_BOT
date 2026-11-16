"""Provider-backed manual RAG evaluation.

This command is intentionally separate from the deterministic pytest suite. It
requires a working Ollama model and exits non-zero when any question fails.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from document_loader import DocumentProcessor
from qa_chain import QABot
from vectorstore import VectorStoreManager


def load_questions(file_path: str = "test_questions.txt") -> list[str]:
    with open(file_path, "r", encoding="utf-8") as handle:
        return [
            line.strip()
            for line in handle
            if line.strip() and not line.strip().startswith("#")
        ]


def rate_answer(question: str, answer: str, sources: list[dict]) -> int | None:
    print("\nRate this answer (1-5):")
    print(f"  Q: {question}")
    print(f"  A: {answer[:200]}...")
    print(f"  Sources: {len(sources)} documents")
    while True:
        rating = input("Rating (1-5, or 's' to skip): ").strip()
        if rating.lower() == "s":
            return None
        try:
            parsed = int(rating)
        except ValueError:
            print("Invalid input. Please enter a number between 1 and 5")
            continue
        if 1 <= parsed <= 5:
            return parsed
        print("Please enter a number between 1 and 5")


def evaluate_questions(
    bot: QABot, questions: Iterable[str], *, rate_interactively: bool = False
) -> tuple[list[dict], list[dict]]:
    """Evaluate questions while keeping failures separate from valid answers."""
    results: list[dict] = []
    failures: list[dict] = []
    for question in questions:
        try:
            result = bot.ask(question)
            sources = result["sources"]
            rating = (
                rate_answer(question, result["answer"], sources)
                if rate_interactively
                else None
            )
            results.append(
                {
                    "status": "ok",
                    "question": question,
                    "answer": result["answer"],
                    "sources": [
                        source["metadata"].get(
                            "source_path",
                            source["metadata"].get("source_file", "Unknown"),
                        )
                        for source in sources
                    ],
                    "source_count": len(sources),
                    "rating": rating,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        except Exception as exc:
            failures.append(
                {
                    "status": "error",
                    "question": question,
                    "error": str(exc),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
    return results, failures


def run_evaluation(
    output_path: str = "test_results.json", rate_interactively: bool = False
) -> int:
    questions = load_questions()
    print(f"Loaded {len(questions)} evaluation questions")

    processor = DocumentProcessor()
    documents = processor.process("./documents")
    store = VectorStoreManager(use_gpu=False)
    store.create_or_load(documents, force_rebuild=True)
    bot = QABot(store, use_openai=False, use_ollama=True)
    bot.initialize_chain()

    results, failures = evaluate_questions(
        bot, questions, rate_interactively=rate_interactively
    )
    payload = {
        "summary": {
            "total": len(questions),
            "succeeded": len(results),
            "failed": len(failures),
        },
        "results": results,
        "failures": failures,
    }
    Path(output_path).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Results saved to {output_path}")
    print(
        f"Summary: {len(results)} succeeded, {len(failures)} failed, "
        f"{len(questions)} total"
    )
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run provider-backed RAG evaluation")
    parser.add_argument(
        "--output", "-o", default="test_results.json", help="Output JSON path"
    )
    parser.add_argument(
        "--rate", "-r", action="store_true", help="Rate answers interactively"
    )
    args = parser.parse_args()
    try:
        return run_evaluation(args.output, args.rate)
    except Exception as exc:
        print(f"Evaluation could not start: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
