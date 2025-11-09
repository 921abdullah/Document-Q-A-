# app/services/answering.py

import re
from typing import List, Dict

def extractive_answer(query: str, retrieved: List[Dict]) -> str:
    """
    A simple extractive answer generator:
    - Looks for the most relevant sentence in top snippets
    - Returns a concise answer
    """

    if not retrieved:
        return "No relevant information found."

    # Combine top snippets
    combined_text = " ".join(r["snippet"] for r in retrieved)

    # Split into sentences
    sentences = re.split(r'(?<=[.!?]) +', combined_text)

    # Heuristic: pick sentence(s) that contain key words from query
    query_words = [w.lower() for w in re.findall(r'\w+', query)]
    ranked = []
    for s in sentences:
        score = sum(1 for w in query_words if w in s.lower())
        ranked.append((score, s.strip()))

    # Pick highest scoring sentence
    ranked.sort(key=lambda x: x[0], reverse=True)
    best_sentence = ranked[0][1] if ranked else retrieved[0]["snippet"]

    # Optionally shorten long sentences
    if len(best_sentence) > 300:
        best_sentence = best_sentence[:297] + "..."

    return best_sentence
