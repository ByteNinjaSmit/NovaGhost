"""
NovaGhost — Technical Knowledge & Computer Science MCQ Solver.
Specializes in Computer Fundamentals, DBMS & SQL, Operating Systems,
Computer Networks, Software Engineering, and Technical MCQs/MSQs.
Excludes programming implementation / code writing submissions.
"""

import logging
from typing import Dict, Any, Optional, List
from engine.schemas import QuestionCategory, AssessmentFormat, StructuredAnswer

logger = logging.getLogger(__name__)


class TechnicalMcqSolver:
    """Specialized solver for Computer Science, IT & Technical Assessment MCQs/MSQs."""

    SYSTEM_PROMPT = (
        "You are an expert Computer Science & Technical Assessment Engine.\n"
        "Your task is to analyze technical aptitude questions.\n"
        "Domains: Computer Fundamentals, Database Management Systems (DBMS & SQL queries/concepts), "
        "Operating Systems (processes, threads, deadlocks, paging), Computer Networks (OSI, TCP/IP, protocols), "
        "Software Engineering Fundamentals, Output Prediction MCQs.\n\n"
        "CRITICAL RULES:\n"
        "1. Answer technical MCQs accurately based on standard CS theory and standards.\n"
        "2. If it is Multiple Select (MSQ), identify ALL correct options (e.g. A and C).\n"
        "3. DO NOT generate code files or write software implementations. Solve the question directly.\n"
        "4. Return strictly valid JSON with this exact schema:\n"
        "{\n"
        '  "question_category": "technical_knowledge",\n'
        '  "subcategory": "DBMS | Operating Systems | Computer Networks | Fundamentals",\n'
        '  "assessment_format": "MCQ" | "MSQ" | "NAT",\n'
        '  "option_label": "A" | "B" | "C" | "D",\n'
        '  "selected_options": ["A", "C"],\n'
        '  "option_index": 0,\n'
        '  "total_options": 4,\n'
        '  "full_answer": "Complete text of the correct answer",\n'
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
        fmt = AssessmentFormat.MSQ if data.get("assessment_format") == "MSQ" else AssessmentFormat.MCQ
        sel = data.get("selected_options") or []
        if not isinstance(sel, list):
            sel = [str(sel)]

        opt_lbl = str(data.get("option_label") or (sel[0] if sel else "A")).strip()
        full = str(data.get("full_answer") or opt_lbl).strip()

        ans = StructuredAnswer(
            question_category=QuestionCategory.TECHNICAL_KNOWLEDGE,
            subcategory=data.get("subcategory", "Technical Knowledge"),
            assessment_format=fmt,
            is_image_options=False,
            option_label=opt_lbl,
            selected_options=sel,
            option_index=data.get("option_index"),
            total_options=int(data.get("total_options") or 4),
            full_answer=full,
            confidence=float(data.get("confidence", 0.95)),
            needs_clarification=bool(data.get("needs_clarification", False)),
            missing_information=data.get("missing_information")
        )
        return ans
