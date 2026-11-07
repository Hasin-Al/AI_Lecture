"""Validated configuration loaded from the process environment or local .env."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ProviderName = Literal[
    "gemini", "groq", "cerebras", "cohere", "cloudflare", "nvidia", "openrouter"
]


class Settings(BaseSettings):
    ai_provider: ProviderName = "gemini"

    gemini_api_key: SecretStr | None = None
    groq_api_key: SecretStr | None = None
    cerebras_api_key: SecretStr | None = None
    cohere_api_key: SecretStr | None = None
    cloudflare_api_token: SecretStr | None = None
    cloudflare_account_id: str | None = None
    nvidia_api_key: SecretStr | None = None
    openrouter_api_key: SecretStr | None = None

    gemini_model: str = "gemini-3.8-flash"
    groq_model: str = "openai/gpt-oss-20b"
    cerebras_model: str = "gpt-oss-120b"
    cohere_model: str = "command-a-plus-05-2026"
    cloudflare_model: str = "@cf/zai-org/glm-4.7-flash"
    nvidia_model: str = "nvidia/nemotron-3.5-bolt-e4b"
    openrouter_model: str = "openrouter/free"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def selected_provider_has_credentials(self) -> "Settings":
        credential_fields = {
            "gemini": ("gemini_api_key",),
            "groq": ("groq_api_key",),
            "cerebras": ("cerebras_api_key",),
            "cohere": ("cohere_api_key",),
            "cloudflare": ("cloudflare_api_token", "cloudflare_account_id"),
            "nvidia": ("nvidia_api_key",),
            "openrouter": ("openrouter_api_key",),
        }

        def plain_value(name: str) -> str:
            value = getattr(self, name)
            if isinstance(value, SecretStr):
                return value.get_secret_value()
            return value or ""

        missing = [
            name
            for name in credential_fields[self.ai_provider]
            if not plain_value(name).strip()
        ]
        if missing:
            raise ValueError(
                f"Set the selected provider's required .env value(s): {', '.join(missing)}"
            )

        for name in credential_fields[self.ai_provider]:
            value = plain_value(name)
            if not value.isascii() or any(character.isspace() for character in value):
                raise ValueError(
                    f"{name} must be a non-empty ASCII credential without whitespace"
                )

        model_field = f"{self.ai_provider}_model"
        model = getattr(self, model_field)
        if not model.strip():
            raise ValueError(f"Set a non-empty model ID in {model_field}")

        if self.ai_provider == "cloudflare":
            account_id = self.cloudflare_account_id or ""
            if not re.fullmatch(r"[0-9a-fA-F]{32}", account_id):
                raise ValueError("cloudflare_account_id must be a 32-character hexadecimal ID")
        return self

    @property
    def active_api_key(self) -> str:
        key_name = {
            "gemini": "gemini_api_key",
            "groq": "groq_api_key",
            "cerebras": "cerebras_api_key",
            "cohere": "cohere_api_key",
            "cloudflare": "cloudflare_api_token",
            "nvidia": "nvidia_api_key",
            "openrouter": "openrouter_api_key",
        }[self.ai_provider]
        secret = getattr(self, key_name)
        return secret.get_secret_value() if secret else ""

    @property
    def active_model(self) -> str:
        model_name = f"{self.ai_provider}_model"
        return getattr(self, model_name).strip()
