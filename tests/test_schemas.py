"""
Tests for schemas, positioning logic, and strict output formatting.
"""

import unittest
from engine.schemas import (
    QuestionCategory, AssessmentFormat, StructuredAnswer,
    ordinal_str, compute_positions
)


class TestSchemasAndFormatting(unittest.TestCase):
    def test_ordinal_str(self):
        self.assertEqual(ordinal_str(1), "1st")
        self.assertEqual(ordinal_str(2), "2nd")
        self.assertEqual(ordinal_str(3), "3rd")
        self.assertEqual(ordinal_str(4), "4th")
        self.assertEqual(ordinal_str(11), "11th")
        self.assertEqual(ordinal_str(12), "12th")
        self.assertEqual(ordinal_str(13), "13th")
        self.assertEqual(ordinal_str(21), "21st")
        self.assertEqual(ordinal_str(22), "22nd")
        self.assertEqual(ordinal_str(23), "23rd")

    def test_compute_positions_horizontal(self):
        # 4 options, 2nd option (index 1)
        pos = compute_positions(index=1, total=4, orientation="horizontal")
        self.assertEqual(pos["position_from_left"], "2nd from LEFT")
        self.assertEqual(pos["position_from_right"], "3rd from RIGHT")

        # 4 options, 1st option (index 0)
        pos0 = compute_positions(index=0, total=4, orientation="horizontal")
        self.assertEqual(pos0["position_from_left"], "1st from LEFT")
        self.assertEqual(pos0["position_from_right"], "4th from RIGHT")

        # 4 options, 4th option (index 3)
        pos3 = compute_positions(index=3, total=4, orientation="horizontal")
        self.assertEqual(pos3["position_from_left"], "4th from LEFT")
        self.assertEqual(pos3["position_from_right"], "1st from RIGHT")

    def test_compute_positions_vertical(self):
        pos_top = compute_positions(index=0, total=3, orientation="vertical")
        self.assertEqual(pos_top["vertical_position"], "TOP")

        pos_mid = compute_positions(index=1, total=3, orientation="vertical")
        self.assertEqual(pos_mid["vertical_position"], "MIDDLE")

        pos_bot = compute_positions(index=2, total=3, orientation="vertical")
        self.assertEqual(pos_bot["vertical_position"], "BOTTOM")

    def test_compute_positions_grid(self):
        # 2x2 grid, index 1 -> Row 1, Column 2
        pos = compute_positions(index=1, total=4, orientation="grid", grid_rows=2, grid_cols=2)
        self.assertEqual(pos["grid_position"], "ROW 1, COLUMN 2")

        # 3x3 grid, index 4 (center) -> Row 2, Column 2
        pos_center = compute_positions(index=4, total=9, orientation="grid", grid_rows=3, grid_cols=3)
        self.assertEqual(pos_center["grid_position"], "ROW 2, COLUMN 2")

    def test_format_a_labeled_image(self):
        ans = StructuredAnswer(
            question_category=QuestionCategory.NON_VERBAL_REASONING,
            assessment_format=AssessmentFormat.IMAGE_OPTIONS,
            is_image_options=True,
            option_label="OPTION 2",
            option_index=1,
            total_options=4,
            full_answer="Option 2 – Second image from the left"
        )
        out = ans.to_strict_format()
        self.assertIn("CORRECT ANSWER: OPTION 2", out)
        self.assertIn("POSITION: 2nd from LEFT", out)
        self.assertIn("POSITION FROM RIGHT: 3rd from RIGHT", out)

    def test_format_b_unlabeled_image(self):
        ans = StructuredAnswer(
            question_category=QuestionCategory.NON_VERBAL_REASONING,
            assessment_format=AssessmentFormat.IMAGE_OPTIONS,
            is_image_options=True,
            option_label=None,
            option_index=1,
            total_options=4
        )
        out = ans.to_strict_format()
        self.assertIn("CORRECT ANSWER: 2nd from LEFT", out)
        self.assertIn("POSITION: 3rd from RIGHT", out)

    def test_format_c_mcq(self):
        ans = StructuredAnswer(
            question_category=QuestionCategory.LOGICAL_REASONING,
            assessment_format=AssessmentFormat.MCQ,
            option_label="C",
            full_answer="125"
        )
        out = ans.to_strict_format()
        self.assertEqual(out, "CORRECT OPTION: C\n\nFULL ANSWER: 125")

    def test_format_d_nat(self):
        ans = StructuredAnswer(
            question_category=QuestionCategory.NUMERICAL_APTITUDE,
            assessment_format=AssessmentFormat.NAT,
            numerical_value="1250.50"
        )
        out = ans.to_strict_format()
        self.assertEqual(out, "ENTER THIS VALUE:\n\n1250.50")

    def test_format_e_msq(self):
        ans = StructuredAnswer(
            question_category=QuestionCategory.TECHNICAL_KNOWLEDGE,
            assessment_format=AssessmentFormat.MSQ,
            selected_options=["A", "C"],
            full_answer="A and C"
        )
        out = ans.to_strict_format()
        self.assertIn("CORRECT OPTIONS: A, C", out)
        self.assertIn("SELECT: A and C", out)

    def test_format_f_data_interpretation(self):
        ans = StructuredAnswer(
            question_category=QuestionCategory.DATA_INTERPRETATION,
            assessment_format=AssessmentFormat.MCQ,
            option_label="B",
            full_answer="45.75"
        )
        out = ans.to_strict_format()
        self.assertEqual(out, "CORRECT OPTION: B\n\nFULL ANSWER: 45.75")

    def test_format_g_unclear(self):
        ans = StructuredAnswer(
            needs_clarification=True,
            missing_information="Chart axis label and legends are unreadable"
        )
        out = ans.to_strict_format()
        self.assertIn("SCREENSHOT UNCLEAR", out)
        self.assertIn("MISSING INFORMATION: Chart axis label and legends are unreadable", out)
        self.assertIn("REQUEST: Upload a clearer screenshot.", out)


if __name__ == "__main__":
    unittest.main()
