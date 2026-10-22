"""Run from project root: python -m unittest discover -s tests -v"""
import unittest
from pathlib import Path
from extract_science_bowl import parse_questions

class ExtractorTests(unittest.TestCase):
    def test_tossup_and_bonus(self):
        text = """TOSS-UP
1. PHYSICS Short Answer What is the SI unit for electric current?
ANSWER: ampere
BONUS
1. BIOLOGY Multiple Choice What organelle produces most cellular ATP?
W) Nucleus
X) Mitochondrion
Y) Ribosome
Z) Lysosome
ANSWER: X) Mitochondrion"""
        lines = [(line, 1) for line in text.splitlines()]
        rows = parse_questions(lines, set(), Path('2025 Demo/Round 1.pdf'), text)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['category'], 'Physics')
        self.assertEqual(rows[0]['answer'], 'ampere')
        self.assertEqual(rows[1]['type'], 'Bonus')
        self.assertEqual(rows[1]['choice_x'], 'Mitochondrion')
        self.assertEqual(rows[1]['needs_review'], False)

if __name__ == '__main__':
    unittest.main()
