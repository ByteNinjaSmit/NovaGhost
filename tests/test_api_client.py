"""
Tests for API client response parsing, JSON extraction, and fallback mechanisms.
"""

import unittest
from engine.schemas import AssessmentFormat
from network.api_client import parse_structured_json, parse_fallback_text


class TestApiClientParsing(unittest.TestCase):
    def test_direct_json_parsing(self):
        raw = '{"question_category": "numerical_aptitude", "option_label": "B", "full_answer": "125"}'
        res = parse_structured_json(raw)
        self.assertIsNotNone(res)
        self.assertEqual(res["option_label"], "B")

    def test_markdown_code_block_parsing(self):
        raw = """Here is the analysis:
```json
{
  "question_category": "non_verbal_reasoning",
  "assessment_format": "IMAGE_OPTIONS",
  "option_label": "Option 2",
  "position_from_left": "2nd from LEFT"
}
```
"""
        res = parse_structured_json(raw)
        self.assertIsNotNone(res)
        self.assertEqual(res["option_label"], "Option 2")
        self.assertEqual(res["position_from_left"], "2nd from LEFT")

    def test_json_with_trailing_comma(self):
        raw = '{"question_category": "logical_reasoning", "full_answer": "Valid",}'
        res = parse_structured_json(raw)
        self.assertIsNotNone(res)
        self.assertEqual(res["full_answer"], "Valid")

    def test_fallback_numerical(self):
        raw = "1250.50"
        ans = parse_fallback_text(raw)
        self.assertEqual(ans.assessment_format, AssessmentFormat.NAT)
        self.assertEqual(ans.numerical_value, "1250.50")

    def test_fallback_option_text(self):
        raw = "Option C: 125"
        ans = parse_fallback_text(raw)
        self.assertEqual(ans.option_label, "C")
        self.assertIn("125", ans.full_answer)

    def test_fallback_unclear(self):
        raw = "Screenshot is unclear and cannot read text."
        ans = parse_fallback_text(raw)
        self.assertTrue(ans.needs_clarification)


if __name__ == "__main__":
    unittest.main()
