# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

Human Machine Interfaces (HMI) which is a subset of HCI (Human Computer Interfaces) -- the study of user interfaces and particular related to trust and various aspect of how to design them in the context of autonomous vehicles. This is useful because HMI studies don't not always focus on autonmous vehicles until recently. 

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | *Trusting autonomous vehicles: An interdisciplinary approach* — Raats, Fors & Pink, Transportation Research Interdisciplinary Perspectives 7 (2020) 100201 | Peer-reviewed journal article | https://doi.org/10.1016/j.trip.2020.100201 · `documents/Trusting_autonomous_vehicles_An_interdisciplinary_.pdf` |
| 2 | *Human-Machine Interfaces and Vehicle Automation: A Review of the Literature and Recommendations for System Design, Feedback, and Alerts* — Mehrotra et al., UMass-Amherst / AAA Foundation for Traffic Safety (Nov 2022) | Research report | AAA Foundation for Traffic Safety · `documents/HMI-and-Automation-Design-Recommendations.pdf` |
| 3 | *"What's Happening" — A Human-centered Multimodal Interpreter Explaining the Actions of Autonomous Vehicles* — Luo et al., Monash University Malaysia (2025) | arXiv preprint | https://arxiv.org/abs/2501.05322 · `documents/2501.05322v2.pdf` |
| 4 | *Accessible Autonomous Vehicles: A Human-Computer Interaction Literature Review* — Mayas, Lengkong & Hirth, TU Ilmenau | ACM conference paper (systematic review) | https://doi.org/10.1145/3750069.3750162 · `documents/3750069.3750162.pdf` |
| 5 | *HMI design for autonomous vehicles* — Langlois (Renault), 13th IFAC Symposium on Analysis, Design & Evaluation of Human-Machine Systems, Kyoto (2016) | Conference paper (IFAC-PapersOnLine) | https://www.sciencedirect.com/science/article/pii/S2405896316322418 · `documents/1-s2.0-S2405896316322418-main.pdf` |
| 6 | *Evaluation of the human interaction with automated vehicles on highways* — Chand, Wang, Jashami & Hurwitz, Oregon State University (2024) | Peer-reviewed research article | `documents/e000078_Chand.pdf` |
| 7 | *Inclusive Design of Autonomous Vehicles: A Public Dialogue — Summary Report* — U.S. Access Board (July 2021) | Government public-dialogue report | U.S. Access Board · `documents/usab-av-forum-summary-report.pdf` |
| 8 | *NVIDIA Autonomous Vehicles Safety Report* — NVIDIA | Industry safety report / white paper | NVIDIA · `documents/auto-self-driving-safety-report.pdf` |
| 9 | *Human Computer Interaction (HMI) in autonomous vehicles for alerting driver during overtaking and lane changing* — Umachigi, Michigan Technological University (CS5760 Topic Paper) | Academic course paper | `documents/HCI_Topic_Paper.pdf` |
| 10 | *The influence of a color themed HMI on trust and take-over performance in automated vehicles* | Academic course paper | `documents/fpsyg-14-1128285 (4).pdf` |

---

## Chunking Strategy

Semantic chunking was used. Each sentenced is processed and compared to its neighboring sentence to check for an abrupt semantic shift. 

Can be reproduced with:
python RAG.py ingest.

No preprocessing was done; even the references were not deleted. 

**Chunk size:**
No fixed size. 
Hard limit of 256 tokens. all-MiniLM-L6-v2 has a 256 limit. 

**Overlap:**
Overlapping is not needed with semantic based chunking as overlap exists to prevent context loss and here with chunking done per topic there is nothing we are loosing as such. 

**Why these choices fit your documents:**
 Fixed-size token chunking cuts mid-argument; semantic chunking keeps the unit intact.

**Final chunk count:**
686 chunks.
---

## Embedding Model

     all-MiniLM-L6-v2 (via sentence-transformers)

     Reasons for the choice:
     - can run on personal laptop/machine on CPU
     - is fast --took 5 seconds to compute
     - doubles up as boundary detector for the semantic chunking



**Model used:**
text-embedding-3-large 
 or a strong open model like BGE-M3 (8192-token, multilingual) on GPU. 


**Production tradeoff reflection:**
Where it genuinely wins
Context length limits — biggest win. 8,191 tokens vs MiniLM's 256 (~32×). For your corpus this is the headline benefit: it removes the 256-token chunk cap entirely, so you could embed whole semantic sections without the truncation and bibliography-fragmentation problems in test.md. It also has a dimensions parameter (Matryoshka) so you can shrink the 3072-dim vector down to, say, 1024 or 256 to control storage/speed without re-embedding.

Accuracy on domain-specific text — real but not magic. It scores ~64% on the MTEB benchmark vs ~56% for MiniLM, and its 3072 dimensions capture more semantic nuance — better paraphrase matching, which is exactly what your Q3 failure needed ("communicate intentions to pedestrians" → "external communication"). Caveat: it's still a general model, not fine-tuned on AV/HMI jargon. For deeply specialized vocabulary, a domain-fine-tuned or instruction-tuned embedder could beat it, so "more accurate" is true on average but not guaranteed on every niche term.

Where it's actually a tradeoff, not an advantage
Latency — worse, not better. MiniLM runs locally: a single query embeds in milliseconds with no network. text-embedding-3-large is an HTTP call to OpenAI — tens-to-hundreds of ms per request plus rate limits. Bulk indexing is fine (batched), but per-query retrieval latency goes up, and you've added a network dependency that can time out or throttle.

Local vs. API-hosted — the opposite of an advantage. It has no public local weights; it's OpenAI-only. So relative to MiniLM you lose: free (it's ~$0.13 per 1M tokens — cheap but not zero), privacy (your document text is sent to a third party), offline capability, and freedom from API keys/rate limits. The only sense in which "API-hosted" is a plus is operational: no GPU to provision, no model to host, managed scaling.


---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

**How source attribution is surfaced in the response:**

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What factors influence trust in autonomous vehicles? | Three layers (Hoff & Bashir, 2015): dispositional (personality, age, gender, culture), situational (system performance, task/environment, effort), and learned trust that grows with experience. | Names dispositional, situational, and learned factors incl. personality and cultural context; notes trust is felt and evolves with experience; cites Hoff & Bashir (2015). All 5 chunks from the correct paper at 0.156–0.205. | Relevant | Accurate |
| 2 | What are key recommendations for designing the HMI in automated vehicles? | Keep the driver engaged/informed; issue alerts and Requests to Intervene (RTI) that quickly orient the driver; use multimodal alerts; scale request explicitness to driver loop-state (in/on/out-of-the-loop); synthesize existing guidelines. | Issue alerts that quickly orient the driver; multimodal alerts effective; scale RTI to in/on/out-of-the-loop; compile existing guidelines. Correct primary report + corroborating Renault paper (0.211–0.300). | Relevant | Accurate |
| 3 | How should an autonomous vehicle communicate its intentions to pedestrians? | External HMI (eHMI) — external displays/visual signals — plus non-visual cues for accessibility (blind/low-vision, deaf). Covered by the accessible-AV review and U.S. Access Board report. | *"I don't have enough information in the provided documents to answer that."* — refused despite the corpus covering the topic. All chunks at ~0.50 (≈3× worse); right document at rank 3 but only bibliography/tangential chunks pulled. | **Off-target** | **Inaccurate (failed to answer)** |
| 4 | How does automation level affect driver situation awareness? | Higher automation (esp. Level 3 / out-of-the-loop) reduces situation awareness as the driver disengages; more takeover lead time and more specific alert cues improve it during transfer of control. | More takeover time and alert-cue specificity improve SA, but explicitly hedges it "does not offer a comprehensive comparison across automation levels." Correct doc (0.260–0.304) but 4/5 chunks were reference-list entries. | Partially relevant | Partially accurate |
| 5 | What is the human-centered multimodal interpreter proposed to explain the actions of autonomous vehicles? | The "What's Happening" paper's Human-centered Multimodal Interpreter: explains AV behavior to non-experts via a visual interface (BEV, maps, text) + voice via a fine-tuned LLM; real-time, concise explanations to improve transparency/trust/acceptance. | A system combining a visual interface (BEV, maps, text) with voice via a fine-tuned LLM; provides real-time, comprehensible explanations of driving behavior. All 5 chunks from the correct paper (0.317–0.367). | Relevant | Accurate |

**Retrieval quality:** Relevant (Q1, Q2, Q5) · Partially relevant (Q4) · Off-target (Q3)  
**Response accuracy:** Accurate (Q1, Q2, Q5) · Partially accurate (Q4) · Inaccurate (Q3)

**Overall:** 3 of 5 fully accurate, 1 partial, 1 failure (Q3). Across the board, response quality
tracked retrieval quality — the only inaccurate answer (Q3) is the only one where retrieval was
off-target (all chunks ~0.50 distance vs ~0.16–0.37 for the accurate answers), confirming the
bottleneck is retrieval, not generation. See the Failure Case Analysis below.

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** "How should an autonomous vehicle communicate its intentions to
pedestrians?" (Q3) — a question the corpus *can* answer: source #4 is a literature review of accessible
AV human-computer interaction and source #7 (U.S. Access Board) discusses how vehicles convey
direction of travel and alerts to people who are blind or deaf.

**What the system returned:** *"I don't have enough information in the provided documents to answer
that."* — a refusal, despite relevant documents existing in the corpus.

**Root cause (tied to a specific pipeline stage):** The failure is in **retrieval (embedding + chunk
content)**, not generation. Two compounding effects: (1) **Bibliography pollution** — several PDFs
have large reference sections, and semantic chunking turns those citation lists into chunks dense
with on-topic keywords ("autonomous vehicle", "pedestrians") but containing no actual answer; they
score deceptively well and crowd the top-5. (2) **Vocabulary mismatch** — the query says "communicate
its intentions to pedestrians," while the relevant paper frames it as "external communication." The
small `all-MiniLM-L6-v2` model didn't bridge these, so *every* retrieved chunk sat at ~0.50 cosine
distance (≈3× worse than the accurate answers at ~0.16). The right document surfaced at rank 3, but
the right *passage* didn't enter the context — so the grounding prompt correctly refused rather than
fabricate. The grounding did its job; retrieval is the bottleneck.

**What you would change to fix it:** (1) **Strip reference/bibliography sections before chunking**
(cut everything after a "References" heading) so citation lists stop competing for retrieval slots —
the highest-leverage fix, likely to resolve Q3 and improve Q4. (2) **Increase k to 8–10** so a
relevant passage at a deeper rank can still enter the context. (3) **Add query rewriting / a larger
embedding model** with stronger paraphrase matching to bridge the "intentions to pedestrians" ↔
"external communication" vocabulary gap.

---

## Spec Reflection

**One way the spec helped you during implementation:** Writing the Chunking Strategy and Retrieval
Approach sections *before* coding meant I had concrete, testable parameters to hand the AI tool —
semantic splitting with `buffer_size=1`, a 95th-percentile breakpoint, a 256-token cap, top-k=5,
`all-MiniLM-L6-v2`, ChromaDB with cosine. Because those numbers were written down, the generated
ingestion and retrieval code matched intent on the first pass, and I could *verify* it against the
spec rather than guess — e.g. re-tokenising every chunk to confirm the 256-token cap actually held
(mean ≈185, max 258). The 5 planned evaluation questions likewise gave the evaluation a fixed target
instead of cherry-picking questions after the fact.

**One way your implementation diverged from the spec, and why:** The spec called for AutoRAG's
built-in `Semantic_llama_index` chunker, but it deadlocked on this machine — its LlamaIndex
`HuggingFaceEmbedding` backend fork-bombed and hung at 0% CPU on macOS + torch, reproducibly. Rather
than abandon semantic chunking, I diverged by re-implementing the *identical* algorithm in
`semantic_chunk.py` using `sentence-transformers` directly (same `buffer_size`, same 95th-percentile
breakpoint, same embedding model), while still parsing with AutoRAG. The divergence was forced by a
tooling failure, not a change of design — the spec's intent (meaning-based boundaries) was preserved,
and the switch also let me add the 256-token cap that fixed a silent-truncation bug.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* 
I gave the link to AutoRAG library which has in built functions for various RAG operations. 

- *What it produced:*
Did the below:

1) Install AutoRAG into the venv 
2) Write parse_config.yaml
3) Write chunk_config.yaml 
4) Write RAG.py to run Parser then Chunker
5) Run pipeline and verify parsed + chunked parquet output

- *What I changed or overrode:*
The chunking strategy that it used has pretty large cosine distance between chunks meaning it was not chunking meaningfully. So, I used a different libary and chunking strategy for the chunking. 

**Instance 2**

- *What I gave the AI:* Build a evaluation test questions.
- *What it produced:* Produced the questions in test.md
- *What I changed or overrode:* Everything accepted. 
# flexiRAG
