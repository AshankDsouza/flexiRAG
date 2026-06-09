#!/usr/bin/env bash
#
# setup.sh — build flexiRAG from scratch.
#
# Runs every step needed to go from a fresh checkout to a working RAG pipeline:
#   1. verify Python 3.11 is available  (AutoRAG's native deps don't build on 3.12+)
#   2. create the .venv virtual environment
#   3. install all dependencies
#   4. create .env from the template (for the Groq API key)
#   5. ingest  — parse PDFs (AutoRAG/pdfminer) + semantic chunking
#   6. index   — embed chunks into ChromaDB with all-MiniLM-L6-v2
#   7. verify  — run a test query (only if a real Groq key is set)
#
# Usage:  bash setup.sh
#
set -euo pipefail

# Always run from the project root (the directory this script lives in).
cd "$(dirname "$0")"

PYTHON=python3.11

echo "==> [1/7] Checking for $PYTHON ..."
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "ERROR: $PYTHON not found." >&2
  echo "AutoRAG requires Python 3.10-3.11 (its Rust deps don't build on 3.12+/3.14)." >&2
  echo "Install it with:  brew install python@3.11" >&2
  exit 1
fi
echo "    found: $($PYTHON --version)"

echo "==> [2/7] Creating virtual environment (.venv) ..."
if [ ! -d .venv ]; then
  "$PYTHON" -m venv .venv
  echo "    created .venv"
else
  echo "    .venv already exists — reusing it"
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> [3/7] Installing dependencies (this can take a few minutes) ..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> [4/7] Setting up .env ..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "    created .env from template — add your Groq API key (GROQ_API_KEY=...)"
  echo "    get a free key at https://console.groq.com"
else
  echo "    .env already exists — leaving it untouched"
fi

echo "==> [5/7] Ingesting documents (parse + semantic chunk) ..."
# AutoRAG refuses to overwrite an existing project dir, so start clean.
rm -rf project
python RAG.py ingest

echo "==> [6/7] Building the vector index (ChromaDB) ..."
rm -rf chroma_db
python RAG.py index

echo "==> [7/7] Verifying with a test query ..."
if [ -f .env ] && grep -q '^GROQ_API_KEY=' .env && ! grep -q 'your_key_here' .env; then
  python RAG.py ask "What factors influence trust in autonomous vehicles?"
else
  echo "    SKIPPED — no Groq API key set in .env."
  echo "    Add your key to .env, then query with:"
  echo "      source .venv/bin/activate && python RAG.py ask \"your question\""
fi

echo ""
echo "==> Setup complete."
