"""End-to-end demo. Run from the project root:

    ./venv/Scripts/python.exe -m rag_engine.demo

Shows: cluster layout, cluster-routed vs full search timing, semantic-cache
hit vs miss timing, LRU/LFU eviction, and the eval report.
"""
import time
import numpy as np

from .config import RagConfig
from .pipeline import RagPipeline
from .ingest import load_sample
from .evaluate import evaluate


def hr(title):
    print("\n" + "=" * 64)
    print(f"  {title}")
    print("=" * 64)


def main():
    cfg = RagConfig()
    hr("1. BUILD  (embed -> KMeans cluster -> index)")
    docs = load_sample()
    pipe = RagPipeline(cfg).build(docs)
    info = pipe.info()
    print(f"  embedder        : {info['embedder']} (dim={info['embed_dim']})")
    print(f"  llm backend     : {info['llm']}")
    idx = info["index"]
    print(f"  chunks indexed  : {idx['n_vectors']}")
    print(f"  clusters        : {idx['n_clusters']}  sizes={idx['cluster_sizes']}")
    print(f"  cache policy    : {cfg.cache_policy.upper()} (cap={cfg.cache_capacity}, "
          f"thr={cfg.cache_threshold}, nprobe={cfg.nprobe})")

    hr("2. CLUSTER-ROUTED vs FULL search (avg over 200 runs)")
    q = "What is the forest clearance status for NH-30?"
    qvec = pipe.embedder.encode(q)
    N = 200
    t = time.perf_counter()
    for _ in range(N):
        pipe.index.search(qvec, cfg.top_k, cfg.nprobe)
    routed = (time.perf_counter() - t) / N * 1e6
    t = time.perf_counter()
    for _ in range(N):
        pipe.index.search_full(qvec, cfg.top_k)
    full = (time.perf_counter() - t) / N * 1e6
    _, probed, scanned = pipe.index.search(qvec, cfg.top_k, cfg.nprobe)
    print(f"  cluster-routed  : {routed:7.1f} µs   (scanned {scanned}/{idx['n_vectors']} "
          f"chunks, probed clusters {probed})")
    print(f"  full brute-force: {full:7.1f} µs   (scanned {idx['n_vectors']}/{idx['n_vectors']})")
    if routed > 0:
        print(f"  -> routing scans {100*scanned/idx['n_vectors']:.0f}% of corpus; "
              f"speedup x{full/routed:.2f}")

    hr("3. SEMANTIC CACHE  (miss = LLM call, hit = cluster-bucket lookup)")
    pipe.cache.clear()
    r1 = pipe.answer(q)                       # miss -> generates + caches
    r2 = pipe.answer("forest clearance status NH-30?")  # near-duplicate -> hit
    print(f"  Q1 (cold)       : {r1['timing_ms']['total']:7.2f} ms  hit={r1['cache_hit']}  "
          f"cluster={r1['cluster']}")
    print(f"  Q2 (similar)    : {r2['timing_ms']['total']:7.2f} ms  hit={r2['cache_hit']}  "
          f"sim={r2.get('cache_similarity')}")
    if r2["cache_hit"] and r2["timing_ms"]["total"] > 0:
        print(f"  -> cache hit speedup x{r1['timing_ms']['total']/max(r2['timing_ms']['total'],0.001):.1f}")
    print(f"  answer          : {r1['answer'][:140]}…")
    print(f"  sources         : {[s['source'] for s in r1['sources']]}")

    hr("4. CACHE EVICTION  (fill past capacity, watch LRU/LFU drop entries)")
    small = RagConfig(cache_capacity=5, cache_policy=cfg.cache_policy)
    p2 = RagPipeline(small).build(docs)
    questions = [
        "forest clearance hectares", "DPR total project cost", "milestone II cost",
        "EOT delay days", "land acquisition percent", "road safety barriers",
        "drainage culverts section 2", "toll revenue per day",
    ]
    for question in questions:
        p2.answer(question)
    cs = p2.cache.stats()
    print(f"  inserted        : {len(questions)} queries, capacity {small.cache_capacity}")
    print(f"  cache size      : {cs['size']}  evictions={cs['evictions']}  "
          f"policy={cs['policy'].upper()}")
    print(f"  bucket spread   : {cs['buckets']}")

    hr("5. EVAL  (retrieval hit-rate + answer keyword recall)")
    report = evaluate(pipe, verbose=True)
    s = report["summary"]
    print(f"\n  retrieval hit-rate   : {s['retrieval_hit_rate']*100:.0f}%")
    print(f"  avg keyword recall   : {s['avg_keyword_recall']*100:.0f}%")
    if "avg_faithfulness_1to5" in s:
        print(f"  avg faithfulness     : {s['avg_faithfulness_1to5']}/5 (LLM-judge)")

    print("\nDone. Switch to production with env vars:")
    print("  RAG_EMBEDDER=sentence-transformers  GROQ_API_KEY=...  (or RAG_LLM=ollama)")


if __name__ == "__main__":
    main()
