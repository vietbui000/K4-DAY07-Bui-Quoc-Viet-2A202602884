import math

import pytest

from bench import evaluate, load_corpus
from src import Document, EmbeddingStore, HeadingChunker, KnowledgeBaseAgent
from src.gemini_runtime import GeminiRuntime


def test_heading_keeps_sections_separate():
    chunks = HeadingChunker().chunk('## Buyer\nReturn conditions.\n\n## Seller\nClaim conditions.')
    assert len(chunks) == 2
    assert 'Seller' not in chunks[0] and 'Buyer' not in chunks[1]


def test_long_section_repeats_heading_and_preserves_words():
    body = ' '.join(f'word{i}' for i in range(60))
    chunks = HeadingChunker(80).chunk('## Returns\n' + body)
    assert all(c.startswith('## Returns\n') and len(c) <= 80 for c in chunks)
    assert ''.join(c.removeprefix('## Returns\n') for c in chunks) == body


def test_nested_heading_keeps_parent_context():
    chunks = HeadingChunker().chunk('# Policy\n## Returns\nConditions.\n### Exceptions\nExceptions here.')
    assert '# Policy\n## Returns\n### Exceptions\nExceptions here.' in chunks
    assert HeadingChunker().chunk('   ') == []


def test_gemini_requires_key(monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    monkeypatch.delenv('GOOGLE_API_KEY', raising=False)
    with pytest.raises(ValueError, match='GEMINI_API_KEY'):
        GeminiRuntime()


def test_normalization_cache_and_generation(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'test-only-no-network')
    client = GeminiRuntime()
    calls = []

    def fake_post(model, method, payload):
        calls.append((method, payload))
        if method == 'embedContent':
            return {'embedding': {'values': [3, 4]}}
        return {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': 'Answer [1]'}]}}]}

    monkeypatch.setattr(client, '_post', fake_post)
    assert client.embed('text') == [0.6, 0.8]
    assert math.isclose(math.hypot(*client.embed('text')), 1)
    assert len(calls) == 1
    assert client.generate('Context') == 'Answer [1]'


def test_no_fake_answer_for_blocked_output(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'test-only-no-network')
    client = GeminiRuntime()
    monkeypatch.setattr(client, '_post', lambda *args: {'candidates': []})
    with pytest.raises(RuntimeError, match='complete answer'):
        client.generate('question')


def test_benchmark_calls_agent_with_filtered_context():
    store = EmbeddingStore(embedding_fn=lambda _: [1.0, 0.0])
    store.add_documents([Document('b', 'buyer evidence', {'audience': 'buyer'}),
                         Document('s', 'seller evidence', {'audience': 'seller'})])
    prompts = []
    agent = KnowledgeBaseAgent(store, lambda p: prompts.append(p) or 'Answer [1]')
    rows = evaluate(store, agent, [{'id': 1, 'query': 'question', 'filter': {'audience': 'seller'}}])
    assert 'seller evidence' in prompts[0] and 'buyer evidence' not in prompts[0]
    assert rows[0]['agent_answer'] == 'Answer [1]'
    assert len(rows[0]['unfiltered_top3']) == 2
    assert len(rows[0]['top3']) == 1


def test_loader_excludes_frontmatter_and_retains_doc_id(tmp_path):
    (tmp_path / 'policy.md').write_text('---\ndoc_id: policy\naudience: buyer\n---\n## Returns\nConditions.', encoding='utf-8')
    docs, hashes = load_corpus(tmp_path, HeadingChunker())
    assert len(docs) == 1 and docs[0].metadata['doc_id'] == 'policy'
    assert 'audience:' not in docs[0].content
    assert len(hashes['policy']) == 64
