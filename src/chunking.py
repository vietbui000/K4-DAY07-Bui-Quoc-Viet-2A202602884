from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        sentences = [part.strip() for part in re.split(r'(?<=[.!?])\s+', text.strip()) if part.strip()]
        size = self.max_sentences_per_chunk
        return [' '.join(sentences[i:i + size]) for i in range(0, len(sentences), size)]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if self.chunk_size <= 0:
            raise ValueError('chunk_size must be positive')
        return self._split(text, self.separators) if text else []

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text] if current_text else []
        if not remaining_separators or remaining_separators[0] == '':
            return [current_text[i:i + self.chunk_size]
                    for i in range(0, len(current_text), self.chunk_size)]
        separator, *rest = remaining_separators
        # Keep separators so punctuation and paragraph boundaries are not lost.
        pieces = current_text.split(separator)
        pieces = [piece + separator if i < len(pieces) - 1 else piece
                  for i, piece in enumerate(pieces)]
        chunks, pending = [], ''
        for piece in pieces:
            if len(piece) > self.chunk_size:
                if pending:
                    chunks.append(pending)
                    pending = ''
                chunks.extend(self._split(piece, rest))
            elif len(pending) + len(piece) <= self.chunk_size:
                pending += piece
            else:
                chunks.append(pending)
                pending = piece
        if pending:
            chunks.append(pending)
        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    if len(vec_a) != len(vec_b):
        raise ValueError('Vectors must have the same dimension')
    norm_a, norm_b = math.hypot(*vec_a), math.hypot(*vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    score = sum((a / norm_a) * (b / norm_b) for a, b in zip(vec_a, vec_b))
    return max(-1.0, min(1.0, score))


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        if chunk_size <= 0:
            raise ValueError('chunk_size must be positive')
        strategies = {
            'fixed_size': FixedSizeChunker(chunk_size, overlap=min(50, chunk_size - 1)),
            'by_sentences': SentenceChunker(),
            'recursive': RecursiveChunker(chunk_size=chunk_size),
        }
        result = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            result[name] = {'count': len(chunks),
                            'avg_length': sum(map(len, chunks)) / len(chunks) if chunks else 0.0,
                            'chunks': chunks}
        return result
