from types import SimpleNamespace

import pytest
from langchain_core.documents import Document

import qa_chain
from qa_chain import QABot


def document(chunk_id="chunk-1"):
    return Document(
        page_content="grounded context",
        metadata={
            "chunk_id": chunk_id,
            "source_path": "course/lecture.txt",
            "source_file": "lecture.txt",
        },
    )


class FakeVectorStore:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def similarity_search(self, *args, **kwargs):
        self.calls.append(kwargs)
        return list(self.results)


class FakeAdvancedRetriever:
    ensemble_retriever = True

    def __init__(self, results):
        self.results = results

    def retrieve(self, *args, **kwargs):
        return list(self.results)


def make_bot(vector_results, hybrid_results, llm):
    bot = object.__new__(QABot)
    bot.vectorstore_manager = FakeVectorStore(vector_results)
    bot.advanced_retriever = FakeAdvancedRetriever(hybrid_results)
    bot.retrieval_mode = "hybrid"
    bot.llm = llm
    bot.qa_chain = True
    return bot


def test_strict_hybrid_refuses_when_semantic_gate_is_empty(monkeypatch):
    monkeypatch.setattr(qa_chain, "STRICT_GROUNDING", True)
    llm = SimpleNamespace(invoke=lambda prompt: pytest.fail("LLM must not be called"))
    bot = make_bot([], [document()], llm)

    result = bot.ask("unrelated question")

    assert result["sources"] == []
    assert "enough grounded context" in result["answer"]
    assert bot.vectorstore_manager.calls[0]["fallback_to_top_k"] is False


def test_provider_failure_is_raised_not_returned_as_an_answer(monkeypatch):
    monkeypatch.setattr(qa_chain, "STRICT_GROUNDING", False)

    def fail(_prompt):
        raise ConnectionError("provider unavailable")

    bot = make_bot([document()], [document()], SimpleNamespace(invoke=fail))

    with pytest.raises(RuntimeError, match="provider unavailable") as error:
        bot.ask("What is this?")

    assert isinstance(error.value.__cause__, ConnectionError)


def test_documents_are_deduplicated_by_stable_chunk_id(monkeypatch):
    monkeypatch.setattr(qa_chain, "STRICT_GROUNDING", False)
    repeated = document("same-id")
    bot = make_bot(
        [repeated],
        [repeated, document("same-id")],
        SimpleNamespace(invoke=lambda prompt: "answer"),
    )

    result = bot.ask("question")

    assert len(result["sources"]) == 1
