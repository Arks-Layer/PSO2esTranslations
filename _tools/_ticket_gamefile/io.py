"""Internal gamefile I/O helpers; not an entry point.

Shared by the F/T tools. JP downloads stay in memory; replacements
preserve the untouched lines of local text.ini/CSV files byte-for-byte.
"""

import csv
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
import io
import os
from pathlib import Path
import re
import stat
import tempfile

from .rules import strip_series_suffix


@contextmanager
def web_pages(urls, get_web, report):
    with ThreadPoolExecutor(max_workers=8) as executor:
        pages = {}
        for url in dict.fromkeys(urls):
            messages = []
            future = executor.submit(get_web, url, lambda status, message, log=messages: log.append((status, message)))

            # Resolve on the caller thread to preserve log order and error handling.
            def read(future=future, messages=messages):
                try:
                    return future.result()
                finally:
                    for status, message in messages:
                        report(status, message)
                    messages.clear()

            pages[url] = read
        yield pages


def decode_text(value):
    return value.replace(r'\u3000', '　').replace(r'\"', '"')


# Native CSV cells contain an extra pair of quotes inside the CSV quoting.
def csv_value(value):
    escaped = value.replace('"', r'\"').replace('　', r'\u3000')
    stream = io.StringIO(newline='')
    csv.writer(stream, lineterminator='').writerow(['"' + escaped + '"'])
    return stream.getvalue()


@dataclass(frozen=True)
class Entry:
    key: str
    text: str
    line: int
    prefix: str
    ending: str


class GameFile:
    def __init__(self, path, kind, japanese_keys=(), series_aliases=False):
        self.path = Path(path).resolve()
        self.source = str(self.path)
        self._parse(self.path.read_bytes(), kind, japanese_keys, series_aliases)

    # In-memory sources (including JP downloads) are read-only.
    @classmethod
    def from_bytes(cls, content, source, kind='csv', japanese_keys=(), series_aliases=False):
        file = cls.__new__(cls)
        file.path = None
        file.source = source
        file._parse(content, kind, japanese_keys, series_aliases)
        return file

    def _parse(self, content, kind, japanese_keys, series_aliases):
        self.kind = kind
        self.original = content
        self.bom = self.original.startswith(b'\xef\xbb\xbf')
        self.lines = self.original.decode('utf-8-sig').splitlines(keepends=True)
        self.entries = {}
        self.ambiguous = set()
        known = set(japanese_keys)
        for number, line in enumerate(self.lines):
            body = line.rstrip('\r\n')
            ending = line[len(body):]
            if not body:
                continue
            if kind == 'csv':
                try:
                    row = next(csv.reader([body], strict=True))
                except csv.Error as error:
                    raise ValueError(f'{self.source}:{number + 1}: {error}') from error
                if len(row) != 2 or len(row[1]) < 2 or not row[1].startswith('"') or not row[1].endswith('"'):
                    raise ValueError(f'{self.source}:{number + 1}: expected ID and quoted game text')
                key = row[0]
                prefix = body[:body.index(',') + 1]
                self._add(Entry(key, decode_text(row[1][1:-1]), number, prefix, ending))
                continue
            if kind != 'ini':
                raise ValueError(f'Unknown gamefile format: {kind}')
            if series_aliases and body.startswith(';') and '=' in body:
                key, value = body.split('=', 1)
                self._add(Entry(key, value, number, key + '=', ending))
            elif not body.startswith((';', '#')):
                # JP keys can contain '='. An ambiguous boundary must not be guessed.
                matches = [(pos, decode_text(body[:pos]))
                           for pos, char in enumerate(body) if char == '='
                           and decode_text(body[:pos]) in known]
                if len(matches) > 1:
                    self.ambiguous.update(key for _, key in matches)
                elif matches:
                    pos, key = matches[0]
                    self._add(Entry(key, body[pos + 1:], number, body[:pos + 1], ending))

    def _add(self, entry):
        if entry.key in self.entries:
            self.ambiguous.add(entry.key)
        else:
            self.entries[entry.key] = entry

    @property
    def pairs(self):
        return [(entry.key, entry.text) for entry in self.entries.values()
                if entry.key not in self.ambiguous]

    def render(self, replacements):
        lines = list(self.lines)
        for key, value in replacements.items():
            if key in self.ambiguous or key not in self.entries:
                raise ValueError(f'{self.source}: missing or ambiguous target {key!r}')
            if '\n' in value or '\r' in value or '\x00' in value:
                raise ValueError(f'{self.source}: a game text value cannot contain a physical line break or NUL')
            entry = self.entries[key]
            if entry.text == value:
                continue
            encoded = csv_value(value) if self.kind == 'csv' else value
            lines[entry.line] = entry.prefix + encoded + entry.ending
        result = ''.join(lines).encode('utf-8')
        return (b'\xef\xbb\xbf' if self.bom else b'') + result

    # Replace complete content atomically so an interrupted write cannot truncate
    # a gamefile. The temporary file is removed on both success and failure.
    def write(self, content):
        if self.path is None:
            raise ValueError('In-memory sources cannot be written')
        if self.path.read_bytes() != self.original:
            raise ValueError(f'Gamefile changed during generation: {self.path}')
        if content == self.original:
            return False
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.path.parent, prefix=f'.{self.path.name}.',
                                             suffix='.tmp', delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(content)
            os.chmod(temporary, stat.S_IMODE(self.path.stat().st_mode))
            if self.path.read_bytes() != self.original:
                raise ValueError(f'Gamefile changed during generation: {self.path}')
            os.replace(temporary, self.path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return True


def preserve_padding(text, value):
    start = len(text) - len(text.lstrip())
    end = max(start, len(text.rstrip()))
    return text[:start] + value.strip() + text[end:]


def strip_ring_name(text):
    return text.split('<br>', 1)[0].replace('／リング', '').replace('/リング', '').strip()


def replace_ring_name(text, name, preserve_suffix=True):
    first, separator, rest = text.partition('<br>')
    suffix = re.search(r'(?:／リング|/リング)\s*$', first) if preserve_suffix else None
    base = first[:suffix.start()] if suffix else first
    return preserve_padding(base, name) + (suffix.group() if suffix else '') + separator + rest


def replace_series_name(text, name, lang):
    notes = ''.join(re.findall(r'[（(]\s*原名[:：].*?[）)]', text))
    if lang in ('KO', 'RU'):
        # Retain the existing localized prefix/suffix rather than inventing one.
        plain = re.sub(r'[（(]\s*原名[:：].*?[）)]', '', text)
        base = strip_series_suffix(plain)
        if base and base != plain:
            before, _, after = plain.partition(base)
            return before + name + notes + after
        return name + notes
    return name + notes + ('系列' if lang == 'CN' else ' Series')
