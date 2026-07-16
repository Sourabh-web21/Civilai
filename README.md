# CivilAI — Construction Project Management + RAG Assistant

A Django REST backend and React frontend for managing construction projects, tasks, and teams — with **CivilAI**, a built-in Retrieval-Augmented Generation (RAG) chat assistant that answers questions grounded in your project documents.

- **Backend:** Django 5.2 + Django REST Framework, SimpleJWT auth
- **RAG engine:** cluster-routed retrieval with a semantic cluster cache, pluggable embedders and LLMs (`rag_engine/`)
- **Frontend:** React 18 + Vite + Tailwind CSS, Recharts, Spline
- **Database:** SQLite by default (swappable via Django settings)

---

## Features

### Project management
- Projects, tasks, and a dashboard summary with progress metrics
- User management with roles, JWT login, password change / forgot / reset
- Admin profile management
- Email extractor for pulling structured data out of emails (`projects/extract.py`)
- Notifications app

### CivilAI — RAG chat assistant
- Ask natural-language questions; answers are **grounded only in your documents** with source citations and confidence scores
- **Cluster-routed retrieval** — a K-means coarse quantizer (FAISS-IVF style) scores only the nearest centroid buckets instead of the whole corpus
- **Semantic cluster cache** — near-duplicate questions hit a per-cluster cache (cosine similarity) and skip retrieval + the LLM entirely, with LRU/LFU eviction
- **Greeting & off-topic gating** — greetings get a canned reply; off-topic questions (below a relevance gate) are politely refused
- **Pluggable embedders:** `TfidfEmbedder` (default, no torch required) or `SentenceTransformerEmbedder` (production)
- **Pluggable LLMs:** `stub` (offline), `groq`, `grok`, `ollama` — auto-selected from environment
- **Document ingestion:** `.txt`, `.md`, and `.pdf` files dropped into `rag_docs/`

> See `RAG_PROGRESS.md` for the full RAG design notes and current status.

---

## Tech stack

| Layer       | Tools |
|-------------|-------|
| Backend     | Django 5.2, Django REST Framework, SimpleJWT |
| RAG         | scikit-learn, FAISS, sentence-transformers, LangChain, pypdf, NumPy |
| Frontend    | React 18, Vite 5, Tailwind CSS, React Router 6, Recharts, framer-motion, Spline |
| Auth        | JWT (`djangorestframework-simplejwt`) |
| Database    | SQLite (default) |

---

## Project structure

```
construction_ai/
├── manage.py
├── construction_ai/           # Django project (settings, urls, wsgi/asgi)
├── users/                     # Auth, user CRUD, profile, password flows
├── projects/                  # Projects, tasks, dashboard, email extractor
├── notification/              # Notifications
├── ollama_api/                # CivilAI chat API (generate + reload endpoints)
├── db/                        # Shared models, permissions, views
├── utils/                     # Response helpers, custom exception handler
├── rag_engine/               # The RAG pipeline (standalone package)
│   ├── pipeline.py            # RagPipeline.build(docs).answer(query)
│   ├── clustering.py          # ClusteredIndex — routed retrieval
│   ├── cache.py               # SemanticClusterCache
│   ├── embeddings.py          # TF-IDF / SentenceTransformer embedders
│   ├── llm.py                 # stub / groq / grok / ollama backends
│   ├── ingest.py              # chunking + .txt/.md/.pdf loaders
│   ├── service.py             # process singleton + ask() with gating
│   ├── config.py              # RagConfig (env-overridable knobs)
│   └── demo.py                # python -m rag_engine.demo
├── rag_docs/                  # Drop project PDFs / txt / md here for the assistant
├── requirements.txt
├── run_queries.py
├── RAG_PROGRESS.md            # RAG design + status notes
└── frontend/                  # React app
    └── src/
        ├── pages/             # Dashboard, Projects, ProjectDetail, Tasks, Users, Profile, Chat, Login
        ├── components/        # Layout, Modal, StatCard, ProgressRing, SplineHero, ui
        ├── context/           # AuthContext
        └── api/client.js      # Axios client
```

---

## Getting started

### Prerequisites
- Python 3.10+
- Node.js 18+
- (Optional) An LLM backend — a Groq/Grok API key or a local [Ollama](https://ollama.com) install. Without one, the offline `stub` LLM and TF-IDF embedder are used, so the assistant still runs end to end.

### 1. Backend setup

```bash
# from the project root
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser   # optional, for the Django admin
python manage.py runserver         # → http://127.0.0.1:8000
```

Create a `.env` in the project root for secrets (Django `SECRET_KEY`, and any LLM keys such as `GROQ_API_KEY`). RAG behavior is configurable via environment variables — e.g. `RAG_MIN_SCORE` (relevance gate, default `0.05`).

Email sending and IMAP fetching share the same environment-only mailbox credentials:

```env
EMAIL_HOST_USER=your-address@gmail.com
EMAIL_HOST_PASSWORD=your-google-app-password
```

Copy `.env.example` for the optional IMAP safety limits. Manual extraction is
limited to the newest 50 messages by default, has a 60-second mailbox cooldown,
and is throttled to six API requests per hour per user/IP. Newly downloaded
attachments automatically invalidate the RAG index so they are included on the
next chat question.

AiConnect synchronizes automatically every two minutes while its page is open
and always returns the five most recent inbox messages for the activity list.
For always-on synchronization when no browser is open, run the dedicated worker
as a separate process alongside Django:

```powershell
.\venv\Scripts\python.exe manage.py sync_email
```

Use `manage.py sync_email --once` for a single diagnostic check.

AiConnect and RAG are intentionally separate features. AiConnect synchronizes
mailbox activity, handles reviewed compose/reply/forward SMTP actions, detects
meeting invitations, and saves attachments. RAG only reads supported saved
attachments (plus local `rag_docs`) to answer document-grounded questions.

### 2. Add documents for the assistant

Drop `.pdf`, `.txt`, or `.md` files into `rag_docs/`. Then either restart the server or call the reload endpoint:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat/reload
```

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev                     # → http://localhost:5173
```

Set the API base URL in `frontend/.env` (e.g. `VITE_API_URL=http://127.0.0.1:8000`).

### 4. Try the RAG engine standalone

```bash
python -m rag_engine.demo       # prints cluster layout, routed-vs-full speedup, cache stats, eval
python run_queries.py           # run a batch of queries
```

---

## API overview

Base URL: `http://127.0.0.1:8000`

| Endpoint                           | Method   | Purpose                              |
|------------------------------------|----------|--------------------------------------|
| `/api/v1/user/login`               | POST     | JWT login                            |
| `/api/v1/user/list`                | GET/POST | List / create users                 |
| `/api/v1/user/change-password`     | POST     | Change password                      |
| `/api/v1/user/forgot-password`     | POST     | Request a password reset             |
| `/api/v1/user/reset-password`      | POST     | Complete a password reset            |
| `/api/v1/user/profile`             | GET      | Admin profile                        |
| `/api/v1/project/list`             | GET/POST | List / create projects               |
| `/api/v1/project/tasks/list`       | GET/POST | List / create tasks                  |
| `/api/v1/project/dashboard`        | GET      | Dashboard summary metrics            |
| `/api/v1/project/extract`          | POST     | Email extractor                      |
| `/api/v1/project/local-meeting/start` | POST  | Start a local/offline meeting session |
| `/api/v1/project/local-meeting/{id}/segments` | POST | Append live transcript segments |
| `/api/v1/project/local-meeting/{id}/stop` | POST | Stop and generate local MOM |
| `/api/v1/chat/generate`            | POST     | Ask CivilAI a question               |
| `/api/v1/chat/reload`              | POST     | Reload documents from `rag_docs/`    |

**Chat response shape** — the backend wraps results as:

```json
{ "status": "...", "status_code": 200, "message": "...", "results": { "answer": "...", "sources": [ ] } }
```

---

## How the RAG pipeline works

```
query ─► embed ─► route to nearest cluster(s) ─► semantic cache lookup (this cluster only)
                                                      │ hit  ─► return cached answer (no LLM)
                                                      │ miss ─► cluster-routed retrieval ─► LLM ─► cache.put
```

Because retrieval only scans the query's nearest clusters (not the full corpus) and near-duplicate questions are served from the cache, repeated and similar queries are answered without a retrieval or LLM round-trip.

---

## Notes

- The offline path (TF-IDF embedder + `stub` LLM) requires no API keys or GPU and is fully verified end to end — useful for development and CI.
- Don't commit real `.env` files or `db.sqlite3` with sensitive data.
- To use a production embedder or a real LLM, install the relevant extras and set the corresponding environment variables; the engine auto-selects available backends.

### Desktop migration status

Desktop runtime paths are available behind an opt-in environment flag:

```env
CIVILAI_DESKTOP=1
```

When enabled, mutable application data is stored outside the installation
directory:

- Windows: `%LOCALAPPDATA%/CivilAI`
- macOS: `~/Library/Application Support/CivilAI`
- Linux: `~/.local/share/CivilAI`

Current redirected data includes SQLite, media uploads, logs, model cache, and
exports. Normal web development remains unchanged when `CIVILAI_DESKTOP` is not
set.
