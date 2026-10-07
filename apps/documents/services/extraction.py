import re

import pymupdf4llm

BR_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
HTML_TAG_RE = re.compile(r"</?(u|b|i|strong|em|span|sup|sub)[^>]*>", re.IGNORECASE)
PAGE_NUMBER_RE = re.compile(r"^\s*(page\s*)?\d{1,4}\s*$", re.IGNORECASE | re.MULTILINE)


def clean_page_text(text):
    text = BR_RE.sub(" ", text)
    text = HTML_TAG_RE.sub("", text)
    text = text.replace("**", "")
    text = PAGE_NUMBER_RE.sub("", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pages(pdf_path):
    """Return a list of {"page": int, "text": str}, with cleaned Markdown text per page."""
    page_data = pymupdf4llm.to_markdown(str(pdf_path), page_chunks=True)
    return [
        {"page": number, "text": clean_page_text(item.get("text") or "")}
        for number, item in enumerate(page_data, start=1)
    ]