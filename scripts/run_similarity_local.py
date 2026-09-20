"""Rerun the pre-recorded predictions with a real local semantic embedder."""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import LocalEmbedder, compute_similarity
from dotenv import load_dotenv


def main():
    load_dotenv(ROOT / '.env', encoding='utf-8-sig')
    embedder = LocalEmbedder(model_name=os.getenv('LOCAL_EMBEDDING_MODEL', 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'))
    rows = json.loads((ROOT / 'report/similarity_predictions.json').read_text(encoding='utf-8'))
    for row in rows:
        row['score'] = compute_similarity(embedder(row['a']), embedder(row['b']))
    (ROOT / 'report/similarity_local_results.json').write_text(json.dumps({
        'backend': embedder._backend_name,
        'executed_at': datetime.now(timezone.utc).isoformat(),
        'predictions_recorded_before_run': True,
        'results': rows,
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Saved similarity_local_results.json')


if __name__ == '__main__':
    main()
