# RAG Backend — FastAPI + AI (Retrieval Augmented Generation)

A production-ready FastAPI backend demonstrating backend engineering best
practices while implementing a full Retrieval Augmented Generation (RAG)
pipeline: document ingestion, chunking, embeddings, similarity search, and
LLM-generated answers grounded in the retrieved context.

---

## 1. Project Overview

This service lets an authenticated user:

1. Sign up / log in (JWT authentication).
2. Upload text documents, which are automatically chunked and embedded.
3. Ask natural-language questions, which are answered using only the most
   relevant chunks from *that user's own* documents (retrieved via cosine
   similarity), passed as context to Groq's `llama3-8b-8192` model.

A server-rendered HTML/CSS/Vanilla-JS frontend (login, signup, dashboard)
is bundled alongside the JSON API.

---

## 2. Architecture

```
Browser (HTML/CSS/JS)
        │
        ▼
 FastAPI application (app/main.py)
        │
        ├── Middleware ── ExceptionLoggingMiddleware ──► error_logs (MongoDB)
        │
        ├── Routers
        │      ├── /auth        (signup / login)
        │      ├── /documents   (upload / list / delete)
        │      ├── /chat        (RAG pipeline)
        │      └── /  (UI pages)
        │
        ├── Services (business logic)
        │      ├── auth_service.py
        │      ├── document_service.py
        │      └── chat_service.py
        │
        ├── Utils
        │      ├── security.py     (bcrypt + JWT)
        │      ├── dependencies.py (current-user dependency)
        │      ├── chunking.py     (text splitting)
        │      └── embeddings.py   (SentenceTransformer singleton + cosine similarity)
        │
        └── MongoDB (via Motor)
               ├── users
               ├── documents
               ├── chunks
               └── error_logs
```

### RAG flow

```
Upload:  title + content → store document → chunk text → embed chunks → store chunks

Chat:    question → embed question → load user's chunks → cosine similarity
                  → top-K chunks → build context → call Groq → return
                    { answer, retrieved_context, similarity_scores }
```

The SentenceTransformer embedding model (`all-MiniLM-L6-v2`) is loaded
**exactly once**, at application startup, via a singleton wrapper
(`app/utils/embeddings.py::EmbeddingModel`) — it is never reloaded per-request.

---

## 3. Folder Structure

```
rag_backend/
├── app/
│   ├── main.py                     # App factory, lifespan, routers, middleware
│   ├── config.py                   # Pydantic settings (env-driven)
│   ├── database.py                 # Motor client, collections, index creation
│   │
│   ├── middleware/
│   │   └── exception_handler.py    # Global error-logging middleware
│   │
│   ├── routes/
│   │   ├── auth.py                 # POST /auth/signup, /auth/login
│   │   ├── document.py             # POST /documents/upload, GET/DELETE
│   │   ├── chat.py                 # POST /chat
│   │   └── ui.py                   # Jinja2 page routes
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── document_service.py
│   │   └── chat_service.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── document.py
│   │   └── chat.py
│   │
│   ├── utils/
│   │   ├── security.py             # bcrypt hashing + JWT encode/decode
│   │   ├── dependencies.py         # get_current_user / get_current_user_id
│   │   ├── chunking.py             # chunk_text()
│   │   └── embeddings.py           # embedding model singleton + cosine similarity
│   │
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/app.js
│   │
│   └── templates/
│       ├── login.html
│       ├── signup.html
│       └── dashboard.html
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── README.md
└── .gitignore
```

---

## 4. Installation (local, without Docker)

### 4.1 Clone & create a virtual environment

```bash
cd rag_backend
python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### 4.2 Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4.3 Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

- `JWT_SECRET_KEY` — any long random string
- `GROQ_API_KEY` — your Groq API key (see below)
- `MONGO_URI` — defaults to `mongodb://localhost:27017`

### 4.4 MongoDB

You need a running MongoDB instance. Options:

**A. Local install**
Install MongoDB Community Server for your OS, then start it:

```bash
mongod --dbpath /path/to/data/dir
```

**B. Docker (just the database)**

```bash
docker run -d --name rag_mongo -p 27017:27017 mongo:7
```

The application automatically creates all required indexes
(`users.email` unique, `documents.user_id`, `chunks.document_id`,
`chunks.user_id`, `error_logs.timestamp`) on startup.

### 4.5 Groq API key

1. Create a free account at [console.groq.com](https://console.groq.com).
2. Generate an API key.
3. Paste it into `.env` as `GROQ_API_KEY`.

The app uses the `llama3-8b-8192` model for answer generation.

### 4.6 Run the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit:

- UI: http://localhost:8000/
- API docs (Swagger): http://localhost:8000/docs
- Health check: http://localhost:8000/health

---

## 5. Running with Docker

This spins up both MongoDB and the API together.

```bash
cp .env.example .env   # then edit JWT_SECRET_KEY / GROQ_API_KEY
docker compose up --build
```

The API will be available at `http://localhost:8000`, and MongoDB data
persists in the `mongo_data` named volume between restarts.

To stop:

```bash
docker compose down
```

To also wipe the database volume:

```bash
docker compose down -v
```

---

## 6. API Endpoints

| Method | Path                | Auth required | Description                                  |
|--------|---------------------|:--------------:|-----------------------------------------------|
| POST   | `/auth/signup`      | No             | Create a new account, returns JWT             |
| POST   | `/auth/login`       | No             | Authenticate, returns JWT                     |
| POST   | `/documents/upload` | Yes            | Upload + chunk + embed a document             |
| GET    | `/documents`        | Yes            | List the current user's documents             |
| DELETE | `/documents/{id}`   | Yes            | Delete a document and its chunks              |
| POST   | `/chat`             | Yes            | Ask a question (RAG pipeline)                 |
| GET    | `/health`           | No             | Liveness probe                                |
| GET    | `/`, `/login`, `/signup`, `/dashboard` | No/Yes | Server-rendered UI pages       |

All authenticated endpoints expect:

```
Authorization: Bearer <access_token>
```

### Example — signup

```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Jane Doe","email":"jane@example.com","password":"supersecret1"}'
```

### Example — upload

```bash
curl -X POST http://localhost:8000/documents/upload \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"title":"Company Policy","content":"Employees are entitled to..."}'
```

### Example — chat

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"question":"How many vacation days do employees get?"}'
```

---

## 7. Screenshots

> _Add screenshots of the running UI here._

- `docs/screenshots/login.png`
- `docs/screenshots/dashboard-overview.png`
- `docs/screenshots/upload.png`
- `docs/screenshots/chat.png`

---

## 8. MongoDB Collections & Indexes

| Collection   | Purpose                                | Indexes                    |
|--------------|-----------------------------------------|-----------------------------|
| `users`      | Account credentials & profile           | `email` (unique)            |
| `documents`  | Raw uploaded documents                  | `user_id`                   |
| `chunks`     | Chunked text + embeddings per document  | `document_id`, `user_id`    |
| `error_logs` | Captured unhandled exceptions           | `timestamp`                 |

---

## 9. Future Improvements

- Swap the brute-force cosine similarity scan for a vector index
  (MongoDB Atlas Vector Search, FAISS, or Qdrant) for large-scale corpora.
- Add refresh tokens and token revocation / blacklisting.
- Add per-document re-indexing when content is edited.
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
| LLM            | Groq API (`llama3-8b-8192`)                  |
| Frontend       | HTML5, CSS3, Vanilla JS, Jinja2              |
| Deployment     | Docker, Docker Compose                       |
