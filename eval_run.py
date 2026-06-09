"""Temporary eval harness: run candidate questions and dump structured results
(question, answer, retrieved chunks with source/distance/snippet) for writing
the evaluation report."""

import RAG

QUESTIONS = [
    "What factors influence trust in autonomous vehicles?",
    "What are key recommendations for designing the human-machine interface (HMI) in automated vehicles?",
    "How should an autonomous vehicle communicate its intentions to pedestrians?",
    "What challenges arise during the takeover or transition of control from automation to the human driver?",
    "What is the human-centered multimodal interpreter proposed to explain the actions of autonomous vehicles?",
    "How does automation level affect driver situation awareness?",
]

for qi, q in enumerate(QUESTIONS, 1):
    retrieved = RAG.retrieve(q, k=5)
    answer = RAG.generate(q, retrieved)
    print("=" * 100)
    print(f"Q{qi}: {q}")
    print("-" * 100)
    print("ANSWER:")
    print(answer)
    print("-" * 100)
    print("RETRIEVED CHUNKS:")
    for i, (doc, meta, dist) in enumerate(retrieved, 1):
        body = doc.split("contents:", 1)[-1].strip().replace("\n", " ")
        print(f"  [{i}] {meta['source']}  (dist {dist:.3f})")
        print(f"       {body[:200]}...")
    print()
