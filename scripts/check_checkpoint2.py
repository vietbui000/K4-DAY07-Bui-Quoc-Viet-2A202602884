"""Check CP2 structure locally; source permission/content still need human review.

Supports the flat, single-line metadata format produced by fetch_public_pages.py.
"""
import argparse
import csv
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


def metadata(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != '---':
        raise ValueError('missing opening front matter delimiter')
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == '---'), None)
    if end is None:
        raise ValueError('missing closing front matter delimiter')
    fields = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        match = re.fullmatch(r'([\w-]+):\s*(.*)', line)
        if not match:
            raise ValueError('use flat, single-line metadata: ' + line)
        key, raw = match.groups()
        if key in fields:
            raise ValueError('duplicate metadata: ' + key)
        if raw.startswith('"'):
            value, rest = json.JSONDecoder().raw_decode(raw)
            if rest < len(raw) and raw[rest:].strip() and not raw[rest:].lstrip().startswith('#'):
                raise ValueError('invalid quoted value: ' + key)
        elif raw.startswith("'"):
            quoted = re.fullmatch(r"'((?:''|[^'])*)'\s*(?:#.*)?", raw)
            if not quoted:
                raise ValueError('invalid quoted value: ' + key)
            value = quoted.group(1).replace("''", "'")
        else:
            value = re.split(r'\s+#', raw, maxsplit=1)[0].strip()
            if value in ('|', '>'):
                raise ValueError('multiline metadata is not supported: ' + key)
        fields[key] = value
    return fields, '\n'.join(lines[end + 1:]).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    failures = []

    def check(condition, message):
        print(('OK   ' if condition else 'FAIL ') + message)
        if not condition:
            failures.append(message)

    check(args.directory.is_dir(), 'corpus directory exists')
    files = sorted(args.directory.glob('*.md'))
    check(5 <= len(files) <= 10, f'document count: {len(files)} (required: 5-10)')
    docs = []
    required = ('doc_id', 'title', 'source_url', 'retrieved_at', 'document_version', 'audience')
    for path in files:
        try:
            fm, body = metadata(path.read_text(encoding='utf-8-sig'))
            missing = [key for key in required if not fm.get(key)]
            check(not missing, f'{path.name}: required metadata; missing={missing}')
            check(fm.get('doc_id') == path.stem, f'{path.name}: doc_id matches filename')
            check(fm.get('audience') in ('buyer', 'seller', 'both'), f'{path.name}: audience')
            check(any(v for k, v in fm.items() if k not in required and k != 'license_or_permission'),
                  f'{path.name}: additional filter field')
            url = urlparse(fm.get('source_url', ''))
            host = url.hostname or ''
            placeholder = any(host == d or host.endswith('.' + d) for d in ('example.com', 'example.org', 'example.net'))
            check(url.scheme in ('http', 'https') and bool(host) and not placeholder,
                  f'{path.name}: source URL format (not an example URL)')
            stamp = fm.get('retrieved_at', '')
            date.fromisoformat(stamp)
            check(bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}', stamp)), f'{path.name}: YYYY-MM-DD date')
            check(bool(body), f'{path.name}: nonempty content')
            docs.append((path, fm))
        except (ValueError, OSError) as exc:
            check(False, f'{path.name}: {exc}')
    ids = [fm.get('doc_id') for _, fm in docs]
    check(len(ids) == len(set(ids)), 'unique doc_id values')
    audiences = Counter(fm.get('audience') for _, fm in docs)
    check(len(set(audiences) & {'buyer', 'seller', 'both'}) >= 2, f'audience distribution: {dict(audiences)}')
    manifest = args.directory / 'sources.csv'
    try:
        with manifest.open(encoding='utf-8-sig', newline='') as handle:
            reader = csv.DictReader(handle)
            columns = {'doc_id', 'file_path', 'title', 'source_url', 'retrieved_at', 'document_version', 'license_or_permission'}
            check(columns <= set(reader.fieldnames or []), 'sources.csv: required columns')
            rows = list(reader)
        check(Counter(row.get('doc_id') for row in rows) == Counter(ids) and len(docs) == len(files),
              'sources.csv: one row per document')
        by_id = {fm.get('doc_id'): (path, fm) for path, fm in docs}
        for row in rows:
            entry = by_id.get(row.get('doc_id'))
            if entry is None:
                continue
            path, fm = entry
            check(all(row.get(k) == fm.get(k) for k in ('title', 'source_url', 'retrieved_at', 'document_version')),
                  f'{path.name}: CSV metadata matches document')
            check(Path(row.get('file_path') or '__missing__').resolve() == path.resolve(),
                  f'{path.name}: CSV file_path (relative to working directory)')
            check(bool((row.get('license_or_permission') or '').strip()), f'{path.name}: permission basis recorded')
    except (OSError, csv.Error) as exc:
        check(False, f'sources.csv: {exc}')
    print(f'\nStructural errors: {len(failures)}')
    print('Manual review required: source access/permission, faithful clean content, report section 1, and benchmark evidence.')
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
