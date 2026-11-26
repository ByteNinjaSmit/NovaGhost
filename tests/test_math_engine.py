"""
Tests for Deterministic SymPy Mathematical Engine.
"""

import unittest
from engine.math_engine import SymPyMathEngine


class TestSymPyMathEngine(unittest.TestCase):
    def test_evaluate_expression(self):
        val = SymPyMathEngine.evaluate_expression("(30 / 130) * 100")
        self.assertAlmostEqual(val, 23.076923, places=4)

        val_pow = SymPyMathEngine.evaluate_expression("1000 * (1.10 ^ 2)")
        self.assertAlmostEqual(val_pow, 1210.0, places=2)

    def test_solve_linear_equation(self):
        sol = SymPyMathEngine.solve_linear_equation("1.15 * x = 460")
        self.assertEqual(sol, 400.0)

        sol2 = SymPyMathEngine.solve_linear_equation("2 * x + 10 = 50")
        self.assertEqual(sol2, 20.0)

    def test_salary_percentage_relationships(self):
        # A is 30% more than B -> B is 23.0769% less than A
        pct_less = SymPyMathEngine.salary_pct_less_than(30.0)
        self.assertAlmostEqual(pct_less, 23.0769, places=2)

        # A is 20% less than B -> B is 25% more than A
        pct_more = SymPyMathEngine.salary_pct_more_than(20.0)
        self.assertEqual(pct_more, 25.0)

    def test_profit_and_loss(self):
        # Sold at 15% profit for Rs. 460 -> CP = 400
        cp = SymPyMathEngine.cost_price_from_sp_and_profit(460.0, 15.0)
        self.assertEqual(cp, 400.0)

        # Sold at 20% loss for Rs. 400 -> CP = 500
        cp_loss = SymPyMathEngine.cost_price_from_sp_and_loss(400.0, 20.0)
        self.assertEqual(cp_loss, 500.0)

    def test_interest_calculations(self):
        si = SymPyMathEngine.simple_interest(10000, 10, 2)
        self.assertEqual(si, 2000.0)

        ci = SymPyMathEngine.compound_interest(10000, 10, 2)
        self.assertEqual(ci, 2100.0)

    def test_time_and_work(self):
        # A takes 10 days, B takes 15 days -> combined = 6 days
        t = SymPyMathEngine.combined_work_time([10, 15])
        self.assertEqual(t, 6.0)

    def test_average_speed(self):
        # 60 km/h going, 40 km/h returning -> 48 km/h
        avg_s = SymPyMathEngine.average_speed(60, 40)
        self.assertEqual(avg_s, 48.0)

    def test_permutations_and_combinations(self):
        self.assertEqual(SymPyMathEngine.permutations_npr(5, 2), 20)
        self.assertEqual(SymPyMathEngine.combinations_ncr(5, 2), 10)

    def test_number_series_predictor(self):
        # AP: 2, 5, 8, 11 -> 14
        next_ap = SymPyMathEngine.predict_number_series_next([2, 5, 8, 11])
        self.assertEqual(next_ap, 14.0)

        # GP: 3, 6, 12, 24 -> 48
        next_gp = SymPyMathEngine.predict_number_series_next([3, 6, 12, 24])
        self.assertEqual(next_gp, 48.0)

        # Quadratic: 2, 6, 12, 20, 30 -> 42
        next_quad = SymPyMathEngine.predict_number_series_next([2, 6, 12, 20, 30])
        self.assertEqual(next_quad, 42.0)

    def test_verify_and_correct(self):
        text = "If A's salary is 30% more than B's salary, then by what percentage is B's salary less than A?"
        corr, was_corr = SymPyMathEngine.verify_and_correct(text, "23%")
        self.assertTrue(was_corr)
        self.assertIn("23.08", corr)


if __name__ == "__main__":
    unittest.main()
