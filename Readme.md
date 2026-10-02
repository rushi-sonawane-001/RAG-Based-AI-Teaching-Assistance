# Sigma Web Development Course — RAG AI Teaching Assistant

An AI-powered **Retrieval-Augmented Generation (RAG)** system that acts as a smart teaching assistant for the **Sigma Web Development Course**. Students can ask natural language questions and instantly get answers pointing to the exact **video lecture**, **topic**, and **timestamp** where the content is taught — powered by a modern ChatGPT & Gemini-style web interface.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [System Workflow](#system-workflow)
  - [Phase 1 — Offline Data Pipeline](#phase-1--offline-data-pipeline-run-once)
  - [Phase 2 — Online RAG Query Pipeline](#phase-2--online-rag-query-pipeline-runs-on-every-query)
- [How to Run](#how-to-run)
  - [Prerequisites](#prerequisites)
  - [Quick Start](#quick-start)
  - [Full Pipeline (Adding New Videos)](#full-pipeline-adding-new-videos)
- [Web Interface Guide](#web-interface-guide)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## Overview

This project processes course videos end-to-end:

1. Extracts audio from lecture videos
2. Transcribes and translates spoken Hindi into English using **OpenAI Whisper**
3. Generates dense semantic vector embeddings using **BGE-M3** via Ollama
4. On a student query — retrieves the top-K most relevant lecture chunks using **cosine similarity**
5. Feeds the retrieved chunks + question into a **Large Language Model** (Gemini or Llama 3.2) to generate a precise, timestamped, contextual answer

---

## Features

| Feature | Description |
|---|---|
| 🎥 Video-to-Audio | Batch converts `.mp4` lecture videos to `.mp3` using `ffmpeg` |
| 🎙️ Speech-to-Text | Transcribes + translates Hindi audio to English via Whisper `large-v2` |
| 📝 Timed Subtitles | Generates subtitle chunks with start/end timestamps per segment |
| 🔗 Chunk Merging | Groups 5 consecutive segments into semantically richer chunks |
| 🧠 BGE-M3 Embeddings | Creates 1024-dim dense embeddings via Ollama locally |
| 🔎 Cosine Similarity Search | Finds the top-K most relevant lecture chunks for any question |
| 🤖 Dual LLM Support | Supports Google Gemini (cloud) and Ollama Llama 3.2 (local) |
| ⏱️ Exact Timestamps | Returns precise video timestamps (e.g. `04:15 - 06:40`) |
| 💬 Chat UI | ChatGPT & Gemini inspired dark-mode web interface |
| 📚 Source Citations | Collapsible citation cards with match confidence % per retrieved chunk |
| 📡 SSE Streaming | Real-time token streaming for smooth response rendering |
| 🔐 Secure Config | API keys loaded from `.env` — never hardcoded |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Video Processing** | `ffmpeg` |
| **Speech Recognition** | OpenAI Whisper `large-v2` |
| **Embeddings** | BGE-M3 (via Ollama) |
| **Vector Store** | In-memory Pandas DataFrame + `joblib` serialization |
| **Similarity Search** | `scikit-learn` cosine similarity |
| **LLM (Cloud)** | Google Gemini `gemini-3.8-flash` |
| **LLM (Local)** | Ollama `llama3.2:3.2B` |
| **Backend API** | FastAPI + Uvicorn |
| **Frontend** | Vanilla HTML + CSS + JavaScript |
| **Markdown Rendering** | `marked.js` |
| **Syntax Highlighting** | `highlight.js` |
| **Streaming** | Server-Sent Events (SSE) |

---

## Project Structure

```
RAG based AI/
│
├── app.py                        # FastAPI backend server (entry point for UI)
├── rag_engine.py                 # Core RAG engine: retrieval + LLM generation
├── prompt.txt                    # Last generated prompt (debug reference)
├── response.txt                  # Last raw LLM response (debug reference)
├── .env                          # API keys (GEMINI_API_KEY)
├── requirements.txt              # Python dependencies
├── Readme.md                     # This file
│
├── src/                          # Offline data pipeline scripts
│   ├── video_to_mp3.py           # Step 1: Convert videos → mp3 audio
│   ├── mp3_to_jsons.py           # Step 2: Whisper transcription → JSON chunks
│   ├── merge_chunks.py           # Step 3: Merge 5 segments → 1 chunk
│   └── preprocess_jsons.py       # Step 4: Embed all chunks → embeddings.joblib
│
├── processing/
│   └── process_incoming.py       # Original CLI-based query handler (legacy)
│
├── static/                       # Frontend web assets
│   ├── index.html                # Main chat UI page
│   ├── style.css                 # Dark-mode ChatGPT/Gemini inspired styles
│   └── app.js                    # Frontend controller (SSE, markdown, history)
│
├── data/                         # Course data at various pipeline stages
│   ├── videos/                   # Raw course video files (.mp4)
│   ├── audios/                   # Extracted audio files (.mp3)
│   ├── jsons/                    # Raw Whisper transcription output (.json)
│   ├── newjsons/                 # Merged/cleaned chunk files (.json)
│   └── unused/                   # Miscellaneous archived files
│
├── models/
│   └── embeddings.joblib         # Serialized DataFrame with all BGE-M3 embeddings
│
├── output/                       # Debug output from previous runs
│   ├── output.json
│   ├── prompt.txt
│   └── response.txt
│
├── whisper/                      # Local Whisper source (for offline use)
└── myenv/                        # Python virtual environment
```

---

## System Workflow

### Phase 1 — Offline Data Pipeline (Run Once)

This phase converts raw course videos into a searchable vector database. Run this once when you add new videos.

```
┌──────────────────────────────────────────────────────────────────────┐
│                     OFFLINE DATA PIPELINE                            │
└──────────────────────────────────────────────────────────────────────┘

 data/videos/               data/audios/               data/jsons/
 ┌───────────┐   ffmpeg     ┌───────────┐  Whisper     ┌───────────┐
 │  .mp4     │ ──────────►  │  .mp3     │ ──────────►  │  .json    │
 │  videos   │              │  audio    │  large-v2    │  raw      │
 └───────────┘              └───────────┘  (translate)  │  chunks   │
                                                        └─────┬─────┘
                                                              │
                                                    merge 5 segments
                                                              │
                                                        ┌─────▼─────┐
                                                        │  .json    │
                                                        │  merged   │  data/newjsons/
                                                        │  chunks   │
                                                        └─────┬─────┘
                                                              │
                                                   BGE-M3 embeddings
                                                    (via Ollama API)
                                                              │
                                                        ┌─────▼─────┐
                                                        │embeddings │
                                                        │ .joblib   │  models/
                                                        └───────────┘
```

#### Step-by-step:

**Step 1 — Extract Audio** (`src/video_to_mp3.py`)
- Scans `data/videos/` for `.mp4` files
- Parses tutorial number and title from the filename
- Runs `ffmpeg` to strip audio → `data/audios/{number}_{title}.mp3`

**Step 2 — Transcribe Audio** (`src/mp3_to_jsons.py`)
- Loads Whisper `large-v2` model
- For each `.mp3` file: transcribes Hindi speech and translates to English
- Produces per-segment JSON with `number`, `title`, `start`, `end`, `text`
- Saves to `data/jsons/{audio}.json`

**Step 3 — Merge Chunks** (`src/merge_chunks.py`)
- Whisper segments are short (2–5 seconds). Too small for good semantic search.
- Groups every `n = 5` consecutive segments into one larger chunk
- Preserves the earliest `start` and latest `end` timestamp per group
- Saves to `data/newjsons/`

**Step 4 — Generate Embeddings** (`src/preprocess_jsons.py`)
- Reads all merged chunks from `data/newjsons/`
- Sends text in batches of 200 to Ollama's `bge-m3` embedding model
- Stores chunk metadata + 1024-dim embedding vector per chunk
- Builds a Pandas DataFrame and serializes it with `joblib.dump` → `models/embeddings.joblib`

---

### Phase 2 — Online RAG Query Pipeline (Runs on Every Query)

This phase handles real-time student questions through the web interface.

```
┌──────────────────────────────────────────────────────────────────────┐
│                    ONLINE QUERY PIPELINE                             │
└──────────────────────────────────────────────────────────────────────┘

   Student Question
         │
         ▼
  ┌─────────────┐
  │  Embed      │  BGE-M3 via Ollama
  │  Question   │  → 1024-dim vector
  └──────┬──────┘
         │
         ▼
  ┌─────────────────────┐
  │  Cosine Similarity  │  Compare against all 1844 chunk embeddings
  │  Search             │  from embeddings.joblib (in-memory)
  └──────┬──────────────┘
         │
         ▼
  ┌─────────────┐
  │  Top-K      │  Retrieve the 5 most semantically similar chunks
  │  Chunks     │  (each with: tutorial#, title, start, end, text)
  └──────┬──────┘
         │
         ▼
  ┌─────────────────────┐
  │  Prompt             │  Inject retrieved chunks + student question
  │  Construction       │  into a structured teaching assistant prompt
  └──────┬──────────────┘
         │
         ▼
  ┌─────────────┐
  │  LLM        │  Google Gemini (gemini-3.8-flash)
  │  Inference  │  OR Ollama (llama3.2:3.2B)
  └──────┬──────┘
         │
         ▼
  ┌─────────────────────────────────────┐
  │  Streaming Answer (SSE)             │
  │  • Tutorial number & title          │
  │  • Exact timestamp (e.g. 04:15)     │
  │  • Concept explanation              │
  │  • Navigation guidance              │
  └─────────────────────────────────────┘
```

---

## How to Run

### Prerequisites

Ensure the following are installed and available:

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10+ | With `myenv` virtual environment |
| ffmpeg | Any | Must be in system `PATH` |
| Ollama | Latest | Must have `bge-m3` and `llama3.2` pulled |
| Google Gemini API Key | — | Set in `.env` file |

**Install Ollama models (one-time):**
```bash
ollama pull bge-m3
ollama pull llama3.2
```

**Install Python dependencies:**
```bash
pip install -r requirements.txt
```

---

### Quick Start

> Use this when `models/embeddings.joblib` already exists (data pipeline already run).

```powershell
# 1. Navigate to the project directory
cd "c:\Users\Lenovo\Data Science\RAG based AI"

# 2. Activate the virtual environment
.\myenv\Scripts\activate

# 3. Run the web interface
python app.py

# 4. Open your browser at:
#    http://localhost:8000
```

> **Note:** Ollama runs automatically as a background service on Windows after first install. You do NOT need to run `ollama serve` manually unless it was stopped.

---

### Full Pipeline (Adding New Videos)

Run this sequence when you add new course videos:

```powershell
# Activate environment
.\myenv\Scripts\activate

# Step 1: Extract audio from videos
python src/video_to_mp3.py

# Step 2: Transcribe audio to subtitle JSON chunks (takes a long time)
python src/mp3_to_jsons.py

# Step 3: Merge short segments into semantic chunks
python src/merge_chunks.py

# Step 4: Embed all chunks and save vector store
python src/preprocess_jsons.py

# Step 5: Launch the web interface
python app.py
```

---

## Web Interface Guide

Once the server is running at `http://localhost:8000`:

### Sidebar
- **Course Lectures** — Lists all 20 indexed video tutorials. Click any lecture to instantly ask about it.
- **Recent Questions** — Your question history, saved locally in the browser. Persists between sessions.
- **System Status** — Green/Red indicator dots showing live status of Ollama and Gemini.

### Top Navigation Bar
- **Model Selector** — Toggle between:
  - `Gemini 3.8 Flash (Cloud)` — Faster, higher quality answers via Google API
  - `Ollama Llama 3.2 (Local)` — Fully offline, no API key required
- **Top-K Selector** — Choose how many lecture chunks to retrieve (3, 5, or 8). More = broader context.
- **Restart Chat** — Clear the current conversation.

### Chat Interface
- Type a question and press **Enter** or click the **Send** button.
- Responses stream in word-by-word (like Gemini / ChatGPT).
- Every response includes:
  - A **formatted markdown answer** with tutorial number, title, and timestamp.
  - A collapsible **"Retrieved Course Sources"** panel showing:
    - Tutorial number and title
    - Timestamp range (e.g. `04:15 - 06:40`)
    - Relevance match percentage (e.g. `🎯 94%`)
    - Verbatim excerpt from the lecture transcript

### Starter Prompts
Click any of the 4 suggestion cards on the welcome screen to get started instantly.

---

## API Reference

The backend exposes the following REST endpoints:

### `GET /api/status`
Returns the health status of all services.

**Response:**
```json
{
  "status": "ready",
  "chunks_indexed": 1844,
  "ollama": {
    "online": true,
    "models": ["bge-m3:latest", "llama3.2:latest"],
    "has_bge_m3": true,
    "has_llama3_2": true
  },
  "gemini": {
    "available": true,
    "model": "gemini-3.8-flash"
  }
}
```

---

### `GET /api/topics`
Returns all unique course video titles indexed in the vector store.

**Response:**
```json
{
  "videos": [
    { "number": "1", "title": "Installing VS Code & How Websites Work" },
    { "number": "2", "title": "Your First HTML Website" },
    ...
  ]
}
```

---

### `POST /api/chat`
Runs the full RAG pipeline and returns the complete answer.

**Request Body:**
```json
{
  "query": "Where is the CSS box model explained?",
  "model": "gemini",
  "top_k": 5
}
```

| Field | Type | Default | Options |
|---|---|---|---|
| `query` | string | required | Any question |
| `model` | string | `"gemini"` | `"gemini"` or `"ollama"` |
| `top_k` | integer | `5` | `1` to `10` |

**Response:**
```json
{
  "answer": "The CSS Box Model is taught in **Tutorial #18**...",
  "chunks": [...],
  "model": "gemini",
  "query": "Where is the CSS box model explained?"
}
```

---

### `POST /api/chat/stream`
Same as `/api/chat` but streams the response using **Server-Sent Events (SSE)**.

**Events emitted (in order):**
```
data: {"type": "sources", "chunks": [...]}   ← Retrieved lecture chunks

data: {"type": "token", "token": "The "}     ← Streamed answer tokens

data: {"type": "done"}                        ← Stream complete
```

---

## Configuration

### `.env` file

```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```

Get your free API key at: [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)

---

### Changing the Port

In [`app.py`](app.py), change the `port` argument on the last line:

```python
uvicorn.run(app, host="127.0.0.1", port=8080)  # Changed to 8080
```

---

### Changing the Number of Merged Segments

In [`src/merge_chunks.py`](src/merge_chunks.py), adjust `n`:

```python
n = 5  # Merge every 5 Whisper segments into 1 chunk
```

Larger `n` → broader context per chunk, but less precision in timestamps.

---

### Changing the Embedding Batch Size

In [`src/preprocess_jsons.py`](src/preprocess_jsons.py):

```python
BATCH_SIZE = 200  # Number of chunks sent to Ollama per API call
```

---

## Troubleshooting

| Problem | Cause | Solution |
|---|---|---|
| `Port 8000 already in use` | Old server still running | Run: `Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000 -State Listen).OwningProcess -Force` |
| `Error: listen tcp 127.0.0.1:11434` when running `ollama serve` | Ollama already running | No action needed — Ollama is already available |
| Embedding error on query | Ollama not running | Start Ollama from the system tray or run `ollama serve` in a new terminal |
| Gemini returns `503 UNAVAILABLE` | Temporary API overload | Wait and retry, or switch to Ollama mode in the UI |
| `embeddings.joblib not found` | Data pipeline not run | Execute Steps 1–4 of the Full Pipeline |
| Whisper transcription is slow | `large-v2` model is heavy | Use `medium` or `small` in `src/mp3_to_jsons.py` for faster (less accurate) output |
| `ModuleNotFoundError` | Virtual environment not activated | Run `.\myenv\Scripts\activate` first |

---

## Course Videos Indexed

| Tutorial # | Title |
|---|---|
| 1 | Installing VS Code & How Websites Work |
| 2 | Your First HTML Website |
| 3 | Basic Structure of an HTML Website |
| 4 | Heading, Paragraphs and Links |
| 5 | Image, Lists, and Tables in HTML |
| 6 | SEO and Core Web Vitals in HTML |
| 7 | Forms and Input Tags in HTML |
| 8 | Inline & Block Elements in HTML |
| 9 | Id & Classes in HTML |
| 10 | Video, Audio & Media in HTML |
| 11 | Semantic Tags in HTML |
| 12 | Exercise 1 — Pure HTML Media Player |
| 13 | Entities, Code Tag and more on HTML |
| 14 | Introduction to CSS |
| 15 | Inline, Internal & External CSS |
| 16 | Exercise 1 — Solution & Shoutouts |
| 17 | CSS Selectors MasterClass |
| 18 | CSS Box Model — Margin, Padding & Borders |
| 19 | CSS Fonts, Text & Color Properties |
| 20 | Exercise 2 — CSS Challenge |

---

*Built with ❤️ using RAG, BGE-M3, Whisper, FastAPI, and Google Gemini.*
Read the joblib file and load it into the memory. then create a relevant prompt as per the user query and feed it to the LLM