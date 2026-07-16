# RAG Pipeline — Progress & Context

> Cluster-routed RAG with an LRU/LFU **cluster-partitioned semantic cache**, wired
> into the Django backend and a React chat UI. This file is the single source of
> truth for what's done / what's left — read it instead of re-reading the whole tree.

Last updated: 2026-06-30

---

## TL;DR — status: ✅ COMPLETE & VERIFIED (offline TF-IDF + stub path)

End-to-end verified with the project venv:
- greeting → friendly intro
- on-topic question → grounded answer + source chips (scores 0.78–0.99)
- near-duplicate question → **cache hit** (cosine sim 1.0, skips retrieval + LLM)
- off-topic question (e.g. "who won the world cup") → politely refused (score 0.0 < gate)
- `python manage.py check` → 0 issues

---

## Architecture (the `rag_engine/` package — already complete, don't rewrite)

```
query ─► embed ─► route to nearest cluster(s) ─► semantic cache lookup (this cluster only)
                                                      │hit─► return cached answer (no LLM)
                                                      │miss─► cluster-routed retrieval ─► LLM ─► cache.put
```

| File | Role |
|------|------|
| `rag_engine/cache.py` | `SemanticClusterCache` — answers filed per cluster bucket; lookup is semantic (cosine ≥ threshold) and only scans the query's cluster. LRU/LFU eviction via a logical clock. |
| `rag_engine/clustering.py` | `ClusteredIndex` — K-means coarse quantizer (FAISS-IVF style). `route()` picks `nprobe` nearest centroids; `search()` scores only those buckets. `search_full()` = brute-force baseline. |
| `rag_engine/embeddings.py` | Pluggable embedders, both L2-normalized. `TfidfEmbedder` (default, no torch) and `SentenceTransformerEmbedder` (prod). |
| `rag_engine/llm.py` | Pluggable LLMs: `stub` (offline), `groq`, `grok`, `ollama`; auto-selected. `SYSTEM` prompt enforces "answer ONLY from context". |
| `rag_engine/ingest.py` | Chunking + loaders: `load_sample`, `load_folder` (.txt/.md/**.pdf**, skips README), `load_email_backup`. |
| `rag_engine/pipeline.py` | `RagPipeline.build(docs).answer(query)` — orchestrates everything, returns timings + cache stats. |
| `rag_engine/config.py` | `RagConfig` — all knobs, env-overridable. |
| `rag_engine/service.py` | **NEW** — process singleton + `ask(query)` with greeting + off-topic gating (see below). |
| `rag_engine/demo.py` | `python -m rag_engine.demo` — prints cluster layout, routed-vs-full speedup, cache speedup, eviction, eval. |

---

## What was added this session (the "finish" work)

1. **PDF support** — `ingest._read_pdf()` (lazy `pypdf`, falls back to `PyPDF2`, never raises); `load_folder` now indexes `.pdf` and skips `README*`.
2. **`rag_engine/service.py`** — thread-safe singleton:
   - `get_pipeline()` builds once from `rag_docs/` + email backup, falls back to sample corpus if empty.
   - `ask(query)`: greeting → canned reply; else run pipeline; **relevance gate** (`RAG_MIN_SCORE`, default 0.05) → off-topic refusal if best source score too low. Only greetings + grounded answers get through.
   - `reset()` → drop singleton so new PDFs reload.
3. **`ollama_api/views.py`** — rewritten. Old FAISS/CrossEncoder module-load (hardcoded Linux path) **removed**. `CivilAIQueryAPIView` (AllowAny) lazy-imports `service.ask`; new `RagReloadAPIView`.
4. **URLs** — `construction_ai/urls.py` enables `path('api/v1/chat/', include('ollama_api.urls'))`. Routes: `POST /api/v1/chat/generate`, `POST /api/v1/chat/reload`.
5. **`construction_ai/settings.py`** — added missing `MEDIA_URL` / `MEDIA_ROOT`.
6. **`rag_docs/`** — drop-zone folder (`README.md` + `.gitkeep`) for project PDFs/txt/md.
7. **Frontend** — `frontend/src/pages/Chat.jsx` (chat UI), route `/chat` in `App.jsx`, nav entry "CivilAI Chat" in `Layout.jsx`.
8. **requirements.txt** — added `pypdf`.

### API response shape (`POST /api/v1/chat/generate`)
Backend wraps as `{status, status_code, message, results}`. `results` =
```json
{ "answer": "...", "combined_context": "...", "sources": [{"source":"f.pdf","score":0.42}],
  "docs_used": [...], "cache_hit": false, "greeting": false, "off_topic": false }
```

---

## ⚙️ Where to configure things

| What | File | Key |
|------|------|-----|
| **LLM provider** | `.env` (project root) | `RAG_LLM=auto\|stub\|groq\|grok\|ollama` |
| **Groq API key** | `.env` | `GROQ_API_KEY=...` (+ optional `GROQ_MODEL`) |
| **xAI Grok key** | `.env` | `XAI_API_KEY=...`, `GROK_MODEL=grok-4.3` (CONFIGURED) |
| **Ollama** | `.env` | `RAG_LLM=ollama` (server on `localhost:11434`, `OLLAMA_MODEL=mistral`) |
| **Better embeddings** | `.env` | `RAG_EMBEDDER=sentence-transformers` (INSTALLED ✓ — all-MiniLM-L6-v2, 384-dim) |
| **Off-topic strictness** | `.env` | `RAG_MIN_SCORE=0.05` (raise to refuse more) |
| **Docs folder** | `.env` | `RAG_DOCS_DIR=` (default `rag_docs/`) |
| **Email send (SMTP)** | `.env` | `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` (Gmail app password) — consumed in `settings.py` |
| **Email *fetch* (IMAP)** | `.env` | `EMAIL_USER`, `EMAIL_PASS` — used by `projects/extract.py` (currently has a hardcoded default; move to `.env`) |

> No keys set → engine runs fully offline (TF-IDF + stub LLM). Add a key to upgrade answer quality with zero code changes.

### xAI Grok status (2026-06-30)
Key is set and the `grok-4.3` model name is valid, BUT the xAI team has **no credits** →
API returns `403 "Your newly created team doesn't have any credits or licenses yet"`.
**Action needed:** buy credits at https://console.x.ai/team → then Grok works automatically.
Until then, the pipeline **gracefully falls back to the offline stub** (extractive,
document-grounded) so the chat still answers from the PDFs — no error shown to the user.
`.env` parsing for `rag_engine` is handled by `config._load_dotenv_once()` (decouple does
not export to os.environ).

---

## How to run

```bash
# backend (from project root)
venv/Scripts/python.exe manage.py runserver
# engine smoke test
venv/Scripts/python.exe  -m rag_engine.demo
# frontend
cd frontend && npm install && npm run dev
```

Drop project PDFs into `rag_docs/`, then `POST /api/v1/chat/reload` (or restart) to re-index.

---

## Known follow-ups (optional, not blocking)
- `sentence-transformers` + `torch` ARE now installed in the venv (2026-06-30). Set
  `RAG_EMBEDDER=sentence-transformers` in `.env` for higher-quality semantic embeddings
  (downloads all-MiniLM-L6-v2 on first use). `faiss` is still not installed and not needed.
- `projects/extract.py` has a hardcoded Gmail address + app password default → move to `.env`.
- Cache is in-process (resets on restart). Persist to disk/Redis if cross-worker sharing is needed.
