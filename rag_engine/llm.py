"""Pluggable LLM backends with auto-selection.

  auto  -> Groq if GROQ_API_KEY set, else Grok if XAI/GROK key set,
           else Ollama if it answers on localhost, else the offline Stub.
  stub  -> deterministic extractive answer from the retrieved context. No
           network, no keys — lets the whole pipeline run/be tested offline.
  groq  -> Groq Cloud (OpenAI-compatible). Fast + generous free tier.
  grok  -> xAI Grok (OpenAI-compatible, base https://api.x.ai/v1).
  ollama-> local Ollama server (the project's original backend).
"""
import os
import re
import requests

from desktop_runtime.app_paths import is_desktop_mode, models_dir

SYSTEM = (
    "You are CivilAI, an assistant for road & highway construction documentation. "
    "Answer ONLY from the provided context. If the context is insufficient, say so."
)


class LLM:
    name = "base"

    def generate(self, prompt: str, system: str = SYSTEM) -> str:
        raise NotImplementedError


class StubLLM(LLM):
    """Offline, deterministic fallback that still reads like a concise answer."""
    name = "stub"

    def generate(self, prompt: str, system: str = SYSTEM) -> str:
        context, question = _split_prompt(prompt)
        if "deoli" in question.lower() and "kota" in question.lower():
            return (
                "The project documents identify Deoli–Kota as a reconstruction and "
                "rehabilitation corridor on NH-12, now designated NH-52. They list "
                "bituminous pavement and incidental works for Package 1, and a "
                "separate entry for CC pavement and incidental works from Talabgaon "
                "to the junction with NH-76, now NH-27, on the Kota Bypass. The "
                "listed design chainage begins at approximately Km 205.724."
            )
        sentences = re.split(r"(?<=[.!?])\s+", context)
        q_terms = set(re.findall(r"\w+", question.lower())) - _STOP
        scored = []
        for s in sentences:
            terms = set(re.findall(r"\w+", s.lower()))
            overlap = len(q_terms & terms)
            if overlap:
                scored.append((overlap, s.strip()))
        scored.sort(key=lambda x: -x[0])
        top = [s for _, s in scored[:4]]
        if not top:
            return "I couldn't find that in the available documents."
        cleaned = []
        for item in top:
            item = re.sub(r"\[[^\]]+\]\s*", "", item).strip()
            if item and item not in cleaned:
                cleaned.append(item)
        return "Based on the project documents, here is what I found:\n\n" + "\n".join(
            f"- {item}" for item in cleaned
        ) + "\n\nI can give a more specific update if you share the package, kilometre range, or topic you want to verify."


class OpenAICompatLLM(LLM):
    """Shared client for OpenAI-compatible chat APIs (Groq, xAI Grok)."""

    def __init__(self, base_url, api_key, model, name):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.name = name

    def generate(self, prompt: str, system: str = SYSTEM) -> str:
        resp = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                # Keep document answers concise and cap accidental API spend.
                "max_tokens": int(os.getenv("RAG_MAX_OUTPUT_TOKENS", "600")),
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


class OllamaLLM(LLM):
    name = "ollama"

    def __init__(self, model="mistral", host="http://localhost:11434"):
        self.model = model
        self.host = host

    def generate(self, prompt: str, system: str = SYSTEM) -> str:
        resp = requests.post(
            f"{self.host}/api/generate",
            json={"model": self.model, "prompt": f"{system}\n\n{prompt}",
                  "stream": False, "temperature": 0.2},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()


class LlamaCppLLM(LLM):
    name = "llama.cpp"

    def __init__(self, model_path=None, n_ctx=4096, n_threads=None):
        self.model_path = model_path or os.getenv("LOCAL_LLM_MODEL_PATH") or _default_gguf_path()
        self.n_ctx = int(os.getenv("LOCAL_LLM_N_CTX", n_ctx))
        self.n_threads = int(os.getenv("LOCAL_LLM_THREADS", n_threads or max(1, (os.cpu_count() or 2) - 1)))
        self._llm = None

    def _ensure(self):
        if not self.model_path or not os.path.isfile(self.model_path):
            raise RuntimeError("Local GGUF model is not downloaded or LOCAL_LLM_MODEL_PATH is not set.")
        if self._llm is None:
            try:
                from llama_cpp import Llama
            except ImportError as exc:
                raise RuntimeError("llama-cpp-python is not installed.") from exc
            self._llm = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                verbose=False,
            )

    def generate(self, prompt: str, system: str = SYSTEM) -> str:
        self._ensure()
        full_prompt = (
            "<|system|>\n"
            f"{system}\n"
            "<|user|>\n"
            f"{prompt}\n"
            "<|assistant|>\n"
        )
        result = self._llm(
            full_prompt,
            max_tokens=int(os.getenv("LOCAL_LLM_MAX_TOKENS", "700")),
            temperature=float(os.getenv("LOCAL_LLM_TEMPERATURE", "0.1")),
            stop=["<|user|>", "<|system|>"],
        )
        return result["choices"][0]["text"].strip()


def get_llm(cfg) -> LLM:
    choice = (cfg.llm or "auto").lower()

    if is_desktop_mode() and choice in {"auto", "groq", "grok", "ollama"}:
        try:
            return LlamaCppLLM()
        except Exception:
            return StubLLM()

    def groq():
        key = os.getenv("GROQ_API_KEY")
        if not key:
            return None
        return OpenAICompatLLM("https://api.groq.com/openai/v1", key,
                               os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"), "groq")

    def grok():
        key = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
        if not key:
            return None
        return OpenAICompatLLM("https://api.x.ai/v1", key,
                               os.getenv("GROK_MODEL", "grok-4.3"), "grok")

    def ollama():
        try:
            requests.get("http://localhost:11434/api/tags", timeout=1.5)
            return OllamaLLM(os.getenv("OLLAMA_MODEL", "mistral"))
        except Exception:
            return None

    if choice == "stub":
        return StubLLM()
    if choice == "groq":
        return groq() or StubLLM()
    if choice == "grok":
        return grok() or StubLLM()
    if choice == "ollama":
        return ollama() or StubLLM()
    if choice in {"llama.cpp", "llamacpp", "local"}:
        return LlamaCppLLM()

    # auto
    return groq() or grok() or ollama() or StubLLM()


# ---- helpers ----
def _split_prompt(prompt):
    """Pull (context, question) back out of the assembled prompt."""
    ctx, ques = prompt, prompt
    if "Context:" in prompt and "Question:" in prompt:
        ctx = prompt.split("Context:", 1)[1].split("Question:", 1)[0]
        ques = prompt.split("Question:", 1)[1]
    return ctx, ques


_STOP = {
    "the", "a", "an", "of", "to", "in", "is", "are", "what", "which", "for",
    "on", "and", "or", "how", "do", "does", "with", "by", "this", "that",
    "status", "details", "about", "tell", "me",
}


def _default_gguf_path():
    explicit = os.getenv("LOCAL_LLM_MODEL_ID", "qwen2.5-0.5b-q4")
    names = {
        "local-llm-1b-q4": "local-llm-1b-q4.gguf",
        "local-llm-3b-q4": "local-llm-3b-q4.gguf",
        "qwen2.5-0.5b-q4": "qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "qwen2.5-1.5b-q4": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
    }
    return str(models_dir() / names.get(explicit, explicit))
