"""Hybrid retrieval: dense vectors in FAISS + BM25 keywords, merged with reciprocal rank fusion."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import faiss
import numpy as np
from rank_bm25 import BM25Okapi

from opspilot import config

TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens for BM25."""
    return TOKEN.findall(text.lower())


@dataclass
class Chunk:
    chunk_id: str   # citation tag, e.g. "KB-07 §2"
    doc_id: str     # e.g. "KB-07"
    title: str      # document title + section heading
    text: str


def load_chunks(folder: Path = config.KNOWLEDGE_DIR) -> list[Chunk]:
    """Split each Markdown file into one chunk per '## ' section."""
    chunks: list[Chunk] = []
    for path in sorted(folder.glob("*.md")):
        doc_id = path.name.split("_")[0]
        raw = path.read_text(encoding="utf-8")
        doc_title = raw.splitlines()[0].lstrip("# ").strip()
        for n, section in enumerate(raw.split("\n## ")[1:], start=1):
            heading, _, body = section.partition("\n")
            chunks.append(Chunk(f"{doc_id} §{n}", doc_id, f"{doc_title}: {heading.strip()}",
                                " ".join(body.split())))
    return chunks


class Embedder:
    """sentence-transformers when available; otherwise TF-IDF (offline, deterministic)."""

    def __init__(self, texts: list[str]):
        self.backend = "tfidf"
        if config.EMBEDDINGS in ("auto", "sentence-transformers"):
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(config.ST_MODEL)
                self.backend = "sentence-transformers"
            except Exception:  # not installed or model download blocked
                if config.EMBEDDINGS == "sentence-transformers":
                    raise
        if self.backend == "tfidf":
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.model = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True,
                                         stop_words="english").fit(texts)

    def encode(self, texts: list[str]) -> np.ndarray:
        """Return L2-normalised float32 vectors, so inner product = cosine similarity."""
        if self.backend == "sentence-transformers":
            vecs = self.model.encode(texts, normalize_embeddings=True)
        else:
            vecs = self.model.transform(texts).toarray()
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            vecs = vecs / np.where(norms == 0, 1, norms)
        return np.asarray(vecs, dtype="float32")


class Retriever:
    """Builds both indexes once, then answers search() calls."""

    def __init__(self, chunks: list[Chunk] | None = None):
        self.chunks = chunks or load_chunks()
        texts = [f"{c.title}. {c.text}" for c in self.chunks]
        self.embedder = Embedder(texts)
        vectors = self.embedder.encode(texts)
        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)
        self.bm25 = BM25Okapi([tokenize(t) for t in texts])

    @property
    def min_evidence(self) -> float:
        return config.MIN_EVIDENCE_SCORE[self.embedder.backend]

    def search(self, query: str, k: int = config.TOP_K) -> list[dict]:
        """Top-k chunks by reciprocal rank fusion of dense and BM25 rankings.

        Each hit carries 'score' = dense cosine similarity, used as the evidence-strength signal.
        """
        n = len(self.chunks)
        sims, ids = self.index.search(self.embedder.encode([query]), n)
        dense_rank = {int(i): r for r, i in enumerate(ids[0])}
        dense_sim = {int(i): float(s) for s, i in zip(sims[0], ids[0])}
        bm25_scores = self.bm25.get_scores(tokenize(query))
        bm25_rank = {int(i): r for r, i in enumerate(np.argsort(-bm25_scores))}
        fused = {i: 1 / (60 + dense_rank[i]) + 1 / (60 + bm25_rank[i]) for i in range(n)}
        best = sorted(fused, key=fused.get, reverse=True)[:k]
        return [{"chunk_id": self.chunks[i].chunk_id, "doc_id": self.chunks[i].doc_id,
                 "title": self.chunks[i].title, "text": self.chunks[i].text,
                 "score": round(dense_sim[i], 4)} for i in best]


_RETRIEVER: Retriever | None = None


def get_retriever() -> Retriever:
    """Build the retriever once per process (loading embeddings is slow)."""
    global _RETRIEVER
    if _RETRIEVER is None:
        _RETRIEVER = Retriever()
    return _RETRIEVER
