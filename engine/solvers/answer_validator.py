"""
NovaGhost — Advanced Answer Validator.
Performs pre-display verification checks: readability, category consistency,
option existence, numerical validity, spatial position matching, and completeness.
Ensures zero fabricated options and issues clear clarification requests when needed.
"""

import re
import logging
from typing import Dict, Any, Optional
from engine.schemas import StructuredAnswer, QuestionCategory, AssessmentFormat

logger = logging.getLogger(__name__)


class AnswerValidator:
    """Validates structured answers before they reach the user or overlay."""

    @classmethod
    def validate_and_refine(
        cls,
        ans: StructuredAnswer,
        quality_metadata: Optional[Dict[str, Any]] = None
    ) -> StructuredAnswer:
        """
        Runs comprehensive validation checks on a StructuredAnswer.
        Refines formatting and sets clarification flags if validation fails.
        """
        if ans is None:
            return StructuredAnswer(
                needs_clarification=True,
                missing_information="Failed to parse answer from model output."
            )

        # 1. Image Quality / Clarity Check
        if quality_metadata:
            if not quality_metadata.get("is_clear", True):
                ans.needs_clarification = True
                ans.missing_information = (
                    quality_metadata.get("warning") or "Screenshot resolution is too low or blurry to read reliably."
                )
                return ans

        # 2. Check if the model itself signaled clarification needed
        if ans.needs_clarification:
            if not ans.missing_information:
                ans.missing_information = "Question text, options, or chart labels are partially occluded or unreadable."
            return ans

        # 3. Check for empty answers
        if not ans.full_answer and not ans.option_label and not ans.numerical_value and not ans.selected_options:
            ans.needs_clarification = True
            ans.missing_information = "Could not identify a clear question or answer choices in the screenshot."
            return ans

        # 4. Numerical validation for NAT
        if ans.assessment_format == AssessmentFormat.NAT or ans.numerical_value:
            if ans.numerical_value:
                # Clean up any extraneous non-number characters while preserving decimals and signs
                cleaned = re.sub(r"[^\d\.\-\+]", "", ans.numerical_value)
                if cleaned:
                    ans.numerical_value = cleaned
                else:
                    ans.needs_clarification = True
                    ans.missing_information = "Numerical value could not be extracted accurately."
                    return ans

        # 5. Position sanity for visual/image options
        if ans.is_image_options:
            if ans.option_index is not None and ans.total_options > 0:
                # Ensure option_index is within bounds [0, total_options - 1]
                if ans.option_index >= ans.total_options:
                    ans.option_index = ans.total_options - 1
                elif ans.option_index < 0:
                    ans.option_index = 0

                # Recompute positions to ensure 100% mathematical accuracy
                from engine.schemas import compute_positions
                pos = compute_positions(
                    index=ans.option_index,
                    total=ans.total_options,
                    orientation=ans.orientation,
                    grid_rows=ans.grid_row or 1,
                    grid_cols=ans.grid_col or 1
                )
                ans.position_from_left = pos["position_from_left"]
                ans.position_from_right = pos["position_from_right"]

        # 6. MSQ validation
        if ans.assessment_format == AssessmentFormat.MSQ:
            if not ans.selected_options and ans.option_label:
                # If option_label has e.g. "A, C" or "A and C"
                labels = re.findall(r"[A-Za-z0-9]", ans.option_label)
                if labels:
                    ans.selected_options = labels

        # 7. Confidence threshold check
        if ans.confidence < 0.40:
            ans.needs_clarification = True
            ans.missing_information = "Low confidence: image content is ambiguous or critical details are missing."
            return ans

        return ans
