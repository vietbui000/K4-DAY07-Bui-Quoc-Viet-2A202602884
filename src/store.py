from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Uses an isolated in-memory store; no optional database dependency is needed.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

    def _make_record(self, doc: Document) -> dict[str, Any]:
        metadata = dict(doc.metadata)
        metadata.setdefault('doc_id', doc.id)
        embedding = list(self._embedding_fn(doc.content))
        record = {'id': f'{doc.id}:{self._next_index}', 'content': doc.content,
                  'metadata': metadata, 'embedding': embedding}
        self._next_index += 1
        return record

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if top_k <= 0 or not records:
            return []
        query_embedding = self._embedding_fn(query)
        results = []
        for record in records:
            if len(query_embedding) != len(record['embedding']):
                raise ValueError('Query and document embeddings must have the same dimension')
            results.append({'id': record['id'], 'content': record['content'],
                            'metadata': dict(record['metadata']),
                            'score': _dot(query_embedding, record['embedding'])})
        return sorted(results, key=lambda result: result['score'], reverse=True)[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        Store a separate record per chunk, preserving the parent doc_id.
        """
        records = [self._make_record(doc) for doc in docs]
        self._store.extend(records)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        filters = metadata_filter or {}
        records = [record for record in self._store
                   if all(key in record['metadata'] and record['metadata'][key] == value
                          for key, value in filters.items())]
        return self._search_records(query, records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        before = len(self._store)
        self._store = [record for record in self._store if record['metadata']['doc_id'] != doc_id]
        return len(self._store) < before
