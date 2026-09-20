"""Download the chosen public Sentence Transformers model without the Xet client."""
import json
import hashlib
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
TARGET = ROOT / '.models' / 'paraphrase-multilingual-MiniLM-L12-v2'


def download_weights(url, path, expected_hash, size):
    def part(index):
        start = size * index // 8
        end = size * (index + 1) // 8 - 1
        dest = path.with_suffix(f'.part{index}')
        if dest.exists() and dest.stat().st_size == end - start + 1:
            return dest
        request = Request(url, headers={'Range': f'bytes={start}-{end}'})
        with urlopen(request, timeout=60) as response:
            if response.status != 206 or response.headers.get('Content-Range') != f'bytes {start}-{end}/{size}':
                raise RuntimeError('Server did not honor byte range')
            with dest.open('wb') as handle:
                shutil.copyfileobj(response, handle, length=1024 * 1024)
        if dest.stat().st_size != end - start + 1:
            raise RuntimeError('Incomplete weight segment')
        print(f'Weight segment {index + 1}/8 downloaded', flush=True)
        return dest
    with ThreadPoolExecutor(max_workers=8) as pool:
        parts = list(pool.map(part, range(8)))
    assembled = path.with_suffix('.assembled')
    digest = hashlib.sha256()
    with assembled.open('wb') as target:
        for part_path in parts:
            with part_path.open('rb') as source:
                while block := source.read(1024 * 1024):
                    digest.update(block)
                    target.write(block)
    if digest.hexdigest() != expected_hash:
        raise RuntimeError('Model checksum mismatch')
    assembled.replace(path)


def main():
    with urlopen('https://huggingface.co/api/models/' + MODEL + '?blobs=true', timeout=30) as response:
        info = json.load(response)
    revision = info['sha']
    allowed = {'config.json', 'config_sentence_transformers.json', 'modules.json',
               'sentence_bert_config.json', 'special_tokens_map.json', 'tokenizer.json',
               'tokenizer_config.json', 'sentencepiece.bpe.model', '1_Pooling/config.json',
               'model.safetensors'}
    for item in info['siblings']:
        name = item['rfilename']
        if name not in allowed:
            continue
        path = TARGET / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            continue
        print('Downloading ' + name, flush=True)
        if name == 'model.safetensors':
            download_weights(f'https://huggingface.co/{MODEL}/resolve/{revision}/{name}',
                             path, item['lfs']['sha256'], item['size'])
            continue
        with urlopen(f'https://huggingface.co/{MODEL}/resolve/{revision}/{name}', timeout=60) as response:
            partial = path.with_suffix(path.suffix + '.partial')
            with partial.open('wb') as handle:
                shutil.copyfileobj(response, handle, length=1024 * 1024)
            expected = response.headers.get('Content-Length')
            if expected and partial.stat().st_size != int(expected):
                raise RuntimeError('Incomplete model file: ' + name)
            partial.replace(path)
    (TARGET / 'download_provenance.json').write_text(json.dumps({'model': MODEL, 'revision': revision}), encoding='utf-8')
    print('Local model ready: ' + str(TARGET), flush=True)


if __name__ == '__main__':
    main()
