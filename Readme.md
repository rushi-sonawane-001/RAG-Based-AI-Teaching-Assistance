# RAG Based AI Teaching Assistant

An AI-powered **Retrieval-Augmented Generation (RAG)** system designed to help students find relevant content from the **Sigma Web Development Course**.

The system processes course videos, converts their audio into text using **Whisper**, creates semantic embeddings using **BGE-M3 with Ollama**, retrieves the most relevant course chunks using **cosine similarity**, and uses the **Gemini API** to generate a contextual answer with the relevant video title and timestamp.

---

## 🚀 Features

- 🎥 Video-to-audio processing
- 🎙️ Automatic speech-to-text using OpenAI Whisper
- 📝 Subtitle/chunk generation with timestamps
- 🧹 JSON preprocessing and chunk cleaning
- 🔗 Merging multiple subtitle chunks
- 🧠 BGE-M3 embeddings using Ollama
- 🔎 Semantic search using cosine similarity
- 📚 Top-K relevant course chunk retrieval
- 🤖 Gemini API for contextual answer generation
- ⏱️ Provides relevant video timestamps
- 🎯 Course-specific question answering
- 🔐 Environment-variable based API key configuration

---

## 🏗️ System Architecture

```text
                    ┌─────────────────────┐
                    │   Course Videos     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Video to Audio    │
                    │   video_to_mp3.py   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       Whisper       │
                    │   Speech-to-Text    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Subtitle JSON     │
                    │  mp3_to_jsons.py    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Preprocessing     │
                    │ preprocess_jsons.py │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Chunk Merging    │
                    │  merge_chunks.py    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   BGE-M3 Embedding  │
                    │       Ollama        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Embedding Storage  │
                    │   embeddings.joblib │
                    └──────────┬──────────┘
                               │
                               │
             ┌─────────────────▼─────────────────┐
             │          User Question           │
             └─────────────────┬─────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Query Embedding   │
                    │       BGE-M3        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Cosine Similarity  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Top-K Retrieval    │
                    │   Relevant Chunks   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Prompt + Context  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     Gemini API      │
                    │  Response Generation│
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Final Answer      │
                    │ Video + Timestamp   │
                    └─────────────────────┘

# How to use this RAG AI Teaching Assistance on your Data

## Step-1: Collect your videos
Move all your video files to the videos folder

## Step-2: Convert to mp3
Convert all the video files to mp3 by running video_to_mp3

## Step-3: Convert mp3 to json
Convert all the mp3 files to json by running mp3_to_json

## Step-4: Convert the jsons files to Vectors
Use the file preprocess_jsons to convert the json file to a dataframe with Embeddings and save it as a joblib pickel

## Step-5: Prompt Generation and feeding to LLM
Read the joblib file and load it into the memory. then create a relevant prompt as per the user query and feed it to the LLM