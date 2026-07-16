"""Singleton RAG service with greeting + relevance gating.

Builds the pipeline ONCE per process (thread-safe, lazily) and exposes a single
`ask(query)` entrypoint used by the Django view. Keeps the engine answering out
of the box (falls back to the sample corpus when no docs are present).
"""
import os
import threading

from .config import RagConfig
from .pipeline import RagPipeline
from . import ingest

_PIPE = None
_LOCK = threading.Lock()


def _docs_dir():
    """Folder users drop project PDFs / .txt / .md into. Overridable via env."""
    override = os.getenv("RAG_DOCS_DIR")
    if override:
        return override
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "rag_docs")


def _load_docs():
    """Load docs from the docs dir + email-attachment backup.

    Falls back to the built-in sample corpus if nothing else is available so the
    engine always works out of the box.
    """
    docs = []
    d = _docs_dir()
    if os.path.isdir(d):
        docs.extend(ingest.load_folder(d))
    docs.extend(ingest.load_email_backup())
    if not docs:
        docs = ingest.load_sample()
    return docs


def get_pipeline():
    """Double-checked-locking singleton — builds the pipeline once per process."""
    global _PIPE
    if _PIPE is None:
        with _LOCK:
            if _PIPE is None:
                _PIPE = RagPipeline(RagConfig()).build(_load_docs())
    return _PIPE


def reset():
    """Drop the cached pipeline so newly added docs/PDFs are reloaded next call."""
    global _PIPE
    with _LOCK:
        _PIPE = None


_GREETINGS = {
    "hi", "hii", "hiii", "hello", "helo", "hey", "heya", "yo",
    "good morning", "good evening", "good afternoon", "good night",
    "how are you", "how r u", "who are you", "what can you do",
    "what's up", "whats up", "sup", "thanks", "thank you", "thankyou",
    "bye", "goodbye", "ok", "okay",
}

GREETING_REPLY = (
    "Hi! I'm CivilAI, your assistant for road and highway construction "
    "documentation. I read your project documents (DPRs, clearance letters, "
    "progress reports, land records, and email attachments) and answer questions "
    "grounded in them.\n\n"
    "Try asking things like:\n"
    " - What is the forest clearance status?\n"
    " - Give me the NH DPR details.\n"
    " - What are the upcoming project milestones?\n"
    " - Tell me about the drainage works.\n"
    " - What is the land acquisition status?"
)


def _is_greeting(q):
    """True for short greeting / smalltalk messages."""
    s = (q or "").strip().lower().rstrip("!.?")
    if not s:
        return False
    if s in _GREETINGS:
        return True
    # Short messages that start with a greeting (e.g. "hi there", "hello!!")
    if len(s.split()) <= 4:
        for g in _GREETINGS:
            if s == g or s.startswith(g + " "):
                return True
    return False


def ask(query):
    """Main entrypoint. Returns a dict the view can serialize directly."""
    if not query or not str(query).strip():
        return {
            "answer": "Please ask me a question about your construction project documents.",
            "sources": [],
            "cache_hit": False,
        }

    query = str(query).strip()

    if _is_greeting(query):
        return {
            "answer": GREETING_REPLY,
            "sources": [],
            "cache_hit": False,
            "greeting": True,
        }

    try:
        result = get_pipeline().answer(query)
    except Exception as e:
        return {
            "answer": "Sorry, something went wrong while searching the documents.",
            "sources": [],
            "error": str(e),
        }

    # Relevance gate — default threshold is intentionally low because the default
    # TF-IDF embedder produces low cosine scores; this only filters truly
    # off-topic junk, not legitimate questions.
    min_score = float(os.getenv("RAG_MIN_SCORE", "0.05"))
    sources = result.get("sources") or []
    max_score = max((s.get("score", 0) for s in sources), default=0)
    if not sources or max_score < min_score:
        return {
            "answer": (
                "I can only answer questions about the construction project "
                "documents I have access to. Please ask about forest clearance, "
                "DPRs, milestones, land acquisition, drainage, safety, tolls, etc."
            ),
            "sources": [],
            "cache_hit": False,
            "off_topic": True,
        }

    return result
