import os
import sys
import json
import time
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag_engine import RAGEngine

# Ensure standard output can handle utf-8
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

app = FastAPI(title="Sigma Web Development RAG Assistant")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load engine globally
engine = RAGEngine()

class QueryRequest(BaseModel):
    query: str
    model: Optional[str] = "gemini"  # "gemini" or "ollama"
    top_k: Optional[int] = 5

@app.get("/api/status")
def get_status():
    ollama_info = engine.check_ollama_status()
    gemini_info = engine.check_gemini_status()
    return {
        "status": "ready",
        "chunks_indexed": len(engine.df) if engine.df is not None else 0,
        "ollama": ollama_info,
        "gemini": gemini_info
    }

@app.get("/api/topics")
def get_course_topics():
    """Returns unique video titles from the indexed course."""
    if engine.df is None:
        return {"videos": []}
    
    unique_videos = engine.df.drop_duplicates(subset=["number", "title"])[["number", "title"]].to_dict(orient="records")
    try:
        unique_videos.sort(key=lambda x: int(x["number"]))
    except Exception:
        pass
    return {"videos": unique_videos}

@app.post("/api/chat")
def chat_endpoint(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    try:
        chunks = engine.retrieve(req.query, top_k=req.top_k)
        prompt = engine.build_prompt(req.query, chunks)
        answer = engine.generate_answer(prompt, model_type=req.model)

        return {
            "answer": answer,
            "chunks": chunks,
            "model": req.model,
            "query": req.query
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/stream")
def chat_stream_endpoint(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    def stream_generator():
        try:
            # 1. Retrieve chunks first
            chunks = engine.retrieve(req.query, top_k=req.top_k)
            # Send retrieved sources as the first SSE event
            yield f"data: {json.dumps({'type': 'sources', 'chunks': chunks})}\n\n"
            time.sleep(0.02)

            # 2. Build prompt
            prompt = engine.build_prompt(req.query, chunks)

            # 3. Stream generated tokens
            for chunk_token in engine.generate_stream(prompt, model_type=req.model):
                yield f"data: {json.dumps({'type': 'token', 'token': chunk_token})}\n\n"

            # 4. Completion event
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

# Mount static folder
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    print("\n========================================================")
    print("Starting Sigma Web Dev RAG AI Interface on http://localhost:8000")
    print("========================================================\n")
    uvicorn.run(app, host="127.0.0.1", port=8000)

