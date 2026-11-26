"""
Tests for Multi-Question Detection and MultiQuestionResult handling.
"""

import unittest
from engine.schemas import (
    StructuredAnswer, MultiQuestionResult, QuestionCategory, AssessmentFormat
)


class TestMultiQuestion(unittest.TestCase):
    def test_single_question_result(self):
        ans = StructuredAnswer(
            question_category=QuestionCategory.NUMERICAL_APTITUDE,
            assessment_format=AssessmentFormat.MCQ,
            option_label="B",
            full_answer="23.07%"
        )
        multi = MultiQuestionResult(questions=[ans])
        self.assertFalse(multi.is_multi_question)
        formatted = multi.to_strict_format()
        self.assertEqual(formatted, "CORRECT OPTION: B\n\nFULL ANSWER: 23.07%")

    def test_multi_question_formatting(self):
        q1 = StructuredAnswer(
            question_category=QuestionCategory.DATA_INTERPRETATION,
            assessment_format=AssessmentFormat.MCQ,
            option_label="B",
            full_answer="45.75"
        )
        q2 = StructuredAnswer(
            question_category=QuestionCategory.DATA_INTERPRETATION,
            assessment_format=AssessmentFormat.MCQ,
            option_label="D",
            full_answer="120.00"
        )
        q3 = StructuredAnswer(
            question_category=QuestionCategory.DATA_INTERPRETATION,
            assessment_format=AssessmentFormat.NAT,
            numerical_value="18"
        )

        multi = MultiQuestionResult(questions=[q1, q2, q3])
        self.assertTrue(multi.is_multi_question)
        self.assertEqual(len(multi.questions), 3)

        # Individual question formatting
        fmt_q1 = multi.to_strict_format(0)
        self.assertIn("QUESTION 1 OF 3", fmt_q1)
        self.assertIn("CORRECT OPTION: B", fmt_q1)

        fmt_q2 = multi.to_strict_format(1)
        self.assertIn("QUESTION 2 OF 3", fmt_q2)
        self.assertIn("CORRECT OPTION: D", fmt_q2)

        # Combined formatting
        fmt_all = multi.to_strict_format(None)
        self.assertIn("QUESTION 1 OF 3", fmt_all)
        self.assertIn("QUESTION 2 OF 3", fmt_all)
        self.assertIn("QUESTION 3 OF 3", fmt_all)
        self.assertIn("ENTER THIS VALUE:\n\n18", fmt_all)


if __name__ == "__main__":
    unittest.main()
