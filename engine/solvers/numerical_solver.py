"""
NovaGhost — Numerical Aptitude Solver.
Handles arithmetic, percentages, profit & loss, interest, ratios, averages,
time & work, speed/distance/time, age, probability, permutations, and series.
Ensures deterministic calculation validation and complete preservation of decimal values.
"""

import re
import math
import logging
from typing import Dict, Any, Optional
from engine.schemas import QuestionCategory, AssessmentFormat, StructuredAnswer
from engine.math_engine import SymPyMathEngine

logger = logging.getLogger(__name__)


class NumericalSolver:
    """Specialized solver for Quantitative Aptitude & Numerical Reasoning."""

    SYSTEM_PROMPT = (
        "You are the world's most precise Quantitative Aptitude and Mathematics Engine.\n"
        "Your task is to solve the numerical or mathematical question presented in the image.\n"
        "Domains: Percentages, Profit & Loss, Simple & Compound Interest, Ratio & Proportion, "
        "Averages, Time & Work, Speed Distance & Time, Ages, Probability, Permutations, Number Series.\n\n"
        "RULES FOR SOLVING:\n"
        "1. Perform step-by-step rigorous calculation internally.\n"
        "2. If it is a multiple-choice question (MCQ), identify the exact option letter/number and full text.\n"
        "3. If it is a Numerical Answer Type (NAT/TITA), calculate the exact numerical value.\n"
        "4. PRESERVE FULL DECIMAL ACCURACY. Never truncate decimals or round prematurely.\n"
        "5. Do NOT confuse percentages with absolute values.\n"
        "6. Return strictly valid JSON with this exact schema:\n"
        "{\n"
        '  "question_category": "numerical_aptitude",\n'
        '  "subcategory": "Percentages | Profit and Loss | Ratio | Time and Work | etc.",\n'
        '  "assessment_format": "MCQ" | "NAT" | "MSQ",\n'
        '  "option_label": "A" | "B" | "C" | "D" | "1" | "2" | null,\n'
        '  "option_index": 0 | 1 | 2 | 3 | null,\n'
        '  "total_options": 4,\n'
        '  "numerical_value": "1250.50" | null,\n'
        '  "full_answer": "Exact text or value of the correct answer",\n'
        '  "confidence": 0.99,\n'
        '  "needs_clarification": false,\n'
        '  "missing_information": null\n'
        "}\n"
        "Output ONLY the JSON object. No explanations, markdown preamble, or extra commentary."
    )

    @classmethod
    def get_prompt(cls) -> str:
        return cls.SYSTEM_PROMPT

    @classmethod
    def verify_arithmetic(cls, expression: str) -> Optional[float]:
        """
        Evaluates arithmetic expressions with exact precision using SymPyMathEngine.
        """
        return SymPyMathEngine.evaluate_expression(expression)

    @classmethod
    def post_process(cls, data: Dict[str, Any], problem_text: Optional[str] = None) -> StructuredAnswer:
        """Translates raw parsed JSON into a verified StructuredAnswer."""
        format_str = data.get("assessment_format", "MCQ")
        assessment_format = AssessmentFormat.NAT if format_str == "NAT" else AssessmentFormat.MCQ

        num_val = str(data["numerical_value"]).strip() if data.get("numerical_value") is not None else None
        full_ans = str(data.get("full_answer") or data.get("numerical_value") or data.get("option_label") or "").strip()

        # Deterministic verification & correction if problem text is provided
        if problem_text:
            target_val = num_val or full_ans
            corrected, was_corrected = SymPyMathEngine.verify_and_correct(problem_text, target_val)
            if was_corrected:
                logger.info(f"SymPy auto-corrected numerical value from '{target_val}' to '{corrected}'")
                if num_val:
                    num_val = corrected
                full_ans = corrected

        ans = StructuredAnswer(
            question_category=QuestionCategory.NUMERICAL_APTITUDE,
            subcategory=data.get("subcategory", "Quantitative Aptitude"),
            assessment_format=assessment_format,
            is_image_options=False,
            option_label=data.get("option_label"),
            option_index=data.get("option_index"),
            total_options=int(data.get("total_options") or 4),
            numerical_value=num_val,
            full_answer=full_ans,
            confidence=float(data.get("confidence", 0.95)),
            needs_clarification=bool(data.get("needs_clarification", False)),
            missing_information=data.get("missing_information")
        )

        # If NAT but full_answer contains the value, ensure numerical_value is set
        if ans.assessment_format == AssessmentFormat.NAT and not ans.numerical_value:
            num_match = re.search(r"[-+]?\d*\.?\d+", ans.full_answer)
            if num_match:
                ans.numerical_value = num_match.group(0)

        return ans
