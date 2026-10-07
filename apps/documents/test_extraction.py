from django.test import SimpleTestCase

from .services.extraction import clean_page_text


class CleaningTests(SimpleTestCase):
    def test_removes_formatting_and_page_numbers(self):
        raw = "# **<u>GDP ESTIMATES</u>**\n\n|a|line one<br>line two|\n\n3"
        self.assertEqual(clean_page_text(raw), "# GDP ESTIMATES\n\n|a|line one line two|")

    def test_keeps_numbers_inside_sentences_and_tables(self):
        raw = "Base year is 2011-12.\n\n|1|Crops|"
        self.assertEqual(clean_page_text(raw), raw)