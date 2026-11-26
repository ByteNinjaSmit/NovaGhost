"""
NovaGhost — Schemas, Question Categories, Assessment Formats & Structured Models.
Defines domain data structures, position calculation utilities, and output formatting.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


class QuestionCategory(str, Enum):
    NUMERICAL_APTITUDE = "numerical_aptitude"
    DATA_INTERPRETATION = "data_interpretation"
    NON_VERBAL_REASONING = "non_verbal_reasoning"
    LOGICAL_REASONING = "logical_reasoning"
    ENGLISH_VERBAL = "english_verbal"
    TECHNICAL_KNOWLEDGE = "technical_knowledge"
    UNCLEAR = "unclear"


class AssessmentFormat(str, Enum):
    MCQ = "MCQ"                     # Single choice text/labeled
    MSQ = "MSQ"                     # Multiple select questions
    NAT = "NAT"                     # Numerical Answer Type (value only)
    IMAGE_OPTIONS = "IMAGE_OPTIONS" # Options are visual figures/unlabeled
    FILL_BLANKS = "FILL_BLANKS"     # Text or missing word input
    TITA = "TITA"                   # Type in the answer
    UNCLEAR = "UNCLEAR"


def ordinal_str(n: int) -> str:
    """Returns ordinal string: 1 -> '1st', 2 -> '2nd', 3 -> '3rd', etc."""
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    return f"{n}{suffix}"


def compute_positions(
    index: int,
    total: int,
    orientation: str = "horizontal",
    grid_rows: int = 1,
    grid_cols: int = 1
) -> Dict[str, Optional[str]]:
    """
    Computes unambiguous position designations for options:
    - 1st from LEFT / 1st from RIGHT
    - TOP / MIDDLE / BOTTOM
    - ROW r, COLUMN c
    """
    pos_info: Dict[str, Optional[str]] = {
        "position_from_left": None,
        "position_from_right": None,
        "vertical_position": None,
        "grid_position": None,
        "summary": ""
    }

    if total <= 0 or index < 0 or index >= total:
        return pos_info

    # 1-based indexing for humans
    idx_from_start = index + 1
    idx_from_end = total - index

    # Horizontal position
    pos_info["position_from_left"] = f"{ordinal_str(idx_from_start)} from LEFT"
    pos_info["position_from_right"] = f"{ordinal_str(idx_from_end)} from RIGHT"

    # Vertical position
    if total == 2:
        pos_info["vertical_position"] = "TOP" if index == 0 else "BOTTOM"
    elif total == 3:
        pos_info["vertical_position"] = "TOP" if index == 0 else ("MIDDLE" if index == 1 else "BOTTOM")
    else:
        pos_info["vertical_position"] = f"{ordinal_str(idx_from_start)} from TOP"

    # Grid position if applicable
    if grid_cols > 1 and grid_rows > 1:
        row = (index // grid_cols) + 1
        col = (index % grid_cols) + 1
        pos_info["grid_position"] = f"ROW {row}, COLUMN {col}"

    # Default summary based on orientation
    if orientation == "grid" and pos_info["grid_position"]:
        pos_info["summary"] = pos_info["grid_position"]
    elif orientation == "vertical":
        pos_info["summary"] = f"{pos_info['vertical_position']} ({pos_info['position_from_left']})"
    else:
        pos_info["summary"] = f"{pos_info['position_from_left']} (Equivalent: {pos_info['position_from_right']})"

    return pos_info


@dataclass
class StructuredAnswer:
    question_category: QuestionCategory = QuestionCategory.NUMERICAL_APTITUDE
    subcategory: str = "General"
    assessment_format: AssessmentFormat = AssessmentFormat.MCQ
    
    # Selection fields
    is_image_options: bool = False
    option_label: Optional[str] = None          # e.g., 'C', 'Option 2', '2'
    option_index: Optional[int] = None          # 0-indexed
    total_options: int = 4
    selected_options: List[str] = field(default_factory=list) # e.g., ['A', 'C'] for MSQ
    
    # Exact value / text
    numerical_value: Optional[str] = None       # e.g., '1250.50'
    full_answer: str = ""                       # Complete answer text as displayed
    
    # Positioning
    orientation: str = "horizontal"             # 'horizontal', 'vertical', 'grid'
    grid_row: Optional[int] = None
    grid_col: Optional[int] = None
    position_from_left: Optional[str] = None
    position_from_right: Optional[str] = None
    
    # Verification & confidence
    confidence: float = 0.95
    needs_clarification: bool = False
    missing_information: Optional[str] = None
    raw_response: str = ""

    def __post_init__(self):
        # Auto-compute positions if index and total are provided
        if self.option_index is not None and self.total_options > 0:
            pos = compute_positions(
                index=self.option_index,
                total=self.total_options,
                orientation=self.orientation,
                grid_rows=self.grid_row or 1,
                grid_cols=self.grid_col or 1
            )
            if not self.position_from_left:
                self.position_from_left = pos["position_from_left"]
            if not self.position_from_right:
                self.position_from_right = pos["position_from_right"]

    def to_strict_format(self) -> str:
        """
        Formats according to the strict requirements of Phase 6:
        Format A — Labeled image options
        Format B — Unlabeled image options
        Format C — MCQ
        Format D — Numerical Answer Type (NAT)
        Format E — MSQ
        Format F — Data Interpretation
        Format G — Unclear screenshot
        NO EXPLANATIONS. NO FILLER TEXT. COMPLETE VALUES ONLY.
        """
        if self.needs_clarification:
            missing = self.missing_information or "Question text, options, or chart data unreadable"
            return (
                "SCREENSHOT UNCLEAR\n\n"
                f"MISSING INFORMATION: {missing}\n\n"
                "REQUEST: Upload a clearer screenshot."
            )

        # Format D: NAT (Numerical Answer Type)
        if self.assessment_format in (AssessmentFormat.NAT, AssessmentFormat.TITA) or (
            self.numerical_value is not None and not self.option_label and not self.selected_options
        ):
            val = self.numerical_value or self.full_answer
            return f"ENTER THIS VALUE:\n\n{val.strip()}"

        # Format E: MSQ (Multiple Select Questions)
        if self.assessment_format == AssessmentFormat.MSQ or len(self.selected_options) > 1:
            opts = [o.strip() for o in self.selected_options if o.strip()]
            opts_str = ", ".join(opts) if opts else (self.option_label or "A")
            select_str = " and ".join(opts) if opts else opts_str
            ans_lines = [
                f"CORRECT OPTIONS: {opts_str}",
                f"SELECT: {select_str}"
            ]
            if self.full_answer and self.full_answer not in (opts_str, select_str):
                ans_lines.append(f"FULL ANSWER: {self.full_answer.strip()}")
            return "\n\n".join(ans_lines)

        # Format F: Data Interpretation
        if self.question_category == QuestionCategory.DATA_INTERPRETATION:
            if self.assessment_format == AssessmentFormat.NAT:
                val = self.numerical_value or self.full_answer
                return f"ENTER THIS VALUE:\n\n{val.strip()}"
            lbl = self.option_label or "A"
            full = self.full_answer or self.numerical_value or lbl
            return f"CORRECT OPTION: {lbl}\n\nFULL ANSWER: {full.strip()}"

        # Format A: Labeled Image Options (e.g. Option 2 / Figure 2)
        if self.is_image_options and self.option_label:
            lines = [f"CORRECT ANSWER: {self.option_label.upper()}"]
            if self.position_from_left:
                lines.append(f"POSITION: {self.position_from_left}")
            if self.position_from_right:
                lines.append(f"POSITION FROM RIGHT: {self.position_from_right}")
            if self.grid_row is not None and self.grid_col is not None:
                lines.append(f"GRID POSITION: ROW {self.grid_row}, COLUMN {self.grid_col}")
            if self.full_answer and self.full_answer.lower() != self.option_label.lower():
                lines.append(f"FULL ANSWER: {self.full_answer.strip()}")
            return "\n\n".join(lines)

        # Format B: Unlabeled Image Options (Position-based)
        if self.is_image_options and not self.option_label:
            pos_left = self.position_from_left or (
                f"{ordinal_str((self.option_index or 0) + 1)} image from LEFT"
            )
            pos_right = self.position_from_right or (
                f"{ordinal_str(self.total_options - (self.option_index or 0))} image from RIGHT"
            )
            lines = [
                f"CORRECT ANSWER: {pos_left}",
                f"POSITION: {pos_right}"
            ]
            if self.grid_row is not None and self.grid_col is not None:
                lines.append(f"GRID POSITION: ROW {self.grid_row}, COLUMN {self.grid_col}")
            if self.full_answer:
                lines.append(f"FULL ANSWER: {self.full_answer.strip()}")
            return "\n\n".join(lines)

        # Format C: Standard MCQ
        opt_lbl = self.option_label or "A"
        full = self.full_answer or opt_lbl
        return f"CORRECT OPTION: {opt_lbl}\n\nFULL ANSWER: {full.strip()}"


@dataclass
class MultiQuestionResult:
    """Encapsulates one or multiple questions detected in a single screenshot."""
    questions: List[StructuredAnswer] = field(default_factory=list)
    active_index: int = 0
    is_multi_question: bool = False
    is_cached: bool = False

    def __post_init__(self):
        if len(self.questions) > 1:
            self.is_multi_question = True

    def get_active_answer(self) -> Optional[StructuredAnswer]:
        if not self.questions:
            return None
        idx = max(0, min(self.active_index, len(self.questions) - 1))
        return self.questions[idx]

    def to_strict_format(self, specific_index: Optional[int] = None) -> str:
        if not self.questions:
            return "SCREENSHOT UNCLEAR\n\nMISSING INFORMATION: No questions detected\n\nREQUEST: Upload a clearer screenshot."

        if specific_index is not None:
            idx = max(0, min(specific_index, len(self.questions) - 1))
            prefix = f"QUESTION {idx + 1} OF {len(self.questions)}\n\n" if self.is_multi_question else ""
            return prefix + self.questions[idx].to_strict_format()

        if not self.is_multi_question or len(self.questions) == 1:
            return self.questions[0].to_strict_format()

        blocks = []
        for i, q in enumerate(self.questions):
            header = f"QUESTION {i + 1} OF {len(self.questions)}"
            content = q.to_strict_format()
            blocks.append(f"{header}\n\n{content}")
        separator = "\n\n" + ("─" * 32) + "\n\n"
        return separator.join(blocks)

