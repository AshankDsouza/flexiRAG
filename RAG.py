"""flexiRAG — end-to-end RAG pipeline.

Stages
------
1. ingest : parse PDFs (pdfminer) + chunk (llama_index Token) via AutoRAG.
2. index  : embed chunks with sentence-transformers (all-MiniLM-L6-v2) and
            store them in a local ChromaDB collection.
3. ask    : retrieve the top-k chunks for a question and generate a grounded
            answer with Groq (llama-3.3-70b-versatile).

Stack (all free / local except the Groq free tier):
    Embeddings   sentence-transformers  all-MiniLM-L6-v2   (local, 384-dim)
    Vector store ChromaDB                                  (local, persisted)
    LLM          Groq                   llama-3.3-70b-versatile

Usage
-----
    python RAG.py ingest          # parse + chunk documents/*.pdf
    python RAG.py index           # embed chunks -> ChromaDB
    python RAG.py ask "question"  # retrieve + generate
"""

import argparse
import glob
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS_GLOB = os.path.join(ROOT, "documents", "*.pdf")
PARSE_PROJECT_DIR = os.path.join(ROOT, "project", "parse")
CHUNK_PROJECT_DIR = os.path.join(ROOT, "project", "chunk")
PARSE_CONFIG = os.path.join(ROOT, "config", "parse_config.yaml")
CHUNK_CONFIG = os.path.join(ROOT, "config", "chunk_config.yaml")

CHROMA_DIR = os.path.join(ROOT, "chroma_db")
COLLECTION_NAME = "flexirag"
EMBED_MODEL = "all-MiniLM-L6-v2"
GROQ_MODEL = "llama-3.3-70b-versatile"
TOP_K = 5


# --------------------------------------------------------------------------- #
# Stage 1 — ingestion (parse + chunk) with AutoRAG
# --------------------------------------------------------------------------- #
def ingest() -> None:
    """Parse every PDF and chunk the parsed text."""
    from autorag.chunker import Chunker
    from autorag.parser import Parser

    os.makedirs(PARSE_PROJECT_DIR, exist_ok=True)
    print(f"Parsing PDFs from {DOCS_GLOB} ...")
    parser = Parser(data_path_glob=DOCS_GLOB, project_dir=PARSE_PROJECT_DIR)
    parser.start_parsing(PARSE_CONFIG)
    parsed = os.path.join(PARSE_PROJECT_DIR, "parsed_result.parquet")
    print(f"Parsed -> {parsed}")

    os.makedirs(CHUNK_PROJECT_DIR, exist_ok=True)
    print("Chunking parsed text ...")
    chunker = Chunker.from_parquet(parsed_data_path=parsed, project_dir=CHUNK_PROJECT_DIR)
    chunker.start_chunking(CHUNK_CONFIG)
    print(f"Chunked -> {CHUNK_PROJECT_DIR}")


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #
def _load_chunks():
    """Return the chunked DataFrame produced by the ingest stage."""
    import pandas as pd

    files = sorted(glob.glob(os.path.join(CHUNK_PROJECT_DIR, "*.parquet")))
    if not files:
        sys.exit("No chunks found. Run `python RAG.py ingest` first.")
    return pd.read_parquet(files[0])


_embedder = None


def _get_embedder():
    """Lazily load the sentence-transformers model (shared by index + ask)."""
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer

        _embedder = SentenceTransformer(EMBED_MODEL)
    return _embedder


def _get_collection(reset: bool = False):
    """Return the persistent ChromaDB collection (optionally recreated)."""
    import chromadb

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
    # cosine similarity suits normalized sentence-transformers embeddings
    return client.get_or_create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )


# --------------------------------------------------------------------------- #
# Stage 2 — embedding + ChromaDB indexing
# --------------------------------------------------------------------------- #
def index() -> None:
    """Embed every chunk with all-MiniLM-L6-v2 and store it in ChromaDB."""
    df = _load_chunks()
    collection = _get_collection(reset=True)
    embedder = _get_embedder()

    documents = df["contents"].tolist()
    ids = [str(d) for d in df["doc_id"].tolist()]
    metadatas = [{"source": os.path.basename(p)} for p in df["path"].tolist()]

    print(f"Embedding {len(documents)} chunks with {EMBED_MODEL} ...")
    embeddings = embedder.encode(
        documents, normalize_embeddings=True, show_progress_bar=True
    ).tolist()

    collection.add(
        ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas
    )
    print(f"Indexed {collection.count()} chunks -> {CHROMA_DIR} (collection '{COLLECTION_NAME}')")


# --------------------------------------------------------------------------- #
# Stage 3 — retrieval + grounded generation
# --------------------------------------------------------------------------- #
def retrieve(question: str, k: int = TOP_K):
    """Return the top-k most relevant chunks for a question."""
    collection = _get_collection()
    if collection.count() == 0:
        sys.exit("Index is empty. Run `python RAG.py index` first.")
    query_emb = _get_embedder().encode(
        [question], normalize_embeddings=True
    ).tolist()
    res = collection.query(query_embeddings=query_emb, n_results=k)
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    dists = res["distances"][0]
    return list(zip(docs, metas, dists))


SYSTEM_PROMPT = (
    "You are a research assistant answering questions about autonomous-vehicle "
    "human factors, trust, and HMI design. Answer ONLY using the numbered "
    "context passages provided. If the answer is not contained in the context, "
    "reply exactly: \"I don't have enough information in the provided documents "
    "to answer that.\" Do not use outside knowledge. Cite the source filename "
    "in square brackets, e.g. [HCI_Topic_Paper.pdf], after each claim it supports."
)


def generate(question: str, retrieved) -> str:
    """Generate a grounded answer with Groq from the retrieved context."""
    from dotenv import load_dotenv
    from groq import Groq

    load_dotenv(os.path.join(ROOT, ".env"))
    if not os.getenv("GROQ_API_KEY"):
        sys.exit("GROQ_API_KEY not set. Copy .env.example to .env and add your key.")

    context_blocks = []
    for i, (doc, meta, _dist) in enumerate(retrieved, 1):
        context_blocks.append(f"[{i}] (source: {meta['source']})\n{doc}")
    context = "\n\n".join(context_blocks)

    user_prompt = (
        f"Context passages:\n\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the context above, citing source filenames."
    )

    client = Groq()
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
    )
    return resp.choices[0].message.content


def ask(question: str, k: int = TOP_K) -> None:
    """Full query path: retrieve then generate, printing answer + sources."""
    retrieved = retrieve(question, k)
    answer = generate(question, retrieved)
    print(f"\nQ: {question}\n")
    print(answer)
    print("\n--- retrieved sources ---")
    for i, (_doc, meta, dist) in enumerate(retrieved, 1):
        print(f"  [{i}] {meta['source']}  (cosine distance {dist:.3f})")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(description="flexiRAG pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ingest", help="parse + chunk documents/*.pdf")
    sub.add_parser("index", help="embed chunks into ChromaDB")
    ask_p = sub.add_parser("ask", help="ask a question")
    ask_p.add_argument("question", help="the question to answer")
    ask_p.add_argument("-k", type=int, default=TOP_K, help="number of chunks to retrieve")

    args = parser.parse_args()
    if args.command == "ingest":
        ingest()
    elif args.command == "index":
        index()
    elif args.command == "ask":
        ask(args.question, args.k)


if __name__ == "__main__":
    main()
