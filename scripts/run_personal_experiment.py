"""Offline demonstration only: starter corpus + mock embeddings/LLM, not group benchmark."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from check_checkpoint2 import metadata
from src import Document, EmbeddingStore, KnowledgeBaseAgent, MockEmbedder, RecursiveChunker, compute_similarity


def demo_llm(prompt):
    context = prompt.split('Context:\n', 1)[1].split('\n\nQuestion:', 1)[0]
    return '[MOCK LLM: chỉ trả lại context, không sinh đáp án chính sách]\n' + context


def main():
    embedder = MockEmbedder()
    predictions = json.loads((ROOT / 'report/similarity_predictions.json').read_text(encoding='utf-8'))
    for row in predictions:
        row['score'] = compute_similarity(embedder(row['a']), embedder(row['b']))
    (ROOT / 'report/similarity_results.json').write_text(json.dumps(
        {'backend': 'MockEmbedder (hash-based, not semantic)', 'results': predictions},
        ensure_ascii=False, indent=2), encoding='utf-8')

    store = EmbeddingStore(embedding_fn=embedder)
    chunker = RecursiveChunker(chunk_size=500)
    for path in sorted((ROOT / 'data/ecommerce').glob('*.md')):
        fields, content = metadata(path.read_text(encoding='utf-8-sig'))
        store.add_documents([Document(f'{fields["doc_id"]}-{i}', chunk,
                                      {**fields, 'chunk_index': i})
                             for i, chunk in enumerate(chunker.chunk(content))])
    # Proposed questions for a pipeline demonstration; the team has not approved them.
    questions = [
        ('Người mua cần đáp ứng điều kiện nào để yêu cầu đổi trả?', {'audience': 'buyer'}),
        ('Người mua có bao nhiêu ngày để yêu cầu hoàn tiền?', {'audience': 'buyer'}),
        ('Ai chịu trách nhiệm xử lý yêu cầu bảo hành?', {'audience': 'seller'}),
        ('Người bán phải phản hồi yêu cầu bảo hành trong bao lâu?', {'audience': 'seller'}),
        ('Người bán từ chối yêu cầu bảo hành hợp lệ có thể chịu hậu quả gì?', {'audience': 'seller'}),
    ]
    agent = KnowledgeBaseAgent(store, demo_llm)
    results = []
    for question, filters in questions:
        results.append({'question': question, 'metadata_filter': filters,
                        'top3': store.search_with_filter(question, 3, filters),
                        'unfiltered_top3': store.search(question, 3),
                        'agent_answer': agent.answer(question, 3, filters),
                        'relevance': 'Chưa chấm: dữ liệu mẫu, chưa có gold answer của nhóm'})
    (ROOT / 'report/retrieval_demo_results.json').write_text(json.dumps(
        {'status': 'DEMO ONLY - not official benchmark', 'embedding': 'MockEmbedder',
         'llm': 'mock context echo', 'strategy': 'RecursiveChunker(chunk_size=500)',
         'corpus': 'data/ecommerce (starter templates)', 'chunk_count': store.get_collection_size(),
         'results': results}, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Saved similarity_results.json and retrieval_demo_results.json (DEMO ONLY).')


if __name__ == '__main__':
    main()
