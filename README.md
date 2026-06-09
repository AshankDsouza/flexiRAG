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
| 10 | **⚠️ STILL NEEDED — the corpus currently has only 9 unique documents. Add at least one more to meet the "≥10 documents" requirement, then re-run `ingest` + `index`.** | | |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

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

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

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

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

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

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*
# flexiRAG
