"""
Test script for evaluating the RAG QA system.
Run this to test the system with predefined questions and rate outputs.

Usage:
    python run_tests.py [--model llama3.2:1b] [--output results.json]
"""
import os
import sys
import json
import argparse
from datetime import datetime

from document_loader import DocumentProcessor
from vectorstore import VectorStoreManager
from qa_chain import QABot
from batch_processor import BatchProcessor


def load_questions(file_path="test_questions.txt"):
    """Load questions from file, skipping comment lines."""
    with open(file_path, "r", encoding="utf-8") as f:
        questions = [
            line.strip() for line in f
            if line.strip() and not line.strip().startswith("#")
        ]
    return questions


def rate_answer(question, answer, sources):
    """
    Rate an answer on a scale of 1-5.
    This is a placeholder for manual evaluation.
    For automated evaluation, implement metrics like BLEU, ROUGE, or use an LLM judge.
    """
    print(f"\nRate this answer (1-5):")
    print(f"  Q: {question}")
    print(f"  A: {answer[:200]}...")
    print(f"  Sources: {len(sources)} documents")
    while True:
        try:
            rating = input("Rating (1-5, or 's' to skip): ").strip()
            if rating.lower() == "s":
                return None
            rating = int(rating)
            if 1 <= rating <= 5:
                return rating
            print("Please enter a number between 1 and 5")
        except ValueError:
            print("Invalid input. Please enter a number between 1 and 5")


def run_tests(output_path="test_results.json", rate_interactively=False):
    """Run all tests and save results."""
    print("=" * 70)
    print("RAG QA System Evaluation")
    print("=" * 70)

    # Load questions
    questions = load_questions()
    print(f"\nLoaded {len(questions)} test questions")

    # Process documents
    print("\n[1/3] Processing documents...")
    processor = DocumentProcessor()
    docs = processor.process("./documents")
    print(f"Processed {len(docs)} document chunks")

    # Create vector store
    print("\n[2/3] Creating vector store...")
    store = VectorStoreManager(use_gpu=False)
    store.create_or_load(docs, force_rebuild=True)
    stats = store.get_collection_stats()
    print(f"Vector store: {stats['document_count']} documents")

    # Initialize bot
    print("\n[3/3] Initializing QA bot...")
    bot = QABot(store, use_openai=False, use_ollama=True)
    bot.initialize_chain()

    # Run tests
    print("\n" + "=" * 70)
    print("Running Tests")
    print("=" * 70)

    results = []
    batch = BatchProcessor(bot)

    for i, question in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] {question}")
        result = bot.ask(question)

        print(f"  Answer: {result['answer'][:150]}...")
        print(f"  Sources: {len(result['sources'])} documents retrieved")

        rating = None
        if rate_interactively:
            rating = rate_answer(question, result["answer"], result["sources"])

        results.append({
            "question": question,
            "answer": result["answer"],
            "sources": [s["metadata"].get("source_file", "Unknown") for s in result["sources"]],
            "source_count": len(result["sources"]),
            "rating": rating,
            "timestamp": datetime.now().isoformat(),
        })

    # Save results
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_path}")

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    rated = [r for r in results if r["rating"] is not None]
    if rated:
        avg_rating = sum(r["rating"] for r in rated) / len(rated)
        print(f"Average rating: {avg_rating:.2f}/5 ({len(rated)} rated)")
    print(f"Total questions: {len(results)}")
    print(f"Questions with sources: {sum(1 for r in results if r['source_count'] > 0)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test RAG QA system")
    parser.add_argument(
        "--output", "-o",
        default="test_results.json",
        help="Output file path (default: test_results.json)"
    )
    parser.add_argument(
        "--rate", "-r",
        action="store_true",
        help="Rate answers interactively"
    )
    args = parser.parse_args()

    run_tests(output_path=args.output, rate_interactively=args.rate)
