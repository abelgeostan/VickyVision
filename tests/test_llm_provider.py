import pytest
from app.llm.ollama import OllamaProvider
from app.core.config import settings


def test_ollama_provider_health():
    """Verifies connection to the user's Ollama instance at OLLAMA_BASE_URL."""
    provider = OllamaProvider(base_url=settings.OLLAMA_BASE_URL, timeout=10.0)
    is_healthy = provider.check_health()
    assert is_healthy is True, f"Ollama instance at {settings.OLLAMA_BASE_URL} should be healthy and reachable."


def test_ollama_list_models():
    """Verifies that installed models (e.g. gemma3:4b, qwen3:4b) can be listed from Ollama."""
    provider = OllamaProvider(base_url=settings.OLLAMA_BASE_URL, timeout=10.0)
    models = provider.list_models()
    assert isinstance(models, list)
    assert len(models) > 0, "At least one model should be available on the Ollama host."
    # Check that either gemma3:4b or qwen3:4b is present
    has_expected_model = any("gemma" in m or "qwen" in m for m in models)
    assert has_expected_model is True, f"Expected models not found in {models}"


def test_ollama_generate_short():
    """Tests live generation with a fast token limit."""
    provider = OllamaProvider(base_url=settings.OLLAMA_BASE_URL, timeout=30.0)
    response = provider.generate(
        prompt="Respond with only the single word: OK",
        model=settings.DEFAULT_MODEL,
        options={"num_predict": 10},
    )
    assert response.content is not None
    assert response.model == settings.DEFAULT_MODEL
