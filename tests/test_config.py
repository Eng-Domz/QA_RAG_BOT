import pytest

from config import load_settings


def test_defaults_are_valid_and_consistent():
    settings = load_settings({})

    assert settings.llm_provider == "ollama"
    assert settings.ollama_model == "llama3.2:1b"
    assert settings.gpu_device == "cpu"
    assert settings.hybrid_weights == (0.5, 0.5)


@pytest.mark.parametrize(
    "environment, message",
    [
        ({"CHUNK_SIZE": "100", "CHUNK_OVERLAP": "100"}, "CHUNK_OVERLAP"),
        ({"SIMILARITY_THRESHOLD": "1.5"}, "SIMILARITY_THRESHOLD"),
        ({"LLM_PROVIDER": "unknown"}, "LLM_PROVIDER"),
        ({"USE_GPU": "sometimes"}, "USE_GPU"),
        ({"HYBRID_WEIGHTS": "nan,1"}, "HYBRID_WEIGHTS"),
        ({"HYBRID_WEIGHTS": "inf,1"}, "HYBRID_WEIGHTS"),
    ],
)
def test_invalid_configuration_fails_early(environment, message):
    with pytest.raises(ValueError, match=message):
        load_settings(environment)


def test_hybrid_weights_are_normalized():
    settings = load_settings({"HYBRID_WEIGHTS": "3,1"})

    assert settings.hybrid_weights == (0.75, 0.25)
