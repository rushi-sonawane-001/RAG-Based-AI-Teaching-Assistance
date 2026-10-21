
import hmac
import os

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

app = FastAPI()

OLLAMA_LOCAL_URL = os.getenv(
    "OLLAMA_LOCAL_URL",
    "http://127.0.0.1:11434",
).rstrip("/")

OLLAMA_PROXY_TOKEN = os.getenv("OLLAMA_PROXY_TOKEN", "")


@app.api_route("/api/{path:path}", methods=["GET", "POST"])
async def ollama_proxy(path: str, request: Request):
    if not OLLAMA_PROXY_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="Proxy token is not configured",
        )

    supplied = request.headers.get("authorization", "")
    expected = f"Bearer {OLLAMA_PROXY_TOKEN}"

    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Allow only the endpoints needed by the deployed app.
    ALLOWED = {
        ("GET",  "tags"),      # model list — used by /api/status
        ("POST", "embed"),     # bge-m3 query embeddings — required for ALL queries
        ("POST", "generate"),  # llama3.2 generation — Ollama LLM mode
    }
    if (request.method, path) not in ALLOWED:
        raise HTTPException(status_code=404, detail="Endpoint not allowed")

    try:
        body = await request.body()

        response = requests.request(
            method=request.method,
            url=f"{OLLAMA_LOCAL_URL}/api/{path}",
            data=body if body else None,
            headers={
                "Content-Type": request.headers.get(
                    "content-type", "application/json"
                )
            },
            timeout=120,  # increased for /api/generate which can be slow
        )

        return JSONResponse(
            status_code=response.status_code,
            content=response.json(),
        )

    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to local Ollama",
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail="Ollama returned an invalid response",
        ) from exc
