"""Lazada benchmark: heading chunks + real Gemini embeddings and agent answers."""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from scripts.check_checkpoint2 import metadata
from src import Document, EmbeddingStore, HeadingChunker, KnowledgeBaseAgent
from src.gemini_runtime import GeminiRuntime
from src.groq_runtime import GroqRuntime

ROOT = Path(__file__).resolve().parent


def parse_markdown_file(filepath):
    return metadata(filepath.read_text(encoding='utf-8-sig'))


def load_corpus(data_dir, chunker):
    files = sorted(data_dir.glob('*.md'))
    if not files:
        raise ValueError(f'No Markdown documents in {data_dir}')
    docs, hashes = [], {}
    for path in files:
        meta, content = parse_markdown_file(path)
        if not content or not meta.get('doc_id'):
            raise ValueError(f'Missing content/doc_id: {path.name}')
        doc_id = meta['doc_id']
        if doc_id in hashes:
            raise ValueError(f'Duplicate doc_id: {doc_id}')
        hashes[doc_id] = hashlib.sha256(path.read_bytes()).hexdigest()
        for i, text in enumerate(chunker.chunk(content)):
            docs.append(Document(f'{doc_id}#{i}', text, {**meta, 'chunk_index': i}))
    return docs, hashes


def load_queries(path):
    queries = json.loads(path.read_text(encoding='utf-8'))
    if len(queries) != 5 or len({q['id'] for q in queries}) != 5:
        raise ValueError('Expected exactly five questions with unique IDs')
    for item in queries:
        if not item.get('query') or not isinstance(item['query'], str):
            raise ValueError('Question text must not be empty')
        if item.get('filter') is not None and not isinstance(item['filter'], dict):
            raise ValueError('Question filter must be an object or null')
    return queries


def evaluate(store, agent, queries):
    results = []
    for item in queries:
        question, filters = item['query'], item.get('filter')
        results.append({
            'id': item['id'], 'query': question, 'filter': filters,
            'top3': store.search_with_filter(question, top_k=3, metadata_filter=filters),
            'unfiltered_top3': store.search(question, top_k=3),
            'agent_answer': agent.answer(question, top_k=3, metadata_filter=filters),
            'gold_answer': item.get('gold_answer'),
            'evidence': item.get('evidence', []),
            'relevance_review': None, 'answer_correctness_review': None,
        })
    return results


def run_benchmark():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true', help='Inspect chunks/configuration without API calls')
    args = parser.parse_args()
    load_dotenv(ROOT / '.env', override=False, encoding='utf-8-sig')
    queries = load_queries(ROOT / 'data/lazada/benchmark_queries.json')
    docs, hashes = load_corpus(ROOT / 'data/lazada', HeadingChunker(chunk_size=500))
    confirmed = all(q.get('verification_status') == 'user_confirmed_source'
                    and q.get('gold_answer') and q.get('evidence')
                    and all(e.get('sha256') == hashes.get(e.get('doc_id')) for e in q['evidence'])
                    for q in queries)
    status = 'user_confirmed_sources_pending_evaluation' if confirmed else 'provisional_unverified_sources'
    print(f'Viet: HeadingChunker(500), {len(hashes)} documents, {len(docs)} chunks, top_k=3')
    print(f'Status: {status}. Source confirmation is user-provided; answer evaluation remains separate.')
    if args.dry_run:
        target = ROOT / 'report/heading_chunks_preview.json'
        target.write_text(json.dumps([{'id': d.id, 'content': d.content, 'metadata': d.metadata}
                                      for d in docs], ensure_ascii=False, indent=2), encoding='utf-8')
        print('Dry run complete. No embedding, LLM or benchmark scores generated.')
        return 0
    provider = os.getenv('LLM_PROVIDER', 'gemini').lower()
    if provider == 'groq':
        runtime = GroqRuntime()
        runtime.check_access()
    elif provider == 'gemini':
        runtime = GeminiRuntime()
    else:
        raise ValueError('LLM_PROVIDER must be groq or gemini')
    print(f'Embedding: {runtime.embedding_model}; LLM: {runtime.llm_model}; no mock fallback')
    store = EmbeddingStore('lazada_viet_heading', embedding_fn=runtime.embed)
    store.add_documents(docs)
    agent = KnowledgeBaseAgent(store, runtime.generate)
    results = evaluate(store, agent, queries)
    output = {
        'status': status,
        'llm_provider': provider,
        'executed_at': datetime.now(timezone.utc).isoformat(),
        'strategy': 'HeadingChunker(chunk_size=500)', 'embedding_model': runtime.embedding_model,
        'llm_model': runtime.llm_model, 'top_k': 3, 'chunk_count': len(docs),
        'corpus_sha256': hashes,
        'queries_sha256': hashlib.sha256((ROOT / 'data/lazada/benchmark_queries.json').read_bytes()).hexdigest(),
        'results': results,
    }
    target = ROOT / 'report/benchmark_viet_heading.json'
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = [f'# Ket qua Viet - Heading + {provider}', '',
             f'Status: {status}; human evaluation pending.',
             f'Embedding: {runtime.embedding_model}; LLM: {runtime.llm_model}', '']
    for row in results:
        lines.extend([f"## {row['id']}. {row['query']}", f"Filter: {row['filter']}", ''])
        for rank, hit in enumerate(row['top3'], 1):
            lines.extend([f"[{rank}] {hit['id']} | cosine={hit['score']:.6f}", hit['content'], ''])
        lines.extend(['Agent:', row['agent_answer'], ''])
    (ROOT / 'report/benchmark_viet_heading.md').write_text('\n'.join(lines), encoding='utf-8')
    print(f'Saved {target.name} and benchmark_viet_heading.md; review answers against sources.')
    return 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    try:
        raise SystemExit(run_benchmark())
    except (ValueError, RuntimeError, OSError, KeyError) as exc:
        print(f'Benchmark stopped: {exc}', file=sys.stderr)
        raise SystemExit(1)
