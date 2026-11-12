"""
Batch processing module for processing multiple questions at once.
Useful for evaluation or generating FAQs.
"""
import json
from typing import List, Dict, Any
from datetime import datetime

from qa_chain import QABot


class BatchProcessor:
    """
    Process multiple questions in batch and save results.
    """

    def __init__(self, bot: QABot):
        self.bot = bot

    def process_questions(
        self,
        questions: List[str],
        save_path: str = None,
        show_progress: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Process a list of questions and return results.

        Args:
            questions: List of questions to ask
            save_path: Optional path to save JSON results
            show_progress: Print progress to console

        Returns:
            List of result dictionaries
        """
        results = []
        total = len(questions)

        for i, question in enumerate(questions, 1):
            if show_progress:
                print(f"[{i}/{total}] Processing: {question[:50]}...")

            result = self.bot.ask(question)
            results.append({
                "question": question,
                "answer": result["answer"],
                "sources": [
                    source["metadata"].get(
                        "source_path", source["metadata"].get("source_file", "Unknown")
                    )
                    for source in result["sources"]
                ],
                "timestamp": datetime.now().isoformat(),
            })

        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\nSaved results to {save_path}")

        return results

    def process_from_file(self, questions_path: str, output_path: str = None) -> List[Dict[str, Any]]:
        """
        Load questions from a file (one per line) and process them.
        """
        with open(questions_path, "r", encoding="utf-8") as f:
            questions = [line.strip() for line in f if line.strip()]

        if not output_path:
            output_path = questions_path.replace(".txt", "_answers.json")

        return self.process_questions(questions, save_path=output_path)


# Example usage
if __name__ == "__main__":
    # This requires the bot to be initialized
    from document_loader import DocumentProcessor
    from vectorstore import VectorStoreManager

    # Initialize
    processor = DocumentProcessor()
    documents = processor.process("./documents")

    store = VectorStoreManager()
    store.create_or_load(documents)

    bot = QABot(store, use_openai=False, use_ollama=True)
    bot.initialize_chain()

    # Example batch questions
    questions = [
        "What is machine learning?",
        "What are the types of machine learning?",
        "What is overfitting?",
    ]

    batch = BatchProcessor(bot)
    results = batch.process_questions(questions, save_path="batch_results.json")

    print("\n" + "="*60)
    print("BATCH RESULTS SUMMARY")
    print("="*60)
    for r in results:
        print(f"Q: {r['question']}")
        print(f"A: {r['answer'][:200]}...\n")
