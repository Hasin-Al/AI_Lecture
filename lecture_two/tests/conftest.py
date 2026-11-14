import pytest
import httpx


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Unit tests must never spend API credits, even when a real .env exists."""
    def blocked(*args, **kwargs):
        raise AssertionError("Network access is forbidden in offline tests")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", blocked)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", blocked)


@pytest.fixture
def good():
    return {"full_name": "Mina Rahman", "email": "mina@example.com", "phone": None}
