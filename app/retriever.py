"""A small, dependency-free keyword retriever (TF-IDF with synonym expansion).

Deliberately simple: the index is a few dozen hand-written chunks, so lexical
scoring with a synonym map gives good, explainable results with zero runtime
cost. Swap this module for embeddings + a vector store if the corpus grows.
"""
from __future__ import annotations

import math
import re
import time
from collections import Counter
from dataclasses import dataclass

STOPWORDS = set(
    "a an the is are was were what which who whom how has have had he his him does did do "
    "of in on at to for with and or about any tell me show give list as by from it its this "
    "that there can could would".split()
)

SYNONYMS = {
    "agent": "agents agentic", "agents": "agent agentic", "llm": "llms ai", "ai": "llm agent",
    "rag": "retrieval vector", "cloud": "aws", "aws": "cloud s3", "scale": "requests performance",
    "performance": "latency scale", "lead": "leadership mentor", "leadership": "lead mentor",
    "team": "mentor lead", "kafka": "etl", "data": "etl pipelines", "experience": "years",
    "python": "backend", "backend": "python", "monitoring": "observability alerting",
    "db": "database", "sql": "mysql database",
}


def tokenize(text: str) -> list[str]:
    words = re.sub(r"[^a-z0-9+ ]", " ", text.lower()).split()
    out = []
    for w in words:
        if w in STOPWORDS:
            continue
        if len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.append(w)
    return out


@dataclass(frozen=True)
class Hit:
    id: str
    title: str
    answer: str
    score: float


class Retriever:
    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        self.docs = [Counter(tokenize(f"{c['title']} {c.get('keywords', '')} {c['answer']}")) for c in chunks]
        df: Counter = Counter()
        for d in self.docs:
            df.update(d.keys())
        n = len(chunks)
        self._idf = {w: math.log(1 + n / c) for w, c in df.items()}

    def search(self, query: str, k: int = 3) -> dict:
        t0 = time.perf_counter()
        base = tokenize(query)
        terms = dict.fromkeys(base)
        for w in base:
            for s in SYNONYMS.get(w, "").split():
                for t in tokenize(s):
                    terms.setdefault(t)

        scored = []
        for i, doc in enumerate(self.docs):
            s = 0.0
            for w in terms:
                tf = doc.get(w, 0)
                if tf:
                    weight = 1.0 if w in base else 0.5
                    s += weight * self._idf[w] * (1 + math.log(tf))
            if s > 0:
                scored.append((s, i))
        scored.sort(reverse=True)
        top = scored[:k]
        best = top[0][0] if top else 1.0
        hits = [
            Hit(
                id=self.chunks[i]["id"],
                title=self.chunks[i]["title"],
                answer=self.chunks[i]["answer"],
                score=round(0.55 + 0.44 * (s / best), 2),
            )
            for s, i in top
        ]
        return {
            "query": query,
            "terms": list(terms),
            "indexed": len(self.chunks),
            "hits": [h.__dict__ for h in hits],
            "ms": round((time.perf_counter() - t0) * 1000, 2),
        }
