"""
NovaGhost — Data Interpretation Solver.
Analyzes Bar Graphs (Horizontal & Vertical), Pie Charts, Line Graphs, Tables,
Combined Graphs, and Caselet-based questions.
Ensures exact extraction of values from legends, axis scales, units, and categories.
"""

import re
import logging
from typing import Dict, Any, Optional
from engine.schemas import QuestionCategory, AssessmentFormat, StructuredAnswer

logger = logging.getLogger(__name__)


class DataInterpretationSolver:
    """Specialized solver for charts, graphs, tables, and data interpretation."""

    SYSTEM_PROMPT = (
        "You are an expert Data Interpretation & Analytics Engine.\n"
        "Your task is to analyze the charts, tables, or graphs in the image and solve the question with zero error.\n"
        "Data Types: Horizontal/Vertical Bar Charts, Pie Charts, Line Graphs, Data Tables, Mixed/Combined Charts.\n\n"
        "STRICT CRITICAL RULES:\n"
        "1. Identify every axis scale, legend label, unit (e.g., in thousands, lakhs, %, millions).\n"
        "2. Do NOT confuse categories or series (e.g. clearly distinguish Organization B vs Organization E, "
        "male vs female, year 2021 vs 2022).\n"
        "3. Read the exact numerical values or percentages corresponding to the requested labels.\n"
        "4. Calculate the required quantity (difference, sum, average, percentage change, ratio) independently.\n"
        "5. If an MCQ option matches your calculated value, select that exact option letter and text.\n"
        "6. If NAT, enter the exact calculated number with complete decimal places.\n"
        "7. Return strictly valid JSON with this exact schema:\n"
        "{\n"
        '  "question_category": "data_interpretation",\n'
        '  "subcategory": "Bar Graph | Pie Chart | Table | Line Graph | Combined",\n'
        '  "assessment_format": "MCQ" | "NAT",\n'
        '  "option_label": "A" | "B" | "C" | "D" | "1" | "2" | null,\n'
        '  "option_index": 0 | 1 | 2 | 3 | null,\n'
        '  "total_options": 4,\n'
        '  "numerical_value": "45.75" | null,\n'
        '  "full_answer": "Exact answer text or calculated value",\n'
        '  "extracted_data": "Brief summary of values extracted from chart",\n'
        '  "confidence": 0.98,\n'
        '  "needs_clarification": false,\n'
        '  "missing_information": null\n'
        "}\n"
        "Output ONLY the JSON object. No explanations, markdown preamble, or extra commentary."
    )

    @classmethod
    def get_prompt(cls) -> str:
        return cls.SYSTEM_PROMPT

    @classmethod
    def post_process(cls, data: Dict[str, Any]) -> StructuredAnswer:
        format_str = data.get("assessment_format", "MCQ")
        assessment_format = AssessmentFormat.NAT if format_str == "NAT" else AssessmentFormat.MCQ

        ans = StructuredAnswer(
            question_category=QuestionCategory.DATA_INTERPRETATION,
            subcategory=data.get("subcategory", "Data Interpretation"),
            assessment_format=assessment_format,
            is_image_options=False,
            option_label=data.get("option_label"),
            option_index=data.get("option_index"),
            total_options=int(data.get("total_options") or 4),
            numerical_value=str(data["numerical_value"]).strip() if data.get("numerical_value") is not None else None,
            full_answer=str(data.get("full_answer") or data.get("numerical_value") or data.get("option_label") or "").strip(),
            confidence=float(data.get("confidence", 0.95)),
            needs_clarification=bool(data.get("needs_clarification", False)),
            missing_information=data.get("missing_information")
        )
        return ans
