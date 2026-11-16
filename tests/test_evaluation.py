from run_tests import evaluate_questions


class MixedBot:
    def ask(self, question):
        if question == "fails":
            raise RuntimeError("provider unavailable")
        return {
            "answer": "grounded answer",
            "sources": [{"metadata": {"source_path": "course/lecture.txt"}}],
        }


def test_failures_are_not_counted_as_answers():
    results, failures = evaluate_questions(MixedBot(), ["works", "fails"])

    assert [result["question"] for result in results] == ["works"]
    assert results[0]["status"] == "ok"
    assert [failure["question"] for failure in failures] == ["fails"]
    assert failures[0]["status"] == "error"
