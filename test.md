# flexiRAG — Evaluation Report

System under test: 9 PDFs (autonomous-vehicle trust, HMI, and HCI) parsed with AutoRAG/pdfminer,
semantically chunked (686 chunks, ≤256 tokens each), embedded with `all-MiniLM-L6-v2`, stored in
ChromaDB (cosine), retrieved top-k=5, generated with Groq `llama-3.3-70b-versatile` under a
grounding prompt that forbids outside knowledge and requires source-filename citations.

Reproduce with: `python eval_run.py` (or `python RAG.py ask "<question>"` per question).

Distance = cosine distance of the retrieved chunk (lower = closer match). It is the clearest signal
of retrieval quality: strong answers below pulled chunks at ~0.16–0.36; the failure case pulled
chunks at ~0.50.

---

## Summary

| # | Question | Retrieval | Response |
|---|----------|-----------|----------|
| 1 | Factors influencing trust in AVs | Relevant | Accurate |
| 2 | HMI design recommendations | Relevant | Accurate |
| 3 | Communicating AV intentions to pedestrians | **Off-target** | **Inaccurate (failed to answer)** |
| 4 | Effect of automation level on situation awareness | Partially relevant | Partially accurate |
| 5 | The "What's Happening" multimodal interpreter | Relevant | Accurate |

---

## Q1 — What factors influence trust in autonomous vehicles?

**Correct answer (ground truth):** Trust in AVs is shaped by three layers (Hoff & Bashir, 2015):
*dispositional* factors (personality, age, gender, culture), *situational* factors (system
performance, task/environment, level of effort), and *learned/dynamic* trust that develops through
experience and interaction over time.

**System returned (summary):** Trust is influenced by dispositional, situational, and learned
factors, including personality traits and cultural context; it is felt (not only reasoned) and
evolves through experience; cites Hoff & Bashir (2015) on investigating trust factors in real-world
environments across social, material, emotional, and cultural dimensions.

**Retrieved chunks (all from `Trusting_autonomous_vehicles_An_interdisciplinary_.pdf`):**
0.156, 0.178, 0.195, 0.196, 0.205.

**Retrieval: Relevant.** All five chunks come from the correct paper at very low distances.
**Response: Accurate.** Correctly names the dispositional/situational/learned structure and the
key source. (Minor: chunks [1] and [3] were bibliography entries, but the substantive chunks [4]/[5]
carried the answer.)

---

## Q2 — What are key recommendations for designing the human-machine interface (HMI) in automated vehicles?

**Correct answer (ground truth):** Keep the driver engaged and informed of system status/actions;
issue alerts and Requests to Intervene (RTI) that quickly and sufficiently orient the driver to the
driving task; use multimodal alerts (visual + auditory + tactile); scale how explicit the request is
to the driver's engagement state (in-the-loop / on-the-loop / out-of-the-loop). The report's purpose
is to compile and synthesize existing guidelines for effective automated-driving interfaces.

**System returned (summary):** Issue alerts/requests that quickly orient the driver; multimodal
alerts are prominent and effective; scale RTI explicitness to whether the driver is in/on/out-of-the
loop; compile existing guidelines to identify new ones.

**Retrieved chunks:** `HMI-and-Automation-Design-Recommendations.pdf` (0.211), the Renault HMI paper
`1-s2.0-S2405896316322418-main.pdf` (0.233), then three more from the HMI recommendations doc
(0.244, 0.263, 0.300).

**Retrieval: Relevant.** Correct primary document plus a corroborating HMI paper.
**Response: Accurate.** Faithfully reflects the report's core recommendations with correct citations.

---

## Q3 — How should an autonomous vehicle communicate its intentions to pedestrians?  *(FAILURE CASE)*

**Correct answer (ground truth):** AVs signal intent to pedestrians through *external* HMI (eHMI) —
external displays/visual signals — and, for accessibility, non-visual cues. The corpus explicitly
covers this: `3750069.3750162.pdf` is *"Towards Inclusive External Communication of Autonomous
Vehicles for Pedestrians with Vision Impairments"* (CHI 2020), and `usab-av-forum-summary-report.pdf`
discusses how vehicles convey direction of travel and alerts to people who are blind or deaf. So the
question **is answerable** from the documents.

**System returned (verbatim):** *"I don't have enough information in the provided documents to answer
that."*

**Retrieved chunks:** `e000078_Chand.pdf` (0.497), `usab-av-forum-summary-report.pdf` (0.501),
`3750069.3750162.pdf` (0.502), `usab-av-forum-summary-report.pdf` (0.509),
`HMI-and-Automation-Design-Recommendations.pdf` (0.512).

**Retrieval: Off-target.** Note every distance is ~0.50 — roughly 3× worse than Q1/Q2/Q5. The right
*documents* appear (the inclusive-communication paper is at rank 3), but the specific chunks pulled
were bibliography entries and tangential fragments rather than the passages describing the eHMI
method itself.
**Response: Inaccurate (failed to answer an answerable question).** The grounding prompt did its job
— given weak, citation-heavy context, the model correctly refused rather than hallucinate — but the
end-to-end system failed: it returned nothing useful for a question the corpus can support. See the
failure analysis below.

---

## Q4 — How does automation level affect driver situation awareness?

**Correct answer (ground truth):** Higher automation (especially Level 3 / out-of-the-loop) tends to
*reduce* driver situation awareness because the driver disengages from the driving task; giving more
lead time before a takeover and using more specific alert cues improves situation awareness during
the transfer of control.

**System returned (summary):** SA increases when drivers have more time to take over in a Level 3
car; alert-cue specificity affects SA during transfer of control — but explicitly hedges that the
context "does not offer a comprehensive comparison of situation awareness across different automation
levels."

**Retrieved chunks (all `HMI-and-Automation-Design-Recommendations.pdf`):** 0.260, 0.274, 0.279,
0.302, 0.304.

**Retrieval: Partially relevant.** Correct document and topic, but four of the five chunks are
reference-list entries (citation titles), not body prose — so the model had thin substantive text.
**Response: Partially accurate.** The points it makes are correct, but the answer is shallow and the
model honestly flags that it cannot give the full picture — a direct consequence of retrieving
citation fragments rather than discussion sections.

---

## Q5 — What is the human-centered multimodal interpreter proposed to explain the actions of autonomous vehicles?

**Correct answer (ground truth):** The "What's Happening" paper (`2501.05322v2.pdf`) introduces a
**Human-centered Multimodal Interpreter (HMI) system** that explains AV driving behavior to
non-expert users through multiple modalities: a visual interface (Bird's Eye View, maps, text) plus
voice interaction driven by a fine-tuned LLM, delivering real-time, concise, understandable
explanations to improve transparency, trust, and acceptance.

**System returned (summary):** A system combining a visual interface (BEV, maps, text) with voice
interaction via a fine-tuned LLM; called the Human-centered Multimodal Interpreter, it provides
real-time, concise, comprehensible responses and integrates visual/textual/auditory feedback to
explain driving behaviors.

**Retrieved chunks (all `2501.05322v2.pdf`):** 0.317, 0.345, 0.358, 0.364, 0.367.

**Retrieval: Relevant.** All five chunks from the correct paper, including the body passage that
introduces the system.
**Response: Accurate.** Matches the paper's described architecture and purpose closely. Best case of
the five.

---

## Failure Case Analysis — Q3 (pedestrian communication)

**Question that failed:** "How should an autonomous vehicle communicate its intentions to
pedestrians?"

**What the system returned:** "I don't have enough information in the provided documents to answer
that." — despite the corpus containing a paper dedicated to exactly this topic.

**Root cause (retrieval stage — embedding + chunk content):** Two compounding effects.
1. **Bibliography pollution.** Several source PDFs (notably the HMI recommendations report and
   `e000078_Chand.pdf`) contain large reference/bibliography sections. Semantic chunking turns those
   reference lists into chunks whose text is dense with on-topic keywords ("autonomous vehicle",
   "pedestrians", "communication") but contains *no actual answer* — only citation titles. These
   chunks score deceptively well on keyword-laden similarity and crowd the top-k, pushing out the
   substantive method passages.
2. **Vocabulary mismatch.** The query says "communicate its intentions to pedestrians," while the
   relevant paper frames it as "external communication" for "pedestrians with vision impairments."
   `all-MiniLM-L6-v2` did not map these closely — every retrieved chunk sat at ~0.50 distance,
   ~3× higher than the strong questions (~0.16). The right document surfaced (rank 3) but the
   right *passage* did not.

The grounding prompt then behaved correctly given weak input — it refused rather than fabricate — so
the failure is upstream in retrieval, not generation.

**What I would change to fix it:**
- **Strip bibliography/reference sections before chunking** (e.g., cut everything after a
  "References" heading), so citation lists stop competing for retrieval slots. This is the
  highest-leverage fix and would likely resolve Q3 and improve Q4.
- **Increase k** (e.g., 8–10) so the substantive passage at deeper ranks can enter the context.
- **Add a lightweight query rewrite / multi-query step** (e.g., also search "external HMI" and
  "eHMI") to bridge the vocabulary gap, or use a larger embedding model with stronger paraphrase
  matching.
