"""
API Configuration
==================
All settings are loaded from environment variables so secrets never live in code.

  Development:  create a .env file in the project root (see .env.example)
  Production:   set environment variables in Render / Railway / etc.

Switch LLM provider by setting LLM_PROVIDER in .env — no code changes needed.

Supported providers
-------------------
  groq        GROQ_API_KEY          — free tier, fast, good tool-calling (default)
  openai      OPENAI_API_KEY        — GPT-4o, GPT-4o-mini, etc.
  anthropic   ANTHROPIC_API_KEY     — Claude 3.5 Sonnet / Haiku
  gemini      GOOGLE_API_KEY        — Gemini 2.0 Flash, Pro, etc.
  mistral     MISTRAL_API_KEY       — Mistral Small / Large
  ollama      (no key)              — local models via Ollama (llama3, mistral, etc.)

Default models per provider (override with LLM_MODEL):
  groq      → llama-3.3-70b-versatile
  openai    → gpt-4o-mini
  anthropic → claude-3-5-haiku-20241022
  gemini    → gemini-2.0-flash
  mistral   → mistral-small-latest
  ollama    → llama3.2
"""

from pathlib import Path

from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).parent.parent

PROVIDER_DEFAULTS: dict[str, str] = {
    "groq":      "llama-3.3-70b-versatile",
    "openai":    "gpt-4o-mini",
    "anthropic": "claude-3-5-haiku-20241022",
    "gemini":    "gemini-2.0-flash",
    "mistral":   "mistral-small-latest",
    "ollama":    "llama3.2",
    "nvidia":    "nvidia/llama-3.1-nemotron-70b-instruct",
}

SUPPORTED_PROVIDERS = set(PROVIDER_DEFAULTS)


class Settings(BaseSettings):
    # ── Game data API keys ────────────────────────────────────────────────
    steam_api_key: str = ""
    playerpulse_rawg_api_key: str = ""

    # ── LLM provider selection ────────────────────────────────────────────
    llm_provider: str = "groq"   # any key in SUPPORTED_PROVIDERS
    llm_model: str = ""          # empty → use PROVIDER_DEFAULTS[llm_provider]

    # ── LLM API keys (only the active provider's key is required) ─────────
    groq_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    mistral_api_key: str = ""
    # Ollama runs locally — no key needed, but base URL is configurable
    ollama_base_url: str = "http://localhost:11434"

    # NVIDIA NIM — OpenAI-compatible endpoint
    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"

    # ── CORS ──────────────────────────────────────────────────────────────
    # In prod, set CORS_ORIGINS=https://your-app.vercel.app in Render dashboard.
    # Multiple origins: CORS_ORIGINS=https://foo.vercel.app,https://bar.vercel.app
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ── Paths ─────────────────────────────────────────────────────────────
    models_dir: Path = PROJECT_ROOT / "models"
    data_dir: Path = PROJECT_ROOT / "data"
    studios_dir: Path = PROJECT_ROOT / "data" / "studios"
    features_path: Path = PROJECT_ROOT / "data" / "03_features" / "player_features.parquet"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def resolved_model(self) -> str:
        """Return llm_model if set, otherwise the provider default."""
        return self.llm_model or PROVIDER_DEFAULTS.get(self.llm_provider, "")


settings = Settings()


def get_llm(streaming: bool = False):
    """
    Return a LangChain chat model for the configured provider.

    Switch provider and model entirely via .env — no code changes needed:
        LLM_PROVIDER=anthropic
        LLM_MODEL=claude-3-5-sonnet-20241022

    Args:
        streaming: enable token-by-token streaming (used by chat endpoints)
    """
    provider = settings.llm_provider.lower()
    model    = settings.resolved_model

    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{provider}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_PROVIDERS))}"
        )

    if provider == "groq":
        _require_key("GROQ_API_KEY", settings.groq_api_key)
        from langchain_groq import ChatGroq
        return ChatGroq(model=model, api_key=settings.groq_api_key, streaming=streaming)

    if provider == "openai":
        _require_key("OPENAI_API_KEY", settings.openai_api_key)
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, api_key=settings.openai_api_key, streaming=streaming)

    if provider == "anthropic":
        _require_key("ANTHROPIC_API_KEY", settings.anthropic_api_key)
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model, api_key=settings.anthropic_api_key, streaming=streaming)

    if provider == "gemini":
        _require_key("GOOGLE_API_KEY", settings.google_api_key)
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model, google_api_key=settings.google_api_key,
                                      streaming=streaming)

    if provider == "mistral":
        _require_key("MISTRAL_API_KEY", settings.mistral_api_key)
        from langchain_mistralai import ChatMistralAI
        return ChatMistralAI(model=model, api_key=settings.mistral_api_key, streaming=streaming)

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model, base_url=settings.ollama_base_url)

    if provider == "nvidia":
        _require_key("NVIDIA_API_KEY", settings.nvidia_api_key)
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model,
            api_key=settings.nvidia_api_key,
            base_url=settings.nvidia_base_url,
            streaming=streaming,
        )

    # Should never reach here given the check above
    raise ValueError(f"Unhandled provider: {provider}")


def _require_key(env_var: str, value: str) -> None:
    if not value:
        raise EnvironmentError(
            f"{env_var} is not set. Add it to your .env file:\n"
            f"  {env_var}=your_key_here"
        )
