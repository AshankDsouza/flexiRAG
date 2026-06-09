"""Semantic chunking for flexiRAG.

AutoRAG's `Semantic_llama_index` method deadlocks on this machine: its
LlamaIndex `HuggingFaceEmbedding` backend spawns a fork-bomb of worker
processes that hang at 0% CPU during model construction (macOS + torch).

This module reproduces the *exact* SemanticSplitterNodeParser algorithm using
the plain `sentence-transformers` model that the retrieval stage already uses
reliably:

    1. split each document into sentences
    2. build a buffered window around each sentence (buffer_size neighbours)
    3. embed each windowed sentence with all-MiniLM-L6-v2
    4. distance[i] = 1 - cosine(emb[i], emb[i+1])
    5. cut wherever distance exceeds the 95th-percentile threshold
    6. (safeguard) further split any chunk that exceeds the model's 256-token
       window, so nothing is silently truncated at embedding time

Output matches AutoRAG's chunk parquet schema so `RAG.py index` works unchanged.
"""

import os
import re
import uuid

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

ROOT = os.path.dirname(os.path.abspath(__file__))
PARSED = os.path.join(ROOT, "project", "parse", "parsed_result.parquet")
CHUNK_DIR = os.path.join(ROOT, "project", "chunk")
EMBED_MODEL = "all-MiniLM-L6-v2"

BUFFER_SIZE = 1
BREAKPOINT_PERCENTILE = 95
MAX_TOKENS = 256  # MiniLM's hard window
PREFIX_TOKENS = 30  # worst-case "file_name: ...\n contents: " prefix + CLS/SEP
BODY_CAP = MAX_TOKENS - PREFIX_TOKENS

_SENT_RE = re.compile(r"(?<=[.!?])\s+")


def split_sentences(text: str):
    sents = [s.strip() for s in _SENT_RE.split(text) if s.strip()]
    return sents


def windowed(sentences, buffer):
    """Combine each sentence with `buffer` neighbours on each side (context)."""
    out = []
    for i in range(len(sentences)):
        lo = max(0, i - buffer)
        hi = min(len(sentences), i + buffer + 1)
        out.append(" ".join(sentences[lo:hi]))
    return out


def semantic_breakpoints(sentences, model):
    """Return indices after which a new chunk should start."""
    if len(sentences) < 2:
        return []
    windows = windowed(sentences, BUFFER_SIZE)
    emb = model.encode(windows, normalize_embeddings=True)
    # distance between consecutive windows (normalized -> cosine = dot product)
    sims = np.sum(emb[:-1] * emb[1:], axis=1)
    distances = 1.0 - sims
    threshold = np.percentile(distances, BREAKPOINT_PERCENTILE)
    return [i for i, d in enumerate(distances) if d > threshold]


def group_by_breakpoints(sentences, breakpoints):
    chunks, start = [], 0
    for bp in breakpoints:
        chunks.append(" ".join(sentences[start : bp + 1]))
        start = bp + 1
    if start < len(sentences):
        chunks.append(" ".join(sentences[start:]))
    return chunks


def _ntok(text, tokenizer):
    return len(tokenizer.encode(text, add_special_tokens=False))


def _split_long_sentence(sentence, tokenizer):
    """Hard-split a single over-long sentence by token windows."""
    ids = tokenizer.encode(sentence, add_special_tokens=False)
    return [
        tokenizer.decode(ids[i : i + BODY_CAP]) for i in range(0, len(ids), BODY_CAP)
    ]


def enforce_token_cap(sentences_of_chunk, tokenizer):
    """Pack sentences into pieces of <= BODY_CAP tokens, hard-splitting any
    individual sentence that alone exceeds the cap. Guarantees every piece fits
    MiniLM's window once the filename prefix is added."""
    units = []
    for s in sentences_of_chunk:
        if _ntok(s, tokenizer) > BODY_CAP:
            units.extend(_split_long_sentence(s, tokenizer))
        else:
            units.append(s)

    out, cur = [], []
    for u in units:
        trial = " ".join(cur + [u])
        if cur and _ntok(trial, tokenizer) > BODY_CAP:
            out.append(" ".join(cur))
            cur = [u]
        else:
            cur.append(u)
    if cur:
        out.append(" ".join(cur))
    return out


def main():
    if not os.path.exists(PARSED):
        raise SystemExit("No parsed data. Run `python RAG.py ingest` first.")
    print(f"Loading {EMBED_MODEL} ...", flush=True)
    model = SentenceTransformer(EMBED_MODEL)
    tokenizer = model.tokenizer

    parsed = pd.read_parquet(PARSED)
    rows = []
    for _, doc in parsed.iterrows():
        text, path = doc["texts"], doc["path"]
        fname = os.path.basename(path)
        sentences = split_sentences(text)
        if not sentences:
            continue
        bps = semantic_breakpoints(sentences, model)
        # map chunks back to their sentence lists for the token-cap pass
        raw_chunks, start = [], 0
        bounds = bps + [len(sentences) - 1]
        for bp in bounds:
            seg = sentences[start : bp + 1]
            if seg:
                raw_chunks.append(seg)
            start = bp + 1
        for seg in raw_chunks:
            for piece in enforce_token_cap(seg, tokenizer):
                rows.append(
                    {
                        "doc_id": str(uuid.uuid4()),
                        # mirror AutoRAG add_file_name: en
                        "contents": f"file_name: {fname}\n contents: {piece}",
                        "path": path,
                        "start_end_idx": None,
                        "metadata": {"path": path},
                    }
                )
        print(f"  {fname:55s} {len(sentences):>4} sents -> "
              f"{sum(1 for r in rows if r['path'] == path):>3} chunks", flush=True)

    os.makedirs(CHUNK_DIR, exist_ok=True)
    out = os.path.join(CHUNK_DIR, "0.parquet")
    pd.DataFrame(rows).to_parquet(out, index=False)
    print(f"\nWrote {len(rows)} semantic chunks -> {out}", flush=True)


if __name__ == "__main__":
    main()
