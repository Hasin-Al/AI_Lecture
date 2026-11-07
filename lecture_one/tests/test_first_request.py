import httpx

from first_request import send_echo_request


def test_post_sends_json_and_returns_echo_response():
    observed = {}

    def handler(request: httpx.Request) -> httpx.Response:
        observed["method"] = request.method
        observed["timeout"] = request.extensions.get("timeout")
        observed["body"] = request.read().decode()
        return httpx.Response(200, json={"json": {"message": "Hello from class"}})

    transport = httpx.MockTransport(handler)
    status, data = send_echo_request(
        "POST", transport=transport, message="Hello from class"
    )

    assert status == 200
    assert data["json"]["message"] == "Hello from class"
    assert observed["method"] == "POST"
    assert '"message":"Hello from class"' in observed["body"]
    assert observed["timeout"]["read"] == 10.0


def test_get_sends_no_request_body():
    observed = {}

    def handler(request: httpx.Request) -> httpx.Response:
        observed["method"] = request.method
        observed["body"] = request.read()
        observed["timeout"] = request.extensions.get("timeout")
        return httpx.Response(200, json={"args": {}})

    status, data = send_echo_request("GET", transport=httpx.MockTransport(handler))

    assert status == 200
    assert data["args"] == {}
    assert observed == {
        "method": "GET",
        "body": b"",
        "timeout": {"connect": 10.0, "read": 10.0, "write": 10.0, "pool": 10.0},
    }
