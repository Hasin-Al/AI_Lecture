import pytest
from pydantic import ValidationError

from settings import Settings


def test_selected_gemini_provider_requires_and_keeps_its_key_private():
    settings = Settings(
        ai_provider="gemini",
        gemini_api_key="class-key",
        gemini_model="gemini-3.8-flash",
        _env_file=None,
    )

    assert settings.ai_provider == "gemini"
    assert settings.active_api_key == "class-key"
    assert settings.active_model == "gemini-3.8-flash"


def test_selected_provider_without_its_key_fails_before_startup(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ValidationError, match="groq_api_key"):
        Settings(ai_provider="groq", _env_file=None)


def test_cloudflare_requires_account_id_and_api_token(monkeypatch):
    monkeypatch.delenv("CLOUDFLARE_ACCOUNT_ID", raising=False)
    with pytest.raises(ValidationError, match="cloudflare_account_id"):
        Settings(
            ai_provider="cloudflare",
            cloudflare_api_token="class-token",
            _env_file=None,
        )


def test_unknown_provider_is_rejected():
    with pytest.raises(ValidationError, match="ai_provider"):
        Settings(
            ai_provider="made-up-provider",
            gemini_api_key="class-key",
            _env_file=None,
        )


def test_validation_error_does_not_echo_any_configured_secret(monkeypatch):
    monkeypatch.delenv("CLOUDFLARE_ACCOUNT_ID", raising=False)

    with pytest.raises(ValidationError) as error:
        Settings(
            ai_provider="cloudflare",
            cloudflare_api_token="dummy-cloudflare-token",
            gemini_api_key="dummy-gemini-key",
            _env_file=None,
        )

    assert "dummy-cloudflare-token" not in str(error.value)
    assert "dummy-gemini-key" not in str(error.value)


def test_selected_model_must_not_be_blank():
    with pytest.raises(ValidationError, match="gemini_model"):
        Settings(
            ai_provider="gemini",
            gemini_api_key="class-key",
            gemini_model="  ",
            _env_file=None,
        )


def test_api_key_rejects_header_line_breaks():
    with pytest.raises(ValidationError, match="groq_api_key"):
        Settings(
            ai_provider="groq",
            groq_api_key="token\r\nX-Injected: yes",
            _env_file=None,
        )


def test_cloudflare_account_id_must_be_32_hex_characters():
    with pytest.raises(ValidationError, match="cloudflare_account_id"):
        Settings(
            ai_provider="cloudflare",
            cloudflare_api_token="class-token",
            cloudflare_account_id="not-an-account-id",
            _env_file=None,
        )
