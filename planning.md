# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |
| 6 | | | |
| 7 | | | |
| 8 | | | |
| 9 | | | |
| 10 | | | |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->
I use **semantic chunking** (the `Semantic_llama_index` algorithm). Instead of cutting at a fixed
size, it splits where the embedding similarity between adjacent sentences drops — i.e. at natural
topic boundaries. The algorithm: (1) split each document into sentences; (2) embed each sentence
together with one neighbouring sentence on each side (`buffer_size = 1`) for context; (3) measure the
cosine distance between consecutive sentence-windows; (4) start a new chunk wherever that distance
exceeds the **95th percentile** (`breakpoint_percentile_threshold = 95`) of all distances in the document.

Embeddings for boundary detection use the same model as retrieval, `all-MiniLM-L6-v2`.

**Implementation note:** AutoRAG's built-in `Semantic_llama_index` chunker deadlocks on this machine
(its LlamaIndex `HuggingFaceEmbedding` backend hangs at 0% CPU on macOS + torch), so the identical
algorithm is implemented in `semantic_chunk.py` using `sentence-transformers` directly. Parsing still
uses AutoRAG (pdfminer).

**Chunk size:**

No fixed chunk size — boundaries are decided semantically, so chunks vary in length. I do enforce a
**hard cap of 256 tokens** per chunk (splitting any longer semantic segment on sentence boundaries),
because the embedding model `all-MiniLM-L6-v2` truncates anything past 256 tokens. Without this cap,
the tail of a long chunk would be silently dropped from its embedding and become unretrievable.
Measured result: mean ≈ 185 tokens, max 258, with all but one chunk within the 256-token window.

**Overlap:**

No overlap between final chunks. The `buffer_size = 1` window is only used to give each sentence
context *while detecting boundaries* — it does not duplicate text across the stored chunks. Overlap is
less important here than with fixed-size chunking because boundaries fall at topic shifts, so a single
idea is unlikely to be split across two chunks in the first place.

**Reasoning:**

I wanted boundaries decided by meaning rather than an arbitrary token count. Fixed-size token chunking
routinely severs a claim from its supporting evidence mid-sentence; semantic chunking keeps a coherent
idea together in one chunk. This matters for my corpus of dense academic papers on autonomous-vehicle
trust and HMI design, where the answer to a question is often a multi-sentence argument. Empirically it
also improved retrieval: top-result cosine distance on my trust test question dropped from 0.203 (token
chunking, 512/50) to 0.156 (semantic), i.e. tighter, more on-topic matches.

**Final chunk count:** 686 chunks across the 9 PDFs.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
