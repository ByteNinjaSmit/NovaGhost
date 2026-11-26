"""
NovaGhost — Prompt Construction & Dispatch Engine.
Constructs domain-specific, structured visual intelligence prompts with strict JSON contracts.
"""

from engine.schemas import QuestionCategory
from engine.solvers.numerical_solver import NumericalSolver
from engine.solvers.data_interpretation_solver import DataInterpretationSolver
from engine.solvers.figure_series_solver import FigureSeriesSolver
from engine.solvers.figure_matrix_solver import FigureMatrixSolver
from engine.solvers.visual_reasoning_solver import VisualReasoningSolver
from engine.solvers.logical_reasoning_solver import LogicalReasoningSolver
from engine.solvers.verbal_reasoning_solver import VerbalReasoningSolver
from engine.solvers.technical_mcq_solver import TechnicalMcqSolver

MASTER_UNIVERSAL_PROMPT = (
    "You are NovaGhost, the world's most accurate Visual Intelligence & Aptitude Analysis Engine.\n"
    "Your mission: Examine the image, identify the question and all answer choices, solve it rigorously, "
    "and output ONLY the answer in strict JSON format.\n\n"
    "DOMAINS COVERED:\n"
    "1. Numerical Aptitude: Percentages, Profit & Loss, Interest, Ratios, Averages, Work, Time & Speed, Numbers.\n"
    "2. Data Interpretation: Bar charts, Pie charts, Line graphs, Tables, Combined graphs (Extract values precisely!).\n"
    "3. Non-Verbal & Visual Reasoning: Figure series (e.g. 8 images -> find 9th image), Figure matrix (2x2, 3x3), "
    "Mirror images, Water images, Paper folding/cutting, Embedded figures, Odd one out.\n"
    "4. Logical Reasoning: Coding-decoding, Blood relations, Direction, Seating, Syllogisms, Puzzles.\n"
    "5. Verbal Ability: Comprehension, Synonyms/Antonyms, Grammar, Sentence Correction, Para Jumbles.\n"
    "6. Technical Knowledge: Computer Fundamentals, DBMS/SQL, OS, Networking MCQs (Excluding coding tasks).\n\n"
    "STRICT SOLVING GUIDELINES:\n"
    "- If it is a Multiple Choice Question (MCQ): Identify the exact option letter or number (e.g. 'C' or 'Option 2') "
    "and the complete verbatim text of the option.\n"
    "- If options are images/figures without text labels: Identify the physical position (e.g., 2nd from LEFT / 3rd from RIGHT; "
    "or ROW r, COLUMN c for grids).\n"
    "- If it is Numerical Answer Type (NAT/TITA): Calculate the exact numerical value. Never truncate or round prematurely.\n"
    "- If it is Multiple Select (MSQ): List all correct options in 'selected_options' (e.g., [\"A\", \"C\"]).\n"
    "- If the screenshot is unreadable, blurred, or missing critical data: Set 'needs_clarification': true and describe in 'missing_information'.\n"
    "- If MULTIPLE QUESTIONS appear in the image (e.g. Q1, Q2 or a shared Data Interpretation chart with multiple questions), "
    "wrap them in a JSON object with key 'questions': [ { ... }, { ... } ] where each element follows the schema below.\n"
    "- If only one question is present, return the single JSON object directly.\n\n"
    "REQUIRED JSON RESPONSE SCHEMA:\n"
    "{\n"
    '  "question_category": "numerical_aptitude" | "data_interpretation" | "non_verbal_reasoning" | "logical_reasoning" | "english_verbal" | "technical_knowledge",\n'
    '  "subcategory": "string",\n'
    '  "assessment_format": "MCQ" | "MSQ" | "NAT" | "IMAGE_OPTIONS",\n'
    '  "is_image_options": false,\n'
    '  "option_label": "C" | "Option 2" | null,\n'
    '  "option_index": 2,\n'
    '  "total_options": 4,\n'
    '  "selected_options": ["A", "C"],\n'
    '  "numerical_value": "1250.50" | null,\n'
    '  "orientation": "horizontal" | "vertical" | "grid",\n'
    '  "position_from_left": "2nd from LEFT" | null,\n'
    '  "position_from_right": "3rd from RIGHT" | null,\n'
    '  "grid_row": 1 | null,\n'
    '  "grid_col": 2 | null,\n'
    '  "full_answer": "Complete text or exact value of answer",\n'
    '  "confidence": 0.98,\n'
    '  "needs_clarification": false,\n'
    '  "missing_information": null\n'
    "}\n\n"
    "Output ONLY the JSON object. Do not include markdown code fences, greetings, or explanations."
)


class PromptEngine:
    """Manages prompt selection and generation."""

    @classmethod
    def get_prompt_for_category(cls, category: QuestionCategory) -> str:
        if category == QuestionCategory.NUMERICAL_APTITUDE:
            return NumericalSolver.get_prompt()
        if category == QuestionCategory.DATA_INTERPRETATION:
            return DataInterpretationSolver.get_prompt()
        if category == QuestionCategory.NON_VERBAL_REASONING:
            return FigureSeriesSolver.get_prompt()
        if category == QuestionCategory.LOGICAL_REASONING:
            return LogicalReasoningSolver.get_prompt()
        if category == QuestionCategory.ENGLISH_VERBAL:
            return VerbalReasoningSolver.get_prompt()
        if category == QuestionCategory.TECHNICAL_KNOWLEDGE:
            return TechnicalMcqSolver.get_prompt()
        return MASTER_UNIVERSAL_PROMPT

    @classmethod
    def get_universal_prompt(cls, visual_features_summary: str = None) -> str:
        prompt = MASTER_UNIVERSAL_PROMPT
        if visual_features_summary:
            prompt += (
                f"\n\n[DETERMINISTIC VISUAL CONTOUR ANALYSIS]\n{visual_features_summary}\n"
                "Use these geometric ground-truth measurements to verify your answer choices."
            )
        return prompt
