from langchain_core.language_models.chat_models import BaseChatModel
from src.infrastructure.config.settings import config


def create_chat_model(model_string: str) -> BaseChatModel:
    """Create a LangChain chat model from a 'provider/model-name' string.

    Supported providers: google, openai, anthropic, ollama.
    """
    provider, _, model_name = model_string.partition("/")
    if not model_name:
        raise ValueError(
            f"Invalid model string '{model_string}'. Expected format: 'provider/model-name'"
        )

    shared = dict(
        temperature=config.ai.temperature,
        max_tokens=config.ai.max_tokens,
        timeout=config.ai.sdk_timeout,
        max_retries=config.ai.sdk_retries,
    )

    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model_name, **shared)

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model_name, **shared)

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model_name=model_name, **shared)

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model_name, **shared)

    raise ValueError(f"Unknown provider '{provider}'. Supported: google, openai, anthropic, ollama")
