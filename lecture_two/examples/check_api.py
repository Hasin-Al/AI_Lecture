"""Optional live check through the actual FastAPI route (two Groq calls).

TestClient sends requests to the app in process, so no uvicorn server is needed.
This script is deliberately outside tests/: pytest stays offline.
"""
from fastapi.testclient import TestClient

from app.main import app


def main():
    ok = True
    with TestClient(app) as client:
        print("Health:", client.get("/health").json())
        for mode in ("prompt", "structured"):
            response = client.post("/extract", json={
                "text": "Mina Rahman mina@example.com", "mode": mode,
                "prompt_version": "v2", "repair": True,
            })
            print(mode, "HTTP", response.status_code, response.json())
            ok = ok and response.status_code == 200
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
