"""
Tests for specialized solvers and answer validator.
"""

import unittest
from engine.schemas import QuestionCategory, AssessmentFormat
from engine.solvers.numerical_solver import NumericalSolver
from engine.solvers.data_interpretation_solver import DataInterpretationSolver
from engine.solvers.figure_series_solver import FigureSeriesSolver
from engine.solvers.figure_matrix_solver import FigureMatrixSolver
from engine.solvers.visual_reasoning_solver import VisualReasoningSolver
from engine.solvers.logical_reasoning_solver import LogicalReasoningSolver
from engine.solvers.verbal_reasoning_solver import VerbalReasoningSolver
from engine.solvers.technical_mcq_solver import TechnicalMcqSolver
from engine.solvers.answer_validator import AnswerValidator


class TestSolvers(unittest.TestCase):
    def test_numerical_arithmetic_verifier(self):
        val = NumericalSolver.verify_arithmetic("(30 / 130) * 100")
        self.assertAlmostEqual(val, 23.076923, places=4)

        val2 = NumericalSolver.verify_arithmetic("1000 * (1 + 0.10)**2")
        self.assertEqual(val2, 1210.0)

        # Invalid characters should be stripped safely
        val3 = NumericalSolver.verify_arithmetic("Salary is 450 + 50")
        self.assertEqual(val3, 500.0)

    def test_numerical_post_process_nat(self):
        data = {
            "question_category": "numerical_aptitude",
            "assessment_format": "NAT",
            "numerical_value": "1250.50",
            "full_answer": "1250.50",
            "confidence": 0.99
        }
        ans = NumericalSolver.post_process(data)
        self.assertEqual(ans.assessment_format, AssessmentFormat.NAT)
        self.assertEqual(ans.numerical_value, "1250.50")
        self.assertIn("1250.50", ans.to_strict_format())

    def test_data_interpretation_post_process(self):
        data = {
            "question_category": "data_interpretation",
            "subcategory": "Bar Graph",
            "assessment_format": "MCQ",
            "option_label": "B",
            "full_answer": "45.75",
            "confidence": 0.98
        }
        ans = DataInterpretationSolver.post_process(data)
        out = ans.to_strict_format()
        self.assertEqual(out, "CORRECT OPTION: B\n\nFULL ANSWER: 45.75")

    def test_figure_series_positioning(self):
        data = {
            "option_label": "Option 2",
            "option_index": 1,
            "total_options": 4,
            "orientation": "horizontal"
        }
        ans = FigureSeriesSolver.post_process(data)
        self.assertEqual(ans.position_from_left, "2nd from LEFT")
        self.assertEqual(ans.position_from_right, "3rd from RIGHT")
        out = ans.to_strict_format()
        self.assertIn("CORRECT ANSWER: OPTION 2", out)
        self.assertIn("POSITION: 2nd from LEFT", out)
        self.assertIn("POSITION FROM RIGHT: 3rd from RIGHT", out)

    def test_figure_matrix_grid(self):
        data = {
            "option_label": "Option 3",
            "option_index": 2,
            "total_options": 4,
            "orientation": "grid",
            "grid_row": 1,
            "grid_col": 2
        }
        ans = FigureMatrixSolver.post_process(data)
        out = ans.to_strict_format()
        self.assertIn("CORRECT ANSWER: OPTION 3", out)
        self.assertIn("GRID POSITION: ROW 1, COLUMN 2", out)

    def test_technical_msq_post_process(self):
        data = {
            "assessment_format": "MSQ",
            "selected_options": ["A", "C"],
            "full_answer": "Atomicity and Consistency"
        }
        ans = TechnicalMcqSolver.post_process(data)
        self.assertEqual(ans.assessment_format, AssessmentFormat.MSQ)
        out = ans.to_strict_format()
        self.assertIn("CORRECT OPTIONS: A, C", out)
        self.assertIn("SELECT: A and C", out)

    def test_answer_validator_low_confidence(self):
        from engine.schemas import StructuredAnswer
        ans = StructuredAnswer(confidence=0.25)
        validated = AnswerValidator.validate_and_refine(ans)
        self.assertTrue(validated.needs_clarification)
        self.assertIn("SCREENSHOT UNCLEAR", validated.to_strict_format())

    def test_answer_validator_low_res_flag(self):
        from engine.schemas import StructuredAnswer
        ans = StructuredAnswer(full_answer="42")
        quality = {"is_clear": False, "warning": "Resolution is too low"}
        validated = AnswerValidator.validate_and_refine(ans, quality_metadata=quality)
        self.assertTrue(validated.needs_clarification)
        self.assertIn("Resolution is too low", validated.to_strict_format())


if __name__ == "__main__":
    unittest.main()
