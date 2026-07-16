"""Document loading + chunking.

Sources supported:
  * the built-in sample corpus,
  * a local folder of .txt / .md files,
  * the email-attachment backup folder the existing Gmail extractor writes to
    (media/emails_backup) — this is what links the "email fetching" island to RAG.
"""
import os
import glob


def chunk_text(text, source, chunk_chars=600, overlap=80):
    """Greedy character-window chunker with overlap. Keeps a `source` + index."""
    text = " ".join(text.split())
    if len(text) <= chunk_chars:
        return [{"text": text, "source": source, "chunk": 0}]
    chunks, start, idx = [], 0, 0
    while start < len(text):
        end = min(start + chunk_chars, len(text))
        chunks.append({"text": text[start:end], "source": source, "chunk": idx})
        idx += 1
        if end == len(text):
            break
        start = end - overlap
    return chunks


def docs_to_chunks(docs, chunk_chars=600, overlap=80):
    out = []
    for d in docs:
        out.extend(chunk_text(d["text"], d.get("source", "unknown"), chunk_chars, overlap))
    return out


def load_sample():
    from .sample_corpus import SAMPLE_DOCS
    return list(SAMPLE_DOCS)


def _read_pdf(path):
    """Extract text from all pages of a PDF. Returns "" on any failure (never raises).

    Lazy-imports pypdf (falls back to PyPDF2) so the dependency is only needed
    when PDFs are actually present.
    """
    try:
        try:
            from pypdf import PdfReader
        except ImportError:
            from PyPDF2 import PdfReader
        reader = PdfReader(path)
        parts = []
        for page in reader.pages:
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                continue
        return "\n".join(parts)
    except Exception:
        return ""


def load_folder(path):
    """Read every .txt / .md / .pdf file in a folder into docs."""
    docs = []
    for fp in glob.glob(os.path.join(path, "**", "*"), recursive=True):
        if not os.path.isfile(fp):
            continue
        ext = os.path.splitext(fp)[1].lower()
        if ext not in {".txt", ".md", ".pdf"}:
            continue
        # Skip instructional READMEs so they don't pollute the corpus.
        if os.path.splitext(os.path.basename(fp))[0].lower() == "readme":
            continue
        try:
            if ext == ".pdf":
                txt = _read_pdf(fp).strip()
            else:
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    txt = f.read().strip()
            if txt:
                docs.append({"text": txt, "source": os.path.basename(fp)})
        except Exception:
            continue
    return docs


def load_email_backup(media_root=None):
    """Read the attachments saved by the Gmail extractor (projects/extract.py)."""
    if media_root is None:
        media_root = os.path.join(os.getcwd(), "media")
    folder = os.path.join(media_root, "emails_backup")
    if not os.path.isdir(folder):
        return []
    return load_folder(folder)
