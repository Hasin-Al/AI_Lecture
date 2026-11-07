"""A small HTTP/JSON example for the first API lecture."""

from __future__ import annotations

import argparse
from typing import Any

import httpx


def send_echo_request(
    method: str = "POST",
    *,
    message: str = "Hello from my first API request",
    transport: httpx.BaseTransport | None = None,
) -> tuple[int, dict[str, Any]]:
    """Call httpbin's GET or POST echo endpoint with a ten-second timeout."""
    normalized_method = method.upper()
    if normalized_method not in {"GET", "POST"}:
        raise ValueError("method must be GET or POST")

    url = (
        "https://httpbin.org/post"
        if normalized_method == "POST"
        else "https://httpbin.org/get"
    )

    with httpx.Client(transport=transport, timeout=10.0) as client:
        if normalized_method == "POST":
            response = client.post(url, json={"message": message})
        else:
            response = client.get(url)

    response.raise_for_status()
    return response.status_code, response.json()


def main() -> None:
    parser = argparse.ArgumentParser(description="Try a public HTTP echo endpoint.")
    parser.add_argument("method", nargs="?", choices=("GET", "POST"), default="POST")
    args = parser.parse_args()

    status, body = send_echo_request(args.method)
    print("Status:", status)
    print("JSON:", body)


if __name__ == "__main__":
    main()


