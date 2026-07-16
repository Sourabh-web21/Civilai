"""RAG evaluation harness.

Two modes:
  * heuristic (default, offline) — for each question we know which source SHOULD
    be retrieved and which keywords a faithful answer should contain. We measure
    retrieval hit-rate and answer keyword-recall. No keys needed.
  * llm-judge (optional) — if a real LLM backend is configured (Groq/Grok/Ollama),
    an LLM scores each answer's faithfulness to the retrieved context 1-5.

This is the "check proper RAG functioning" pipeline.
"""
import json
import re

# (question, expected source substring, expected keywords)
EVAL_SET = [
    ("What is the forest clearance status for NH-30?", "forest_clearance",
     ["forest", "clearance", "hectares"]),
    ("What is the total project cost in the NH-458 DPR?", "dpr",
     ["320", "crore", "cost"]),
    ("When is Milestone-II due and what does it require?", "milestone",
     ["milestone", "35", "cost"]),
    ("Why was an extension of time granted on NH-30?", "eot",
     ["eot", "56", "delay"]),
    ("How much land has been acquired for the Coastal Road?", "land_acquisition",
     ["92", "percent", "land"]),
    ("What did the road safety audit recommend?", "safety",
     ["signage", "barriers", "audit"]),
    ("What drainage works are planned for section 2?", "drainage",
     ["culvert", "drains", "storm"]),
    ("What is the daily toll revenue on the NH-458 bypass?", "toll",
     ["toll", "revenue", "lakh"]),
]


def _kw_recall(answer, keywords):
    a = answer.lower()
    hit = sum(1 for k in keywords if k.lower() in a)
    return hit / len(keywords) if keywords else 0.0


def evaluate(pipeline, eval_set=EVAL_SET, llm_judge=False, verbose=True):
    rows, ret_hits, kw_scores, judge_scores = [], 0, [], []

    for q, expect_src, keywords in eval_set:
        res = pipeline.answer(q, use_cache=False)
        srcs = [s["source"] for s in res["sources"]]
        retrieved = any(expect_src in s for s in srcs)
        ret_hits += int(retrieved)
        kw = _kw_recall(res["answer"], keywords)
        kw_scores.append(kw)

        row = {
            "question": q,
            "retrieved_expected": retrieved,
            "top_sources": srcs,
            "keyword_recall": round(kw, 2),
            "answer": res["answer"][:200],
        }

        if llm_judge and pipeline.llm.name != "stub":
            row["faithfulness"] = _judge(pipeline, q, res)
            judge_scores.append(row["faithfulness"])

        rows.append(row)
        if verbose:
            mark = "OK " if retrieved else "MISS"
            print(f"  [{mark}] kw={kw:.2f}  {q}")

    n = len(eval_set)
    summary = {
        "n_questions": n,
        "retrieval_hit_rate": round(ret_hits / n, 3),
        "avg_keyword_recall": round(sum(kw_scores) / n, 3),
    }
    if judge_scores:
        summary["avg_faithfulness_1to5"] = round(sum(judge_scores) / len(judge_scores), 2)
    return {"summary": summary, "rows": rows}


def _judge(pipeline, question, res):
    ctx = "\n".join(s["source"] for s in res["sources"])
    prompt = (
        "Rate, from 1 to 5, how well the ANSWER is supported by the retrieved "
        "SOURCES for the QUESTION. Reply with only the integer.\n\n"
        f"QUESTION: {question}\nSOURCES: {ctx}\nANSWER: {res['answer']}\n\nScore:"
    )
    try:
        out = pipeline.llm.generate(prompt, system="You are a strict grader.")
        m = re.search(r"[1-5]", out)
        return int(m.group()) if m else None
    except Exception:
        return None


if __name__ == "__main__":
    from .pipeline import RagPipeline
    from .ingest import load_sample

    pipe = RagPipeline().build(load_sample())
    report = evaluate(pipe, verbose=True)
    print(json.dumps(report["summary"], indent=2))
