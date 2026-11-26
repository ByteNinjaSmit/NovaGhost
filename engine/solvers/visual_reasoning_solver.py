"""
NovaGhost — Visual Reasoning Solver.
Specializes in Mirror Images, Water Images, Paper Folding & Cutting,
Embedded Figures, Odd One Out, and Spatial Reasoning.
"""

import logging
from typing import Dict, Any, Optional
from engine.schemas import QuestionCategory, AssessmentFormat, StructuredAnswer, compute_positions

logger = logging.getLogger(__name__)


class VisualReasoningSolver:
    """Specialized solver for Mirror, Water Images, Paper Folding, and Embedded Figures."""

    SYSTEM_PROMPT = (
        "You are an expert Visual & Spatial Reasoning Engine.\n"
        "Your task is to analyze non-verbal visual reasoning tasks:\n"
        "- Mirror Images: Reflection along a vertical mirror line (left-right inversion, top-bottom preserved).\n"
        "- Water Images: Reflection along a horizontal water surface (top-bottom inversion, left-right preserved).\n"
        "- Paper Folding & Cutting: Step-by-step unfolding of punched or cut folded paper.\n"
        "- Embedded Figures: Locating a simple given figure hidden inside a complex geometric structure.\n"
        "- Odd One Out: Identifying the single figure that violates the underlying symmetry or rotational rule.\n\n"
        "RULES:\n"
        "1. Strictly apply reflection, unfolding, or containment geometry.\n"
        "2. Compare every answer choice carefully against the predicted visual shape.\n"
        "3. Identify the correct option and its physical position (from left, from right, or vertical).\n"
        "4. Return strictly valid JSON with this exact schema:\n"
        "{\n"
        '  "question_category": "non_verbal_reasoning",\n'
        '  "subcategory": "Mirror Image | Water Image | Paper Folding | Embedded Figure | Odd One Out",\n'
        '  "assessment_format": "IMAGE_OPTIONS",\n'
        '  "is_image_options": true,\n'
        '  "option_label": "Option 2" | "Option 4" | "2" | "B" | null,\n'
        '  "option_index": 1,\n'
        '  "total_options": 4,\n'
        '  "orientation": "horizontal" | "vertical" | "grid",\n'
        '  "position_from_left": "2nd from LEFT",\n'
        '  "position_from_right": "3rd from RIGHT",\n'
        '  "full_answer": "Option 2 – Second image from the left",\n'
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
            subcategory=data.get("subcategory", "Visual Reasoning"),
            assessment_format=AssessmentFormat.IMAGE_OPTIONS,
            is_image_options=True,
            option_label=label,
            option_index=opt_idx,
            total_options=total,
            orientation=orientation,
            position_from_left=pos_left,
            position_from_right=pos_right,
            full_answer=full,
            confidence=float(data.get("confidence", 0.95)),
            needs_clarification=bool(data.get("needs_clarification", False)),
            missing_information=data.get("missing_information")
        )
        return ans
