"""Gemini REST adapter. Never falls back to mock and never logs credentials."""
import json
import math
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class GeminiRuntime:
    def __init__(self):
        self.key = (os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY') or '').strip()
        if not self.key or self.key in ('your-key-here', 'PASTE_YOUR_KEY_HERE'):
            raise ValueError('Missing GEMINI_API_KEY: configure .env locally. No mock fallback.')
        self.embedding_model = os.getenv('GEMINI_EMBEDDING_MODEL', 'gemini-embedding-2')
        self.llm_model = os.getenv('GEMINI_LLM_MODEL', 'gemini-3.8-flash')
        for model in (self.embedding_model, self.llm_model):
            if not re.fullmatch(r'[a-zA-Z0-9._-]+', model):
                raise ValueError('Use a bare Gemini model ID in .env (without models/).')
        self.cache = {}

    def _post(self, model, method, payload):
        request = Request(
            f'https://generativelanguage.googleapis.com/v1beta/models/{model}:{method}',
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'x-goog-api-key': self.key},
            method='POST',
        )
        try:
            with urlopen(request, timeout=45) as response:
                return json.load(response)
        except HTTPError as exc:
            # Do not include server bodies or request headers: they may contain credentials.
            raise RuntimeError(f'Gemini HTTP {exc.code}: check key, model access and quota. No mock fallback.') from None
        except (URLError, TimeoutError, OSError):
            raise RuntimeError('Cannot connect to Gemini API. Check network access; no mock fallback.') from None

    def embed(self, text):
        if text not in self.cache:
            result = self._post(self.embedding_model, 'embedContent', {
                'model': f'models/{self.embedding_model}',
                'content': {'parts': [{'text': text}]},
            })
            values = [float(v) for v in result['embedding']['values']]
            norm = math.hypot(*values)
            if not values or not math.isfinite(norm) or norm == 0:
                raise ValueError('Gemini returned an invalid embedding')
            # Store uses dot product; unit vectors make scores cosine similarities.
            self.cache[text] = [v / norm for v in values]
        return list(self.cache[text])

    def generate(self, prompt):
        result = self._post(self.llm_model, 'generateContent', {
            'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
            'systemInstruction': {'parts': [{'text': 'Trả lời bằng tiếng Việt. Chỉ dùng ngữ cảnh được cung cấp, dẫn nguồn [1], [2]. Nếu thiếu bằng chứng, nói rõ không đủ thông tin.'}]},
            'generationConfig': {'temperature': 0, 'maxOutputTokens': 4096},
        })
        candidates = result.get('candidates') or []
        if not candidates or candidates[0].get('finishReason') != 'STOP':
            raise RuntimeError('Gemini did not produce a complete answer (blocked/truncated).')
        answer = '\n'.join(part.get('text', '') for part in
                           candidates[0].get('content', {}).get('parts', [])
                           if not part.get('thought')).strip()
        if not answer:
            raise RuntimeError('Gemini returned no answer; no mock fallback.')
        return answer
