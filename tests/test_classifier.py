"""
Tests for question classifier across all categories and formats.
"""

import unittest
from engine.schemas import QuestionCategory, AssessmentFormat
from engine.question_classifier import QuestionClassifier


class TestQuestionClassifier(unittest.TestCase):
    def test_numerical_aptitude_classification(self):
        cat, sub = QuestionClassifier.classify_text(
            "If A's salary is 30% more than B's salary, then by what percentage is B's salary less than A?"
        )
        self.assertEqual(cat, QuestionCategory.NUMERICAL_APTITUDE)
        self.assertEqual(sub, "Percentages")

        cat2, sub2 = QuestionClassifier.classify_text(
            "Find the cost price if a book is sold at 15% profit for Rs. 460."
        )
        self.assertEqual(cat2, QuestionCategory.NUMERICAL_APTITUDE)
        self.assertEqual(sub2, "Profit and Loss")

        cat3, sub3 = QuestionClassifier.classify_text(
            "Find the missing number in the number series: 2, 6, 12, 20, 30, ?"
        )
        self.assertEqual(cat3, QuestionCategory.NUMERICAL_APTITUDE)
        self.assertEqual(sub3, "Number Series")

    def test_data_interpretation_classification(self):
        cat, sub = QuestionClassifier.classify_text(
            "Directions (Q. Nos. 1 - 5) Study the following graph and pie chart carefully. "
            "What is the difference between the number of females in organisation B and organisation E?"
        )
        self.assertEqual(cat, QuestionCategory.DATA_INTERPRETATION)
        self.assertEqual(sub, "Pie Chart")

        cat2, sub2 = QuestionClassifier.classify_text(
            "Study the bar graph below showing production of cars in lakhs."
        )
        self.assertEqual(cat2, QuestionCategory.DATA_INTERPRETATION)
        self.assertEqual(sub2, "Bar Graph")

    def test_non_verbal_reasoning_classification(self):
        cat, sub = QuestionClassifier.classify_text(
            "A series is given with figure missing. Choose the correct 9th image from 4 options."
        )
        self.assertEqual(cat, QuestionCategory.NON_VERBAL_REASONING)
        self.assertEqual(sub, "Figure Series")

        cat2, sub2 = QuestionClassifier.classify_text(
            "Identify the correct mirror image of the given problem figure."
        )
        self.assertEqual(cat2, QuestionCategory.NON_VERBAL_REASONING)
        self.assertEqual(sub2, "Mirror Image")

        cat3, sub3 = QuestionClassifier.classify_text(
            "Predict the result after unfolding a folded paper cut as shown below."
        )
        self.assertEqual(cat3, QuestionCategory.NON_VERBAL_REASONING)
        self.assertEqual(sub3, "Paper Folding and Cutting")

    def test_logical_reasoning_classification(self):
        cat, sub = QuestionClassifier.classify_text(
            "Pointing to a photograph, a woman says: 'He is the only son of my father-in-law'. "
            "How is the person related to the woman's daughter?"
        )
        self.assertEqual(cat, QuestionCategory.LOGICAL_REASONING)
        self.assertEqual(sub, "Blood Relations")

        cat2, sub2 = QuestionClassifier.classify_text(
            "Eight friends A, B, C, D, E, F, G, H are sitting around a circular table facing the center."
        )
        self.assertEqual(cat2, QuestionCategory.LOGICAL_REASONING)
        self.assertEqual(sub2, "Seating Arrangement")

    def test_english_verbal_classification(self):
        cat, sub = QuestionClassifier.classify_text(
            "Choose the word that is closest in meaning (synonym) to PERSPICACIOUS."
        )
        self.assertEqual(cat, QuestionCategory.ENGLISH_VERBAL)
        self.assertEqual(sub, "Synonyms")

    def test_technical_knowledge_classification(self):
        cat, sub = QuestionClassifier.classify_text(
            "Which normal form eliminates partial dependency on a composite primary key in DBMS SQL?"
        )
        self.assertEqual(cat, QuestionCategory.TECHNICAL_KNOWLEDGE)
        self.assertEqual(sub, "DBMS & SQL")

        cat2, sub2 = QuestionClassifier.classify_text(
            "In operating systems, which condition is NOT necessary for deadlock occurrence?"
        )
        self.assertEqual(cat2, QuestionCategory.TECHNICAL_KNOWLEDGE)
        self.assertEqual(sub2, "Operating Systems")

    def test_assessment_format_detection(self):
        fmt1 = QuestionClassifier.detect_assessment_format("Choose all that apply. Select multiple answers.")
        self.assertEqual(fmt1, AssessmentFormat.MSQ)

        fmt2 = QuestionClassifier.detect_assessment_format("Numerical Answer Type (NAT). Type only the value:")
        self.assertEqual(fmt2, AssessmentFormat.NAT)

        fmt3 = QuestionClassifier.detect_assessment_format("A) 12  B) 24  C) 36  D) 48")
        self.assertEqual(fmt3, AssessmentFormat.MCQ)

        fmt4 = QuestionClassifier.detect_assessment_format("Pick image", has_image_options=True)
        self.assertEqual(fmt4, AssessmentFormat.IMAGE_OPTIONS)


if __name__ == "__main__":
    unittest.main()
