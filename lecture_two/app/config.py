from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Optional until a live call is requested: offline lessons need no key.
    groq_api_key: SecretStr | None = None
    groq_model: str = "openai/gpt-oss-20b"
    groq_structured_model: str = "openai/gpt-oss-20b"
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    def api_key(self) -> str:
        if not self.groq_api_key or not self.groq_api_key.get_secret_value().strip():
            raise ValueError("Set GROQ_API_KEY in .env before running a live example.")
        return self.groq_api_key.get_secret_value()
