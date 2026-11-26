"""
NovaGhost — Figure Series & Non-Verbal Reasoning Solver.
Analyzes 8-image sequences to find the 9th missing image, progressive transformations,
rotations, reflections, movements, shading, and shape counts.
Compares every available option before selecting the exact option number and physical position.
"""

import logging
from typing import Dict, Any, Optional
from engine.schemas import QuestionCategory, AssessmentFormat, StructuredAnswer, compute_positions

logger = logging.getLogger(__name__)


class FigureSeriesSolver:
    """Specialized solver for Figure Series, Sequences & Non-Verbal Transformations."""

    SYSTEM_PROMPT = (
        "You are an elite Visual Reasoning & Figure Series Intelligence Engine.\n"
        "Your task is to analyze non-verbal figure series (e.g., 8 images leading to a missing 9th image, "
        "or 4-5 sequential problem figures) and identify the correct option among the answer choices.\n\n"
        "ANALYSIS PROCEDURE:\n"
        "1. Identify the transformation rules in the sequence:\n"
        "   - Rotation: Clockwise or counter-clockwise (45°, 90°, 135°, 180°).\n"
        "   - Movement/Position: Elements moving along corners, sides, or centers.\n"
        "   - Count/Quantity: Shapes increasing, decreasing, or following an arithmetic pattern.\n"
        "   - Shading/Fill: Alternating filled/empty, cyclic patterns, or quadrant shading.\n"
        "   - Reflection/Inversion: Mirror reflection across vertical or horizontal axis.\n"
        "   - Addition/Deletion: Lines or dots added or removed progressively.\n"
        "2. Formulate the exact visual profile of the missing target figure.\n"
        "3. Systematically compare EVERY available answer option against your predicted figure.\n"
        "4. Determine the exact option number (e.g. 'Option 2' or '2') and its physical position:\n"
        "   - From LEFT: (1st from LEFT, 2nd from LEFT, 3rd from LEFT, etc.)\n"
        "   - From RIGHT: (1st from RIGHT, 2nd from RIGHT, 3rd from RIGHT, etc.)\n"
        "5. Return strictly valid JSON with this exact schema:\n"
        "{\n"
        '  "question_category": "non_verbal_reasoning",\n'
        '  "subcategory": "Figure Series",\n'
        '  "assessment_format": "IMAGE_OPTIONS",\n'
        '  "is_image_options": true,\n'
        '  "option_label": "Option 2" | "Option 1" | "2" | "B" | null,\n'
        '  "option_index": 1,\n'
        '  "total_options": 4,\n'
        '  "orientation": "horizontal" | "vertical" | "grid",\n'
        '  "position_from_left": "2nd from LEFT",\n'
        '  "position_from_right": "3rd from RIGHT",\n'
        '  "full_answer": "Option 2 – Second image from the left",\n'
        '  "pattern_rule": "Detailed rule explanation for internal verification",\n'
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

        # Normalize option index if only label was provided
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
            subcategory="Figure Series",
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
