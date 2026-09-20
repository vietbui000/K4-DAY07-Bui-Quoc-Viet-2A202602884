"""Groq generation with local multilingual embeddings; no mock fallback."""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .embeddings import LocalEmbedder, LOCAL_EMBEDDING_MODEL


class GroqRuntime:
    def __init__(self):
        self.key = os.getenv('GROQ_API_KEY', '').strip()
        if not self.key:
            raise ValueError('Missing GROQ_API_KEY in .env')
        self.llm_model = os.getenv('GROQ_LLM_MODEL', 'openai/gpt-oss-20b')
        self.embedding_model = os.getenv('LOCAL_EMBEDDING_MODEL', LOCAL_EMBEDDING_MODEL)
        self.local = None
        self.cache = {}

    def _request(self, endpoint, payload=None):
        req = Request('https://api.groq.com/openai/v1/' + endpoint,
                      data=None if payload is None else json.dumps(payload).encode('utf-8'),
                      headers={'Authorization': 'Bearer ' + self.key,
                               'Content-Type': 'application/json', 'User-Agent': 'LazadaLab/1.0'})
        try:
            with urlopen(req, timeout=45) as response:
                return json.load(response)
        except HTTPError as exc:
            raise RuntimeError(f'Groq HTTP {exc.code}: check Groq key, model access and quota. No mock fallback.') from None
        except (URLError, TimeoutError, OSError):
            raise RuntimeError('Cannot connect to Groq API; no mock fallback.') from None

    def check_access(self):
        models = self._request('models')
        if self.llm_model not in {m['id'] for m in models.get('data', [])}:
            raise ValueError('GROQ_LLM_MODEL is not available to this account')

    def embed(self, text):
        if self.local is None:
            try:
                self.local = LocalEmbedder(self.embedding_model)
            except ImportError:
                raise RuntimeError('Install local embeddings: python -m pip install -r requirements-local.txt') from None
        if text not in self.cache:
            self.cache[text] = self.local(text)
        return list(self.cache[text])

    def generate(self, prompt):
        response = self._request('chat/completions', {
            'model': self.llm_model, 'temperature': 0, 'max_completion_tokens': 2048,
            'messages': [
                {'role': 'system', 'content': 'Trả lời bằng tiếng Việt, chỉ dùng ngữ cảnh và dẫn nguồn [1], [2]. Nói rõ nếu thiếu bằng chứng.'},
                {'role': 'user', 'content': prompt},
            ],
        })
        choices = response.get('choices') or []
        if not choices or choices[0].get('finish_reason') != 'stop':
            raise RuntimeError('Groq answer missing, blocked or truncated')
        answer = choices[0].get('message', {}).get('content')
        if not answer or not answer.strip():
            raise RuntimeError('Groq returned an empty answer')
        return answer.strip()
