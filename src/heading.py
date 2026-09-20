"""Heading-aware policy chunks with repeated section context for long sections."""
import re

from .chunking import RecursiveChunker


class HeadingChunker:
    def __init__(self, chunk_size: int = 500):
        if chunk_size <= 0:
            raise ValueError('chunk_size must be positive')
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        sections, parents, body = [], [], []

        def flush():
            content = ''.join(body).strip()
            prefix = '\n'.join(line for _, line in parents)
            if not content and not prefix:
                return
            whole = '\n'.join(part for part in (prefix, content) if part)
            if len(whole) <= self.chunk_size:
                sections.append(whole)
            elif len(prefix) + 1 < self.chunk_size and content:
                budget = self.chunk_size - len(prefix) - 1
                sections.extend(prefix + '\n' + part for part in
                                RecursiveChunker(chunk_size=budget).chunk(content))
            else:
                # Extremely long heading: preserve all text with a hard fallback.
                sections.extend(RecursiveChunker(chunk_size=self.chunk_size).chunk(whole))

        in_fence = False
        for line in text.splitlines(keepends=True):
            if line.lstrip().startswith(('```', '~~~')):
                in_fence = not in_fence
            heading = re.match(r'^(#{1,6})\s+\S.*', line) if not in_fence else None
            if heading:
                flush()
                body = []
                level = len(heading.group(1))
                parents = [(depth, title) for depth, title in parents if depth < level]
                parents.append((level, line.strip()))
            else:
                body.append(line)
        flush()
        return sections
