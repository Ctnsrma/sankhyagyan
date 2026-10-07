import hashlib
import re
from dataclasses import dataclass

import tiktoken

ENCODER = tiktoken.get_encoding("cl100k_base")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)")


def count_tokens(text):
    return len(ENCODER.encode(text))


@dataclass
class Block:
    text: str
    page: int
    section: str
    tokens: int
    is_heading: bool = False


@dataclass
class ChunkData:
    text: str
    section: str
    page_start: int
    page_end: int
    token_count: int
    content_hash: str


def _split_by_sentences(text, max_tokens):
    sentences = re.split(r"(?<=[.!?])\s+", text)
    pieces, current = [], ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip()
        if current and count_tokens(candidate) > max_tokens:
            pieces.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        pieces.append(current)
    return pieces


def _split_table(text, max_tokens):
    lines = text.splitlines()
    header, rows = lines[:2], lines[2:]
    pieces, current = [], []
    for row in rows:
        if current and count_tokens("\n".join(header + current + [row])) > max_tokens:
            pieces.append("\n".join(header + current))
            current = [row]
        else:
            current.append(row)
    if current:
        pieces.append("\n".join(header + current))
    return pieces


def _build_blocks(pages, max_tokens):
    blocks, heading_path = [], []
    for page in pages:
        for raw in re.split(r"\n\s*\n", page["text"]):
            raw = raw.strip()
            if not raw:
                continue

            match = HEADING_RE.match(raw)
            is_heading = bool(match) and "\n" not in raw
            if is_heading:
                level = len(match.group(1))
                title = match.group(2).strip("* ").strip()
                heading_path = heading_path[: level - 1] + [title]

            section = " > ".join(heading_path)
            pieces = [raw]
            if count_tokens(raw) > max_tokens:
                splitter = _split_table if raw.startswith("|") else _split_by_sentences
                pieces = splitter(raw, max_tokens)

            for piece in pieces:
                blocks.append(Block(piece, page["page"], section, count_tokens(piece), is_heading))
    return blocks


def chunk_pages(pages, max_tokens=600, overlap_tokens=80, min_tokens=150):
    blocks = _build_blocks(pages, max_tokens)
    chunks, current = [], []

    def current_tokens():
        return sum(b.tokens for b in current)

    def flush():
        text = "\n\n".join(b.text for b in current)
        chunks.append(ChunkData(
            text=text,
            section=current[0].section,
            page_start=current[0].page,
            page_end=current[-1].page,
            token_count=count_tokens(text),
            content_hash=hashlib.sha256(text.encode()).hexdigest(),
        ))

    for block in blocks:
        if block.is_heading and current_tokens() >= min_tokens:
            flush()
            current = []
        elif current and current_tokens() + block.tokens > max_tokens:
            flush()
            overlap, total = [], 0
            for prev in reversed(current):
                if total + prev.tokens > overlap_tokens:
                    break
                overlap.insert(0, prev)
                total += prev.tokens
            current = overlap
        current.append(block)

    if current:
        flush()
    return chunks