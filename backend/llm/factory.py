from __future__ import annotations
from llm.base import LLMProvider

_instance: LLMProvider | None = None


def get_llm() -> LLMProvider:
    global _instance
    if _instance is None:
        _instance = _create()
    return _instance


def _create() -> LLMProvider:
    from settings import settings

    provider = settings.llm_provider.lower()

    if provider == "claude":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for LLM_PROVIDER=claude")
        from llm.claude import ClaudeProvider
        return ClaudeProvider(api_key=settings.anthropic_api_key)

    if provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required for LLM_PROVIDER=gemini")
        from llm.gemini import GeminiProvider
        return GeminiProvider(api_key=settings.gemini_api_key)

    if provider == "groq":
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is required for LLM_PROVIDER=groq")
        from llm.groq import GroqProvider
        return GroqProvider(api_key=settings.groq_api_key)

    if provider == "ollama":
        from llm.ollama import OllamaProvider
        return OllamaProvider(base_url=settings.ollama_base_url)

    if provider == "mock":
        from llm.mock import MockProvider
        return MockProvider()

    raise ValueError(
        f"Unknown LLM_PROVIDER={provider!r}. Choose from: claude, gemini, groq, ollama, mock"
    )
