"""
NovaGhost — Verbal Reasoning & English Ability Solver.
Specializes in Reading Comprehension, Synonyms, Antonyms, Sentence Correction,
Fill in the Blanks, Grammar, Para Jumbles, Error Detection, and Vocabulary.
Preserves exact spelling and complete option text.
"""

import logging
from typing import Dict, Any, Optional
from engine.schemas import QuestionCategory, AssessmentFormat, StructuredAnswer

logger = logging.getLogger(__name__)


class VerbalReasoningSolver:
    """Specialized solver for English Language & Verbal Ability."""

    SYSTEM_PROMPT = (
        "You are an expert English Language & Verbal Ability Engine.\n"
        "Your task is to analyze verbal reasoning, grammar, and comprehension questions.\n"
        "Domains: Reading Comprehension, Synonyms & Antonyms, Sentence Correction, Fill in the Blanks, "
        "Grammar Rules, Para Jumbles, Spotting Errors, Vocabulary.\n\n"
        "CRITICAL RULES:\n"
        "1. Read the full sentence or passage carefully before arriving at an answer.\n"
        "2. For synonyms/antonyms, consider contextual connotation and part of speech.\n"
        "3. For grammar/sentence correction, identify the precise grammatical violation (subject-verb agreement, tense, idioms).\n"
        "4. PRESERVE THE COMPLETE OPTION TEXT verbatim. Never truncate or summarize words.\n"
        "5. Return strictly valid JSON with this exact schema:\n"
        "{\n"
        '  "question_category": "english_verbal",\n'
        '  "subcategory": "Reading Comprehension | Synonyms | Grammar | Sentence Correction",\n'
        '  "assessment_format": "MCQ",\n'
        '  "option_label": "A" | "B" | "C" | "D",\n'
        '  "option_index": 0 | 1 | 2 | 3,\n'
        '  "total_options": 4,\n'
        '  "full_answer": "Complete verbatim text of the selected option",\n'
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
            question_category=QuestionCategory.ENGLISH_VERBAL,
            subcategory=data.get("subcategory", "Verbal Ability"),
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
