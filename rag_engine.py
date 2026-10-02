import os
import sys
import joblib
import numpy as np
import requests
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

def format_timestamp(seconds: float) -> str:
    """Converts seconds into MM:SS or HH:MM:SS format."""
    total_seconds = int(max(0, seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


class RAGEngine:
    def __init__(self, joblib_path: str = "models/embeddings.joblib", ollama_url: str = "http://localhost:11434"):
        self.joblib_path = joblib_path
        self.ollama_url = ollama_url
        self.df = None
        self.embedding_matrix = None
        self.gemini_client = None
        self._init_gemini()
        self.load_index()

    def _init_gemini(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize Gemini client: {e}")
                self.gemini_client = None

    def load_index(self):
        if not os.path.exists(self.joblib_path):
            raise FileNotFoundError(f"Embedding file not found at: {self.joblib_path}")
        print(f"Loading embeddings from {self.joblib_path}...")
        self.df = joblib.load(self.joblib_path)
        self.embedding_matrix = np.vstack(self.df["embedding"].values)
        print(f"Loaded {len(self.df)} chunks into memory.")

    def check_ollama_status(self) -> dict:
        try:
            r = requests.get(f"{self.ollama_url}/api/tags", timeout=3)
            if r.status_code == 200:
                data = r.json()
                models = [m.get("name") for m in data.get("models", [])]
                return {
                    "online": True,
                    "models": models,
                    "has_bge_m3": any("bge-m3" in m for m in models),
                    "has_llama3_2": any("llama3.2" in m for m in models)
                }
        except Exception as e:
            return {"online": False, "error": str(e)}
        return {"online": False}

    def check_gemini_status(self) -> dict:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {"available": False, "reason": "GEMINI_API_KEY not found in .env"}
        if self.gemini_client is None:
            self._init_gemini()
        return {"available": self.gemini_client is not None, "model": "gemini-3.8-flash"}

    def get_query_embedding(self, query_text: str) -> list[float]:
        try:
            r = requests.post(
                f"{self.ollama_url}/api/embed",
                json={"model": "bge-m3", "input": [query_text]},
                timeout=60
            )
            r.raise_for_status()
            data = r.json()
            return data["embeddings"][0]
        except Exception as e:
            raise RuntimeError(f"Error connecting to Ollama for embedding generation: {e}")

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        query_embedding = self.get_query_embedding(query)
        similarities = cosine_similarity(
            self.embedding_matrix,
            [query_embedding]
        ).flatten()

        top_indices = similarities.argsort()[::-1][:top_k]
        top_df = self.df.iloc[top_indices]

        results = []
        for idx_pos, (orig_idx, row) in enumerate(top_df.iterrows()):
            score = float(similarities[top_indices[idx_pos]])
            start_sec = float(row.get("start", 0))
            end_sec = float(row.get("end", 0))

            results.append({
                "chunk_id": int(row.get("chunk_id", orig_idx)),
                "number": str(row.get("number", "")).strip(),
                "title": str(row.get("title", "")).strip(),
                "start": start_sec,
                "end": end_sec,
                "start_time": format_timestamp(start_sec),
                "end_time": format_timestamp(end_sec),
                "timestamp_range": f"{format_timestamp(start_sec)} - {format_timestamp(end_sec)}",
                "text": str(row.get("text", "")).strip(),
                "score": round(score, 4),
                "match_pct": f"{max(0, int(score * 100))}%"
            })

        return results

    def build_prompt(self, query: str, chunks: list[dict]) -> str:
        chunks_context = []
        for c in chunks:
            chunks_context.append({
                "video_number": c["number"],
                "video_title": c["title"],
                "timestamp": c["timestamp_range"],
                "start_seconds": c["start"],
                "end_seconds": c["end"],
                "transcript": c["text"]
            })

        prompt = f"""You are the official AI Teaching Assistant for the Sigma Web Development Course.

Below is verified subtitle content retrieved directly from the course video lectures:

=== RETRIEVED COURSE CHUNKS ===
{chunks_context}
================================

User Question:
{query}

Instructions:
1. Answer the student's question accurately, concisely, and helpfully using the course content above.
2. Clearly identify:
   - The relevant Tutorial Number(s) (e.g. Tutorial #13)
   - The Video Title
   - The exact Timestamp range (e.g. 02:15 - 04:30)
3. Explain the concept or answer briefly so the student understands what is covered.
4. Guide the student specifically on where to watch this in the course.
5. If the retrieved chunks do not contain relevant information, state politely that this specific topic is not found in the indexed course videos.
6. Keep your tone encouraging, professional, and friendly, like a supportive instructor.
7. Format your response cleanly using Markdown (use bolding, bullet points, and code blocks where helpful).
8. Never refer to "retrieved JSON", "embeddings", or "chunks". Speak directly about the course lectures and timestamps.
"""
        return prompt

    def generate_answer(self, prompt: str, model_type: str = "gemini") -> str:
        if model_type == "gemini":
            if self.gemini_client is None:
                self._init_gemini()
            if self.gemini_client is None:
                raise RuntimeError("Gemini API key is not configured or client failed to initialize.")
            
            try:
                response = self.gemini_client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt
                )
                if response.text:
                    return response.text
            except Exception as e1:
                try:
                    interaction = self.gemini_client.interactions.create(
                        model="gemini-3.8-flash",
                        input=prompt
                    )
                    return interaction.output_text
                except Exception as e2:
                    raise RuntimeError(f"Gemini API error (generate_content: {e1} | interactions: {e2})")

        elif model_type == "ollama":
            try:
                r = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=300
                )
                r.raise_for_status()
                data = r.json()
                return data.get("response", "")
            except Exception as e:
                raise RuntimeError(f"Ollama generation error: {e}")
        else:
            raise ValueError(f"Unknown model_type: {model_type}")

    def generate_stream(self, prompt: str, model_type: str = "gemini"):
        """Yields chunks of text for real-time streaming."""
        if model_type == "ollama":
            r = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": prompt,
                    "stream": True
                },
                stream=True,
                timeout=300
            )
            r.raise_for_status()
            import json
            for line in r.iter_lines():
                if line:
                    chunk = json.loads(line.decode("utf-8"))
                    text = chunk.get("response", "")
                    if text:
                        yield text
                    if chunk.get("done", False):
                        break
        elif model_type == "gemini":
            full_text = self.generate_answer(prompt, model_type="gemini")
            import time
            words = full_text.split(" ")
            for i, word in enumerate(words):
                yield word + (" " if i < len(words) - 1 else "")
                time.sleep(0.015)

