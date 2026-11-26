"""
NovaGhost — Logical Reasoning Solver (Text-Based).
Specializes in Coding-Decoding, Blood Relations, Direction Sense,
Seating Arrangements, Syllogisms, Statement & Conclusion, Puzzles, Clocks & Calendars.
Excludes programming implementation or coding tasks.
"""

import logging
from typing import Dict, Any, Optional
from engine.schemas import QuestionCategory, AssessmentFormat, StructuredAnswer

logger = logging.getLogger(__name__)


class LogicalReasoningSolver:
    """Specialized solver for Text-based Logical & Deductive Reasoning."""

    SYSTEM_PROMPT = (
        "You are an expert Deductive & Logical Reasoning Engine.\n"
        "Your task is to solve text-based logical reasoning questions.\n"
        "Domains: Coding-Decoding, Blood Relations, Direction Sense, Seating Arrangement (linear/circular), "
        "Syllogisms (formal logic), Statement and Conclusion, Statement and Assumption, Ranking & Ordering, "
        "Clocks, Calendars, Logic Puzzles.\n\n"
        "CRITICAL RULES:\n"
        "1. Strictly follow logical deduction and formal rules (e.g. for Syllogisms only what definitely follows).\n"
        "2. For coding-decoding, trace the exact letter shifts or numerical mappings.\n"
        "3. For blood relations, map out the relationships systematically.\n"
        "4. DO NOT write or generate programming code. This is an aptitude test question.\n"
        "5. Identify the exact correct option letter and the complete text of the chosen option.\n"
        "6. Return strictly valid JSON with this exact schema:\n"
        "{\n"
        '  "question_category": "logical_reasoning",\n'
        '  "subcategory": "Blood Relations | Direction Sense | Syllogisms | Coding-Decoding | etc.",\n'
        '  "assessment_format": "MCQ",\n'
        '  "option_label": "A" | "B" | "C" | "D",\n'
        '  "option_index": 0 | 1 | 2 | 3,\n'
        '  "total_options": 4,\n'
        '  "full_answer": "Complete text of the option as written",\n'
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
        opt_lbl = str(data.get("option_label") or "A").strip()
        full = str(data.get("full_answer") or opt_lbl).strip()

        ans = StructuredAnswer(
            question_category=QuestionCategory.LOGICAL_REASONING,
            subcategory=data.get("subcategory", "Logical Reasoning"),
            assessment_format=AssessmentFormat.MCQ,
            is_image_options=False,
            option_label=opt_lbl,
            option_index=data.get("option_index"),
            total_options=int(data.get("total_options") or 4),
            full_answer=full,
            confidence=float(data.get("confidence", 0.95)),
            needs_clarification=bool(data.get("needs_clarification", False)),
            missing_information=data.get("missing_information")
        )
        return ans
