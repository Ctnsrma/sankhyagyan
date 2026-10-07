from django.test import SimpleTestCase

from .services.chunking import chunk_pages, count_tokens


class ChunkingTests(SimpleTestCase):
    def test_sections_and_pages_are_tracked(self):
        pages = [
            {"page": 1, "text": "# Sampling\n\n" + "Random sampling explained. " * 40},
            {"page": 2, "text": "# Index Numbers\n\n" + "CPI measures prices. " * 40},
        ]
        chunks = chunk_pages(pages, max_tokens=600, min_tokens=50)
        self.assertEqual(chunks[0].section, "Sampling")
        self.assertEqual(chunks[-1].section, "Index Numbers")
        self.assertEqual(chunks[-1].page_start, 2)

    def test_chunks_respect_max_tokens(self):
        pages = [{"page": 1, "text": "\n\n".join(["Data quality matters. " * 20] * 30)}]
        chunks = chunk_pages(pages, max_tokens=300)
        self.assertTrue(len(chunks) > 1)
        for chunk in chunks:
            self.assertLessEqual(chunk.token_count, 300 + 20)

    def test_large_table_keeps_header_in_every_piece(self):
        header = "| State | Value |\n|---|---|"
        rows = "\n".join(f"| State{i} | {i * 10} |" for i in range(300))
        pages = [{"page": 1, "text": f"{header}\n{rows}"}]
        chunks = chunk_pages(pages, max_tokens=200)
        self.assertTrue(len(chunks) > 1)
        for chunk in chunks:
            self.assertIn("| State | Value |", chunk.text)