# Document RAG Backend

This project is a FastAPI-based Retrieval-Augmented Generation (RAG) application that lets users sign up, upload documents, and ask questions about their own content. The app splits documents into chunks, creates embeddings, and uses those embeddings together with a Groq LLM to generate answers grounded in the uploaded documents.

## What this project does

- User authentication with JWT
- Document upload and storage in MongoDB
- Text chunking and embedding generation
- Semantic retrieval from the user’s documents
- Answer generation using a Groq model
- A simple web UI for login, signup, and dashboard usage

- ---

## Key Features

- **JWT Authentication:** Secure user signup, login, and token-based route protection.
- **Document Ingestion & Parsing:** Upload `.pdf` and `.txt` files directly via multipart form data (`pypdf` extraction).
- **Serverless Cloud Embeddings:** Offloads vector generation to the Hugging Face `InferenceClient` SDK (`sentence-transformers/all-MiniLM-L6-v2`), eliminating local PyTorch/SentenceTransformers memory usage.
- **Low-Memory Footprint:** Optimized to run strictly within 512 MB RAM environments (e.g., Render free tier).
- **Vector Search & Persistence:** Async document chunking, indexing, and vector storage backed by MongoDB Atlas (Motor driver).
- **Sub-Second LLM Generation:** Answers generated using Groq's high-speed inference engine (`llama-3.1-8b-instant`).
- **Interactive UI:** Built-in web dashboard for user registration, file uploads, and contextual chat.

---

## Architecture Flow

```text
  [ Client / Web UI ]
          │
          ▼
  ┌───────────────┐
  │ FastAPI App   │ ──(File Upload)──> [ pypdf Extract & Text Chunking ]
  └───────┬───────┘                                    │
          │                                            ▼
          ├────(HuggingFace SDK)────> [ HF Inference Cloud API ]
          │                                            │
          │ <───(Return 384-d Vectors)─────────────────┘
          │
          ├───(Save Chunks & Embeddings)──────────────> [ MongoDB Atlas ]
          │
          ├───(Vector Cosine Similarity)──────────────> [ Top-K Context Chunks ]
          │
          └────(Context + User Query)─> [ Groq LLaMA 3.1 ] ───> [ Grounded Response ]
```
---
## Prerequisites

Before running the project, make sure you have:

- Python 3.10+ (3.12 recommended)
- pip
- MongoDB running locally or Docker installed
- A Groq API key from https://console.groq.com
- A Hugging Face User Access Token (Read permission from huggingface.co/settings/tokens)

## Installation

1. Open the project folder:

```bash
cd rag_backend
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
# On Windows use: .venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. Create your environment file:

```bash
copy .env.example .env
# On Linux/macOS use: cp .env.example .env
```

Update the values in `.env` with your own settings, especially:

- `JWT_SECRET_KEY`
- `GROQ_API_KEY`
- `MONGO_URI` (if needed)

## Running the project locally

1. Start MongoDB.

If you are using Docker, you can run:

```bash
docker run -d --name rag_mongo -p 27017:27017 mongo:7
```

2. Start the FastAPI server:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

3. Open the app in your browser:

- UI: http://localhost:8000/
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Running with Docker Compose

You can also run the full app and MongoDB together:

```bash
docker compose up --build
```

To stop the containers:

```bash
docker compose down
```

## Important notes

- The first run may take a few minutes because the embedding model is downloaded.
- The app uses the `llama-3.1-8b-instant` Groq model, so a valid Groq API key is required.
- If you change the database connection settings, make sure they match your MongoDB instance.
- The backend automatically creates the required indexes on startup.

- Add rate limiting on `/chat` and `/documents/upload`.
- Add streaming responses for the chat endpoint (Server-Sent Events).
- Add pytest test suite with a mocked Mongo instance (mongomock / testcontainers).
- Add role-based access control for multi-tenant / admin scenarios.
- Add pagination to `/documents` and chat history persistence.

---

## 10. Tech Stack Summary

| Layer          | Technology                                  |
|----------------|----------------------------------------------|
| Backend        | Python 3.12, FastAPI, Uvicorn                |
| Auth           | JWT (python-jose), Passlib (bcrypt)          |
| Database       | MongoDB, Motor (async driver)                |
| Embeddings     | Sentence-Transformers (`all-MiniLM-L6-v2`)   |
| LLM            | Groq API (`llama-3.1-8b-instant`)                  |
| Frontend       | HTML5, CSS3, Vanilla JS, Jinja2              |
| Deployment     | Docker, Docker Compose                       |
|Embeddings      | Hugging Face Inference SDK (huggingface-hub, all-MiniLM-L6-v2) |  
