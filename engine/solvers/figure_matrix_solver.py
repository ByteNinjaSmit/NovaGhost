"""
NovaGhost — Figure Matrix Solver.
Analyzes 2x2 and 3x3 visual arrangements to determine the missing image.
Applies row-wise, column-wise, and diagonal relational logic.
"""

import logging
from typing import Dict, Any, Optional
from engine.schemas import QuestionCategory, AssessmentFormat, StructuredAnswer, compute_positions

logger = logging.getLogger(__name__)


class FigureMatrixSolver:
    """Specialized solver for 2x2 and 3x3 Abstract Figure Matrices."""

    SYSTEM_PROMPT = (
        "You are an expert Abstract Matrix & Visual Reasoning Solver.\n"
        "Your task is to solve 2x2 or 3x3 figure matrices (Raven's style or ASEP abstract matrix tests) "
        "where one figure in the grid is missing (often indicated by a question mark '?').\n\n"
        "SYSTEMATIC MATRIX ANALYSIS RULES:\n"
        "1. Horizontal Row Analysis: Analyze changes across Row 1, Row 2, and determine the rule for Row 3.\n"
        "2. Vertical Column Analysis: Check if the same rule or a complementary rule applies down Column 1, 2, and 3.\n"
        "3. Relational Operations:\n"
        "   - Overlay / Superimposition: OR, AND, XOR logic (elements appearing in both or only one figure).\n"
        "   - Progressive Transformation: Shape rotation, scaling, or translation across the grid.\n"
        "   - Distribution of Characteristics: Each row and column contains exactly one of each shape, line style, or count.\n"
        "4. Compare all available options (1-4 or 1-8).\n"
        "5. Identify the matching option and its exact position (from left, from right, or row/column if grid).\n"
        "6. Return strictly valid JSON with this exact schema:\n"
        "{\n"
        '  "question_category": "non_verbal_reasoning",\n'
        '  "subcategory": "Figure Matrix",\n'
        '  "assessment_format": "IMAGE_OPTIONS",\n'
        '  "is_image_options": true,\n'
        '  "option_label": "Option 3" | "Option 1" | "3" | "C" | null,\n'
        '  "option_index": 2,\n'
        '  "total_options": 4,\n'
        '  "orientation": "horizontal" | "vertical" | "grid",\n'
        '  "grid_row": 1,\n'
        '  "grid_col": 2,\n'
        '  "position_from_left": "3rd from LEFT",\n'
        '  "position_from_right": "2nd from RIGHT",\n'
        '  "full_answer": "Option 3 – Third image from the left",\n'
        '  "matrix_rule": "Concise summary of row/column transformation rule",\n'
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
        opt_idx = data.get("option_index")
        total = int(data.get("total_options") or 4)
        orientation = data.get("orientation", "horizontal")

        if opt_idx is None and data.get("option_label"):
            lbl = str(data["option_label"]).lower()
            for i, char in enumerate(["a", "b", "c", "d", "e", "f"]):
                if char in lbl:
                    opt_idx = i
                    break
            if opt_idx is None:
                for i, char in enumerate(["1", "2", "3", "4", "5", "6"]):
                    if char in lbl:
                        opt_idx = i
                        break

        if opt_idx is None:
            opt_idx = 0

        pos = compute_positions(opt_idx, total, orientation)
        pos_left = data.get("position_from_left") or pos["position_from_left"]
        pos_right = data.get("position_from_right") or pos["position_from_right"]

        label = data.get("option_label")
        if not label:
            label = f"Option {opt_idx + 1}"

        full = data.get("full_answer")
        if not full or full == label:
            full = f"{label} – {pos_left}"

        ans = StructuredAnswer(
            question_category=QuestionCategory.NON_VERBAL_REASONING,
            subcategory="Figure Matrix",
            assessment_format=AssessmentFormat.IMAGE_OPTIONS,
            is_image_options=True,
            option_label=label,
            option_index=opt_idx,
            total_options=total,
            orientation=orientation,
            grid_row=data.get("grid_row"),
            grid_col=data.get("grid_col"),
            position_from_left=pos_left,
            position_from_right=pos_right,
            full_answer=full,
            confidence=float(data.get("confidence", 0.95)),
            needs_clarification=bool(data.get("needs_clarification", False)),
            missing_information=data.get("missing_information")
        )
        return ans
