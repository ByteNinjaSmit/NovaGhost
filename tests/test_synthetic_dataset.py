"""
NovaGhost — Comprehensive Synthetic Dataset Verification.
Generates 25+ diverse, labeled aptitude questions across:
- Numerical Aptitude (Percentages, Profit & Loss, Series, NAT)
- Data Interpretation (Bar, Pie, Table)
- Non-Verbal Reasoning (Figure Series 8->9, Figure Matrix, Mirror, Water, Paper Folding, Embedded, Odd One Out)
- Logical Reasoning (Blood Relations, Direction Sense, Seating, Syllogisms, Coding-Decoding)
- English & Verbal (Reading Comprehension, Synonyms, Grammar)
- Technical MCQs (DBMS SQL, Operating Systems, Computer Networks, MSQ)
- Unclear screenshot detection
Measures and reports actual test accuracy.
"""

import unittest
from engine.schemas import QuestionCategory, AssessmentFormat, StructuredAnswer
from engine.question_classifier import QuestionClassifier
from engine.solvers.numerical_solver import NumericalSolver
from engine.solvers.data_interpretation_solver import DataInterpretationSolver
from engine.solvers.figure_series_solver import FigureSeriesSolver
from engine.solvers.figure_matrix_solver import FigureMatrixSolver
from engine.solvers.visual_reasoning_solver import VisualReasoningSolver
from engine.solvers.logical_reasoning_solver import LogicalReasoningSolver
from engine.solvers.verbal_reasoning_solver import VerbalReasoningSolver
from engine.solvers.technical_mcq_solver import TechnicalMcqSolver
from engine.solvers.answer_validator import AnswerValidator


# 25 Labeled Synthetic Evaluation Cases
SYNTHETIC_DATASET = [
    # 1. Numerical Aptitude: Percentage
    {
        "id": "CASE_01_NUM_PERCENT",
        "text": "If A's salary is 30% more than B's salary, then by what percentage is B's salary less than A?",
        "expected_category": QuestionCategory.NUMERICAL_APTITUDE,
        "expected_subcat": "Percentages",
        "format": AssessmentFormat.MCQ,
        "input_data": {"option_label": "B", "full_answer": "23.07%", "option_index": 1, "confidence": 0.99},
        "solver": NumericalSolver,
        "expected_format_keyword": "CORRECT OPTION: B"
    },
    # 2. Numerical Aptitude: Profit & Loss
    {
        "id": "CASE_02_NUM_PROFIT_LOSS",
        "text": "Find the cost price if a book is sold at 15% profit for Rs. 460.",
        "expected_category": QuestionCategory.NUMERICAL_APTITUDE,
        "expected_subcat": "Profit and Loss",
        "format": AssessmentFormat.MCQ,
        "input_data": {"option_label": "C", "full_answer": "Rs. 400", "option_index": 2, "confidence": 0.99},
        "solver": NumericalSolver,
        "expected_format_keyword": "CORRECT OPTION: C"
    },
    # 3. Numerical Aptitude: NAT
    {
        "id": "CASE_03_NUM_NAT",
        "text": "Numerical Answer Type: Compute the compound interest on Rs. 10000 at 10% per annum for 2 years.",
        "expected_category": QuestionCategory.NUMERICAL_APTITUDE,
        "expected_subcat": "Simple / Compound Interest",
        "format": AssessmentFormat.NAT,
        "input_data": {"assessment_format": "NAT", "numerical_value": "2100.00", "full_answer": "2100.00", "confidence": 0.99},
        "solver": NumericalSolver,
        "expected_format_keyword": "ENTER THIS VALUE:\n\n2100.00"
    },
    # 4. Numerical Aptitude: Number Series
    {
        "id": "CASE_04_NUM_SERIES",
        "text": "Find the next missing number in the number series: 2, 6, 12, 20, 30, ?",
        "expected_category": QuestionCategory.NUMERICAL_APTITUDE,
        "expected_subcat": "Number Series",
        "format": AssessmentFormat.MCQ,
        "input_data": {"option_label": "D", "full_answer": "42", "option_index": 3, "confidence": 0.99},
        "solver": NumericalSolver,
        "expected_format_keyword": "CORRECT OPTION: D"
    },
    # 5. Data Interpretation: Bar Chart
    {
        "id": "CASE_05_DI_BAR_CHART",
        "text": "Study the following bar graph. What is the difference between females in organisation B and organisation E?",
        "expected_category": QuestionCategory.DATA_INTERPRETATION,
        "expected_subcat": "Bar Graph",
        "format": AssessmentFormat.MCQ,
        "input_data": {"option_label": "B", "full_answer": "45.75", "option_index": 1, "confidence": 0.98},
        "solver": DataInterpretationSolver,
        "expected_format_keyword": "CORRECT OPTION: B\n\nFULL ANSWER: 45.75"
    },
    # 6. Data Interpretation: Pie Chart
    {
        "id": "CASE_06_DI_PIE_CHART",
        "text": "Study the following pie chart showing expenditure breakdown. Find total expenditure on education.",
        "expected_category": QuestionCategory.DATA_INTERPRETATION,
        "expected_subcat": "Pie Chart",
        "format": AssessmentFormat.MCQ,
        "input_data": {"option_label": "A", "full_answer": "18%", "option_index": 0, "confidence": 0.98},
        "solver": DataInterpretationSolver,
        "expected_format_keyword": "CORRECT OPTION: A"
    },
    # 7. Data Interpretation: Table Data
    {
        "id": "CASE_07_DI_TABLE",
        "text": "Study the following table data showing sales of 4 branches across 4 quarters.",
        "expected_category": QuestionCategory.DATA_INTERPRETATION,
        "expected_subcat": "Table Data",
        "format": AssessmentFormat.MCQ,
        "input_data": {"option_label": "C", "full_answer": "320 lakhs", "option_index": 2, "confidence": 0.97},
        "solver": DataInterpretationSolver,
        "expected_format_keyword": "CORRECT OPTION: C"
    },
    # 8. Figure Series (8 images -> 9th missing image)
    {
        "id": "CASE_08_FIG_SERIES_8TO9",
        "text": "A series is given with figure missing. Analyse 8 images and choose the correct 9th image from 4 options.",
        "expected_category": QuestionCategory.NON_VERBAL_REASONING,
        "expected_subcat": "Figure Series",
        "format": AssessmentFormat.IMAGE_OPTIONS,
        "input_data": {
            "option_label": "Option 2",
            "option_index": 1,
            "total_options": 4,
            "orientation": "horizontal",
            "full_answer": "Option 2 – Second image from the left",
            "confidence": 0.98
        },
        "solver": FigureSeriesSolver,
        "expected_format_keyword": "POSITION: 2nd from LEFT"
    },
    # 9. Figure Matrix (2x2 / 3x3 grid)
    {
        "id": "CASE_09_FIG_MATRIX",
        "text": "Find the missing figure in the 3x3 figure matrix arrangement.",
        "expected_category": QuestionCategory.NON_VERBAL_REASONING,
        "expected_subcat": "Figure Matrix",
        "format": AssessmentFormat.IMAGE_OPTIONS,
        "input_data": {
            "option_label": "Option 3",
            "option_index": 2,
            "total_options": 4,
            "orientation": "grid",
            "grid_row": 1,
            "grid_col": 2,
            "confidence": 0.98
        },
        "solver": FigureMatrixSolver,
        "expected_format_keyword": "GRID POSITION: ROW 1, COLUMN 2"
    },
    # 10. Mirror Image
    {
        "id": "CASE_10_MIRROR_IMAGE",
        "text": "Identify the reflected mirror image of the given problem figure.",
        "expected_category": QuestionCategory.NON_VERBAL_REASONING,
        "expected_subcat": "Mirror Image",
        "format": AssessmentFormat.IMAGE_OPTIONS,
        "input_data": {"option_label": "Option 4", "option_index": 3, "total_options": 4, "confidence": 0.98},
        "solver": VisualReasoningSolver,
        "expected_format_keyword": "POSITION: 4th from LEFT"
    },
    # 11. Water Image
    {
        "id": "CASE_11_WATER_IMAGE",
        "text": "Identify the inverted water image of the given figure.",
        "expected_category": QuestionCategory.NON_VERBAL_REASONING,
        "expected_subcat": "Water Image",
        "format": AssessmentFormat.IMAGE_OPTIONS,
        "input_data": {"option_label": "Option 1", "option_index": 0, "total_options": 4, "confidence": 0.98},
        "solver": VisualReasoningSolver,
        "expected_format_keyword": "POSITION: 1st from LEFT"
    },
    # 12. Paper Folding and Cutting
    {
        "id": "CASE_12_PAPER_FOLDING",
        "text": "Predict the result after unfolding a folded paper cut with three circular holes.",
        "expected_category": QuestionCategory.NON_VERBAL_REASONING,
        "expected_subcat": "Paper Folding and Cutting",
        "format": AssessmentFormat.IMAGE_OPTIONS,
        "input_data": {"option_label": "Option 2", "option_index": 1, "total_options": 4, "confidence": 0.98},
        "solver": VisualReasoningSolver,
        "expected_format_keyword": "POSITION FROM RIGHT: 3rd from RIGHT"
    },
    # 13. Embedded Figures
    {
        "id": "CASE_13_EMBEDDED_FIGURE",
        "text": "In the following question, find the hidden shape embedded figure inside the complex image.",
        "expected_category": QuestionCategory.NON_VERBAL_REASONING,
        "expected_subcat": "Embedded Figures",
        "format": AssessmentFormat.IMAGE_OPTIONS,
        "input_data": {"option_label": "Option 3", "option_index": 2, "total_options": 4, "confidence": 0.98},
        "solver": VisualReasoningSolver,
        "expected_format_keyword": "CORRECT ANSWER: OPTION 3"
    },
    # 14. Odd One Out
    {
        "id": "CASE_14_ODD_ONE_OUT",
        "text": "Identify the odd one out figure that differs in pattern from the other figures.",
        "expected_category": QuestionCategory.NON_VERBAL_REASONING,
        "expected_subcat": "Odd One Out",
        "format": AssessmentFormat.IMAGE_OPTIONS,
        "input_data": {"option_label": "Option 4", "option_index": 3, "total_options": 4, "confidence": 0.98},
        "solver": VisualReasoningSolver,
        "expected_format_keyword": "POSITION: 4th from LEFT"
    },
    # 15. Logical Reasoning: Coding-Decoding
    {
        "id": "CASE_15_LOGIC_CODING",
        "text": "In a certain code language, if 'TIGER' is coded as 'VKIGT', how is 'HORSE' coded in that language?",
        "expected_category": QuestionCategory.LOGICAL_REASONING,
        "expected_subcat": "Coding-Decoding",
        "format": AssessmentFormat.MCQ,
        "input_data": {"option_label": "A", "full_answer": "JQTUG", "option_index": 0, "confidence": 0.99},
        "solver": LogicalReasoningSolver,
        "expected_format_keyword": "CORRECT OPTION: A\n\nFULL ANSWER: JQTUG"
    },
    # 16. Logical Reasoning: Blood Relations
    {
        "id": "CASE_16_LOGIC_BLOOD",
        "text": "Pointing to a man, a woman says: 'His mother is the only daughter of my mother'. How is the woman related to the man?",
        "expected_category": QuestionCategory.LOGICAL_REASONING,
        "expected_subcat": "Blood Relations",
        "format": AssessmentFormat.MCQ,
        "input_data": {"option_label": "B", "full_answer": "Mother", "option_index": 1, "confidence": 0.99},
        "solver": LogicalReasoningSolver,
        "expected_format_keyword": "CORRECT OPTION: B\n\nFULL ANSWER: Mother"
    },
    # 17. Logical Reasoning: Direction Sense
    {
        "id": "CASE_17_LOGIC_DIRECTION",
        "text": "A man walks 10m towards North, turns right and walks 5m, turns right and walks 10m. What is his direction from starting point?",
        "expected_category": QuestionCategory.LOGICAL_REASONING,
        "expected_subcat": "Direction Sense",
        "format": AssessmentFormat.MCQ,
        "input_data": {"option_label": "C", "full_answer": "East", "option_index": 2, "confidence": 0.99},
        "solver": LogicalReasoningSolver,
        "expected_format_keyword": "CORRECT OPTION: C\n\nFULL ANSWER: East"
    },
    # 18. Logical Reasoning: Seating Arrangement
    {
        "id": "CASE_18_LOGIC_SEATING",
        "text": "Six persons are sitting around a circular table facing the center.",
        "expected_category": QuestionCategory.LOGICAL_REASONING,
        "expected_subcat": "Seating Arrangement",
        "format": AssessmentFormat.MCQ,
        "input_data": {"option_label": "D", "full_answer": "Opposite to B", "option_index": 3, "confidence": 0.99},
        "solver": LogicalReasoningSolver,
        "expected_format_keyword": "CORRECT OPTION: D"
    },
    # 19. Logical Reasoning: Syllogisms
    {
        "id": "CASE_19_LOGIC_SYLLOGISM",
        "text": "Statements: All cats are dogs. Some dogs are birds. Syllogism conclusion:",
        "expected_category": QuestionCategory.LOGICAL_REASONING,
        "expected_subcat": "Syllogisms",
        "format": AssessmentFormat.MCQ,
        "input_data": {"option_label": "A", "full_answer": "Only conclusion I follows", "option_index": 0, "confidence": 0.99},
        "solver": LogicalReasoningSolver,
        "expected_format_keyword": "CORRECT OPTION: A"
    },
    # 20. English Verbal: Reading Comprehension
    {
        "id": "CASE_20_VERBAL_COMPREHENSION",
        "text": "According to the passage on economic policy, what is the primary cause of inflation in developing nations?",
        "expected_category": QuestionCategory.ENGLISH_VERBAL,
        "expected_subcat": "Reading Comprehension",
        "format": AssessmentFormat.MCQ,
        "input_data": {"option_label": "C", "full_answer": "Supply chain bottlenecks", "option_index": 2, "confidence": 0.98},
        "solver": VerbalReasoningSolver,
        "expected_format_keyword": "CORRECT OPTION: C\n\nFULL ANSWER: Supply chain bottlenecks"
    },
    # 21. English Verbal: Synonyms
    {
        "id": "CASE_21_VERBAL_SYNONYMS",
        "text": "Select the option that is the closest synonym to the word 'EPHEMERAL'.",
        "expected_category": QuestionCategory.ENGLISH_VERBAL,
        "expected_subcat": "Synonyms",
        "format": AssessmentFormat.MCQ,
        "input_data": {"option_label": "B", "full_answer": "Transient", "option_index": 1, "confidence": 0.99},
        "solver": VerbalReasoningSolver,
        "expected_format_keyword": "CORRECT OPTION: B\n\nFULL ANSWER: Transient"
    },
    # 22. English Verbal: Sentence Correction / Grammar
    {
        "id": "CASE_22_VERBAL_GRAMMAR",
        "text": "Find the grammatical error in the sentence: 'Neither of the boys were present at the meeting.'",
        "expected_category": QuestionCategory.ENGLISH_VERBAL,
        "expected_subcat": "Sentence Correction & Grammar",
        "format": AssessmentFormat.MCQ,
        "input_data": {"option_label": "B", "full_answer": "'were present' should be 'was present'", "option_index": 1, "confidence": 0.98},
        "solver": VerbalReasoningSolver,
        "expected_format_keyword": "CORRECT OPTION: B"
    },
    # 23. Technical Knowledge: Operating Systems
    {
        "id": "CASE_23_TECH_OS",
        "text": "In modern operating systems, which scheduling algorithm is strictly non-preemptive?",
        "expected_category": QuestionCategory.TECHNICAL_KNOWLEDGE,
        "expected_subcat": "Operating Systems",
        "format": AssessmentFormat.MCQ,
        "input_data": {"option_label": "A", "full_answer": "First-Come First-Served (FCFS)", "option_index": 0, "confidence": 0.99},
        "solver": TechnicalMcqSolver,
        "expected_format_keyword": "CORRECT OPTION: A"
    },
    # 24. Technical Knowledge: MSQ in DBMS
    {
        "id": "CASE_24_TECH_MSQ_DBMS",
        "text": "Select multiple answers: Which of the following are ACID properties in DBMS transactions? (MSQ)",
        "expected_category": QuestionCategory.TECHNICAL_KNOWLEDGE,
        "expected_subcat": "DBMS & SQL",
        "format": AssessmentFormat.MSQ,
        "input_data": {
            "assessment_format": "MSQ",
            "selected_options": ["A", "C"],
            "full_answer": "Atomicity and Consistency",
            "confidence": 0.99
        },
        "solver": TechnicalMcqSolver,
        "expected_format_keyword": "CORRECT OPTIONS: A, C"
    },
    # 25. Edge Case: Screenshot Unclear
    {
        "id": "CASE_25_SCREENSHOT_UNCLEAR",
        "text": "Unclear distorted question where text and options are blurry.",
        "expected_category": None,  # For unclear images, category matching is bypassed
        "expected_subcat": "General",
        "format": AssessmentFormat.MCQ,
        "input_data": {
            "needs_clarification": True,
            "missing_information": "Chart label and numbers are illegible",
            "confidence": 0.30
        },
        "solver": NumericalSolver,
        "expected_format_keyword": "SCREENSHOT UNCLEAR"
    }
]


class TestSyntheticDataset(unittest.TestCase):
    def test_full_dataset_accuracy(self):
        total_cases = len(SYNTHETIC_DATASET)
        correct_cases = 0
        results_log = []

        for case in SYNTHETIC_DATASET:
            case_id = case["id"]
            text = case["text"]

            # 1. Classification Verification
            cat, subcat = QuestionClassifier.classify_text(text)
            cat_match = (case["expected_category"] is None or cat == case["expected_category"])

            # 2. Solver Post-Processing
            solver = case["solver"]
            ans = solver.post_process(case["input_data"])

            # 3. Validation
            val_ans = AnswerValidator.validate_and_refine(ans)

            # 4. Strict Formatting
            formatted = val_ans.to_strict_format()
            keyword_match = case["expected_format_keyword"] in formatted

            passed = cat_match and keyword_match
            if passed:
                correct_cases += 1
            else:
                results_log.append(
                    f"FAILED {case_id}: cat_match={cat_match} (got {cat}, expected {case['expected_category']}), "
                    f"keyword_match={keyword_match} (expected '{case['expected_format_keyword']}' in '{formatted}')"
                )

        accuracy_pct = (correct_cases / total_cases) * 100.0
        print(f"\n[SYNTHETIC TEST SUITE] Cases: {total_cases} | Passed: {correct_cases} | Accuracy: {accuracy_pct:.2f}%")
        for err in results_log:
            print(f"  -> {err}")

        # Assert 100% accuracy on our labeled synthetic benchmark
        self.assertEqual(correct_cases, total_cases, f"Failed cases: {results_log}")


if __name__ == "__main__":
    unittest.main()
