"""
NovaGhost — Universal Question Classification Engine.
Classifies visual questions across Numerical Aptitude, Data Interpretation,
Non-Verbal & Visual Reasoning, Logical Reasoning, English/Verbal, and Technical MCQs.
"""

import re
import logging
from typing import Dict, Any, Tuple, Optional
from engine.schemas import QuestionCategory, AssessmentFormat

logger = logging.getLogger(__name__)

# Keywords associated with each category
CATEGORY_KEYWORDS = {
    QuestionCategory.NUMERICAL_APTITUDE: [
        "salary", "percent", "%", "profit", "loss", "cost price", "selling price",
        "marked price", "discount", "simple interest", "compound interest", "ratio",
        "proportion", "average", "mean", "time and work", "speed", "distance",
        "train", "upstream", "downstream", "age", "years old", "probability",
        "permutation", "combination", "number series", "find the missing number",
        "arithmetic", "geometric", "hcf", "lcm", "fraction", "pipe and cistern"
    ],
    QuestionCategory.DATA_INTERPRETATION: [
        "graph", "chart", "pie chart", "bar graph", "bar chart", "line graph",
        "table", "study the following table", "study the following graph",
        "directions (q. nos.", "sales in lakhs", "expenditure", "revenue",
        "organisation", "organization", "difference between the number of",
        "females in", "males in", "production of", "data given below"
    ],
    QuestionCategory.NON_VERBAL_REASONING: [
        "figure", "missing figure", "figure series", "figure matrix", "matrix",
        "pattern", "unfolding", "paper folding", "paper cutting", "folded",
        "mirror image", "water image", "embedded figure", "hidden shape",
        "odd one out", "rotation", "reflected", "inverted", "abstract",
        "choose the correct figure", "next figure", "9th image", "problem figure",
        "answer figure", "analogy figure", "spatial"
    ],
    QuestionCategory.LOGICAL_REASONING: [
        "blood relation", "mother", "father", "son", "daughter", "sister",
        "brother", "uncle", "aunt", "direction", "facing north", "facing south",
        "turns left", "turns right", "seating arrangement", "circular table",
        "sitting around", "syllogism", "all cats are", "some dogs are",
        "statement and conclusion", "statement and assumption", "puzzle",
        "ranking", "ordered from top", "clocks", "calendar", "day of the week",
        "coding-decoding", "if in a code language", "coded as", "related to",
        "father-in-law", "mother-in-law"
    ],
    QuestionCategory.ENGLISH_VERBAL: [
        "synonym", "antonym", "opposite meaning", "closest in meaning",
        "sentence correction", "fill in the blank", "grammar", "grammatical",
        "grammatical error", "para jumble", "error detection", "spotting errors",
        "reading comprehension", "passage", "according to the author",
        "according to the passage", "vocabulary", "idiom", "phrase",
        "sentence", "find the error in the sentence"
    ],
    QuestionCategory.TECHNICAL_KNOWLEDGE: [
        "dbms", "database", "sql", "operating system", "process", "thread",
        "deadlock", "memory management", "cpu scheduling", "computer network",
        "tcp/ip", "osi model", "packet", "router", "switch", "normalization",
        "foreign key", "primary key", "computer fundamentals", "cache memory",
        "software engineering", "sdlc", "output of the following"
    ]
}


class QuestionClassifier:
    """Classifies questions into universal aptitude categories and assessment formats."""

    @classmethod
    def classify_text(cls, text: str) -> Tuple[QuestionCategory, str]:
        """
        Classifies given text based on weighted keyword matching.
        Returns (QuestionCategory, subcategory_name).
        """
        if not text or not text.strip():
            return QuestionCategory.NUMERICAL_APTITUDE, "General"

        lower_text = text.lower()
        scores: Dict[QuestionCategory, int] = {cat: 0 for cat in CATEGORY_KEYWORDS}

        for cat, keywords in CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw in lower_text:
                    # Give higher weight to multi-word phrases
                    weight = 3 if " " in kw else 1
                    scores[cat] += weight

        best_cat = max(scores, key=lambda k: scores[k])
        if scores[best_cat] == 0:
            return QuestionCategory.NUMERICAL_APTITUDE, "General"

        # Determine subcategory
        subcat = cls._determine_subcategory(best_cat, lower_text)
        return best_cat, subcat

    @classmethod
    def _determine_subcategory(cls, cat: QuestionCategory, lower_text: str) -> str:
        if cat == QuestionCategory.NUMERICAL_APTITUDE:
            if "profit" in lower_text or "loss" in lower_text:
                return "Profit and Loss"
            if "percent" in lower_text or "%" in lower_text:
                return "Percentages"
            if "interest" in lower_text:
                return "Simple / Compound Interest"
            if "ratio" in lower_text or "proportion" in lower_text:
                return "Ratio and Proportion"
            if "average" in lower_text or "mean" in lower_text:
                return "Average"
            if "work" in lower_text or "pipe" in lower_text:
                return "Time and Work"
            if "speed" in lower_text or "distance" in lower_text or "train" in lower_text:
                return "Speed, Distance and Time"
            if "probability" in lower_text:
                return "Probability"
            if "series" in lower_text or "missing number" in lower_text:
                return "Number Series"
            return "Quantitative Aptitude"

        if cat == QuestionCategory.DATA_INTERPRETATION:
            if "pie" in lower_text:
                return "Pie Chart"
            if "bar" in lower_text:
                return "Bar Graph"
            if "line" in lower_text:
                return "Line Graph"
            if "table" in lower_text:
                return "Table Data"
            return "Data Interpretation"

        if cat == QuestionCategory.NON_VERBAL_REASONING:
            if "mirror" in lower_text:
                return "Mirror Image"
            if "water" in lower_text:
                return "Water Image"
            if "paper" in lower_text or "folding" in lower_text:
                return "Paper Folding and Cutting"
            if "embedded" in lower_text or "hidden" in lower_text:
                return "Embedded Figures"
            if "matrix" in lower_text:
                return "Figure Matrix"
            if "series" in lower_text or "9th image" in lower_text or "next figure" in lower_text:
                return "Figure Series"
            if "odd one" in lower_text:
                return "Odd One Out"
            return "Visual Reasoning"

        if cat == QuestionCategory.LOGICAL_REASONING:
            if any(k in lower_text for k in ["blood", "father", "mother", "son", "daughter", "uncle", "aunt", "related"]):
                return "Blood Relations"
            if "direction" in lower_text or "walks" in lower_text:
                return "Direction Sense"
            if "seat" in lower_text or "sitting" in lower_text or "circular table" in lower_text:
                return "Seating Arrangement"
            if "syllogism" in lower_text:
                return "Syllogisms"
            if "statement" in lower_text:
                return "Statement and Conclusion"
            if "code" in lower_text or "coding" in lower_text:
                return "Coding-Decoding"
            return "Logical Reasoning"

        if cat == QuestionCategory.ENGLISH_VERBAL:
            if "synonym" in lower_text or "closest in meaning" in lower_text:
                return "Synonyms"
            if "antonym" in lower_text or "opposite" in lower_text:
                return "Antonyms"
            if "passage" in lower_text or "comprehension" in lower_text or "author" in lower_text:
                return "Reading Comprehension"
            if "grammar" in lower_text or "error" in lower_text or "grammatical" in lower_text:
                return "Sentence Correction & Grammar"
            return "Verbal Ability"

        if cat == QuestionCategory.TECHNICAL_KNOWLEDGE:
            if "sql" in lower_text or "dbms" in lower_text:
                return "DBMS & SQL"
            if "operating system" in lower_text or "os" in lower_text or "deadlock" in lower_text:
                return "Operating Systems"
            if "network" in lower_text or "tcp" in lower_text:
                return "Computer Networks"
            return "Computer Fundamentals"

        return "General"

    @classmethod
    def detect_assessment_format(cls, text: str, has_image_options: bool = False) -> AssessmentFormat:
        """Detects whether question format is MCQ, MSQ, NAT, or IMAGE_OPTIONS."""
        if has_image_options:
            return AssessmentFormat.IMAGE_OPTIONS

        lower = text.lower() if text else ""
        if "select multiple" in lower or "choose all that apply" in lower or "msq" in lower:
            return AssessmentFormat.MSQ

        if "numerical answer" in lower or "enter this value" in lower or "nat" in lower or "type only the value" in lower:
            return AssessmentFormat.NAT

        # Check for multiple options like A, B, C, D
        if re.search(r"(\([A-Da-d1-4]\)|[A-Da-d1-4]\.|\bOption [A-Da-d1-4]\b)", text):
            return AssessmentFormat.MCQ

        return AssessmentFormat.MCQ

    @classmethod
    def parse_category_from_response(cls, cat_str: str) -> QuestionCategory:
        """Safely parses model output string into a QuestionCategory enum."""
        if not cat_str:
            return QuestionCategory.NUMERICAL_APTITUDE

        clean = cat_str.strip().lower().replace("-", "_").replace(" ", "_")
        for member in QuestionCategory:
            if member.value == clean or clean in member.value or member.value in clean:
                return member

        if "num" in clean or "math" in clean or "quant" in clean:
            return QuestionCategory.NUMERICAL_APTITUDE
        if "data" in clean or "chart" in clean or "graph" in clean or "table" in clean:
            return QuestionCategory.DATA_INTERPRETATION
        if "visual" in clean or "non_verbal" in clean or "figure" in clean or "matrix" in clean:
            return QuestionCategory.NON_VERBAL_REASONING
        if "logic" in clean or "reasoning" in clean:
            return QuestionCategory.LOGICAL_REASONING
        if "english" in clean or "verbal" in clean:
            return QuestionCategory.ENGLISH_VERBAL
        if "tech" in clean or "computer" in clean or "dbms" in clean:
            return QuestionCategory.TECHNICAL_KNOWLEDGE

        return QuestionCategory.NUMERICAL_APTITUDE
