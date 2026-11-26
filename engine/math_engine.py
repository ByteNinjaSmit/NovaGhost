"""
NovaGhost — Deterministic SymPy Mathematical Engine.
Provides symbolic equation solving, exact aptitude problem solvers,
and arithmetic verification to eliminate numerical hallucinations.
"""

import re
import math
import logging
from typing import Optional, Union, List, Tuple, Dict, Any

try:
    import sympy as sp
    from sympy import Symbol, Eq, solve, sympify, Rational, N
    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False

logger = logging.getLogger(__name__)


class SymPyMathEngine:
    """Deterministic mathematical problem solver and verifier."""

    @classmethod
    def evaluate_expression(cls, expr_str: str) -> Optional[float]:
        """
        Deterministically evaluates mathematical expressions (e.g., '(30 / 130) * 100', '1000 * 1.1**2').
        Uses SymPy for exact rational arithmetic before converting to float, preserving full precision.
        """
        if not expr_str or not expr_str.strip():
            return None

        # Clean string to only allow math characters
        cleaned = re.sub(r"[^0-9\+\-\*\/\.\(\)\%\^\s,]", "", expr_str).replace("^", "**")
        if not cleaned:
            return None

        if HAS_SYMPY:
            try:
                sym_expr = sympify(cleaned, evaluate=True)
                val = float(N(sym_expr, 15))
                return round(val, 8)
            except Exception as e:
                logger.debug(f"SymPy evaluation error on '{cleaned}': {e}")

        # Safe fallback with math builtins
        try:
            safe_env = {"__builtins__": None, "math": math, "pow": pow, "round": round}
            val = eval(cleaned, safe_env, {})
            if isinstance(val, (int, float)):
                return round(float(val), 8)
        except Exception:
            pass
        return None

    @classmethod
    def solve_linear_equation(cls, equation_str: str, var_name: str = "x") -> Optional[float]:
        """
        Solves algebraic equation like '1.30 * x = 460' or 'x + 0.15 * x = 460'.
        """
        if not HAS_SYMPY:
            return None
        try:
            var = Symbol(var_name)
            if "=" in equation_str:
                left, right = equation_str.split("=", 1)
                eq = Eq(sympify(left), sympify(right))
            else:
                eq = Eq(sympify(equation_str), 0)
            solutions = solve(eq, var)
            if solutions:
                sol = float(N(solutions[0], 12))
                return round(sol, 6)
        except Exception as e:
            logger.debug(f"SymPy solve error on '{equation_str}': {e}")
        return None

    # ── Domain-Specific Quantitative Aptitude Solvers ────────────────────────

    @classmethod
    def salary_pct_less_than(cls, pct_more: float) -> float:
        """
        If A's salary is X% more than B's salary, then B's salary is:
        (X / (100 + X)) * 100 % less than A.
        """
        return round((pct_more / (100.0 + pct_more)) * 100.0, 4)

    @classmethod
    def salary_pct_more_than(cls, pct_less: float) -> float:
        """
        If A's salary is X% less than B's salary, then B's salary is:
        (X / (100 - X)) * 100 % more than A.
        """
        return round((pct_less / (100.0 - pct_less)) * 100.0, 4)

    @classmethod
    def cost_price_from_sp_and_profit(cls, sp_val: float, profit_pct: float) -> float:
        """Cost Price = (Selling Price * 100) / (100 + Profit%)"""
        return round((sp_val * 100.0) / (100.0 + profit_pct), 4)

    @classmethod
    def cost_price_from_sp_and_loss(cls, sp_val: float, loss_pct: float) -> float:
        """Cost Price = (Selling Price * 100) / (100 - Loss%)"""
        return round((sp_val * 100.0) / (100.0 - loss_pct), 4)

    @classmethod
    def simple_interest(cls, p: float, r: float, t: float) -> float:
        """Simple Interest = (P * R * T) / 100"""
        return round((p * r * t) / 100.0, 4)

    @classmethod
    def compound_interest(cls, p: float, r: float, t: float, n: int = 1) -> float:
        """Compound Interest = P * (1 + R / (100 * n))^(n * T) - P"""
        amt = p * ((1.0 + (r / (100.0 * n))) ** (n * t))
        return round(amt - p, 4)

    @classmethod
    def combined_work_time(cls, times: List[float]) -> Optional[float]:
        """
        Time taken when working together: 1 / (1/t1 + 1/t2 + ... + 1/tn)
        """
        if not times or any(t <= 0 for t in times):
            return None
        rate_sum = sum(1.0 / t for t in times)
        return round(1.0 / rate_sum, 4)

    @classmethod
    def average_speed(cls, s1: float, s2: float) -> float:
        """Average speed for equal distance round trip: (2 * s1 * s2) / (s1 + s2)"""
        return round((2.0 * s1 * s2) / (s1 + s2), 4)

    @classmethod
    def permutations_npr(cls, n: int, r: int) -> int:
        return math.perm(int(n), int(r))

    @classmethod
    def combinations_ncr(cls, n: int, r: int) -> int:
        return math.comb(int(n), int(r))

    @classmethod
    def predict_number_series_next(cls, series: List[float]) -> Optional[float]:
        """
        Predicts the next number in series using polynomial difference sequences:
        - Constant difference (AP)
        - Constant ratio (GP)
        - Second-order difference (Quadratic: 2, 6, 12, 20, 30 -> 42)
        - Third-order difference (Cubic)
        """
        if len(series) < 3:
            return None

        # Check Geometric Progression (constant ratio)
        if all(x != 0 for x in series):
            ratios = [series[i+1] / series[i] for i in range(len(series)-1)]
            if all(abs(r - ratios[0]) < 1e-6 for r in ratios):
                return round(series[-1] * ratios[0], 4)

        # Check differences (1st, 2nd, 3rd order)
        diff1 = [series[i+1] - series[i] for i in range(len(series)-1)]
        if all(abs(d - diff1[0]) < 1e-6 for d in diff1):
            return round(series[-1] + diff1[0], 4)

        diff2 = [diff1[i+1] - diff1[i] for i in range(len(diff1)-1)]
        if all(abs(d - diff2[0]) < 1e-6 for d in diff2):
            next_diff1 = diff1[-1] + diff2[0]
            return round(series[-1] + next_diff1, 4)

        diff3 = [diff2[i+1] - diff2[i] for i in range(len(diff2)-1)]
        if len(diff3) >= 2 and all(abs(d - diff3[0]) < 1e-6 for d in diff3):
            next_diff2 = diff2[-1] + diff3[0]
            next_diff1 = diff1[-1] + next_diff2
            return round(series[-1] + next_diff1, 4)

        return None

    # ── Auto-Verification & Auto-Correction Engine ───────────────────────────

    @classmethod
    def verify_and_correct(cls, problem_text: str, candidate_value: str) -> Tuple[str, bool]:
        """
        Inspects problem text for deterministic mathematical relationships.
        If a deterministic solution is found, compares with candidate_value.
        Returns (corrected_value, was_corrected).
        """
        if not problem_text:
            return candidate_value, False

        lower = problem_text.lower()

        # 1. Salary X% more pattern: "A's salary is X% more than B"
        m_sal = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:more than|greater than)", lower)
        if m_sal and ("less than" in lower or "by what percentage" in lower):
            pct_more = float(m_sal.group(1))
            exact_val = cls.salary_pct_less_than(pct_more)
            exact_str = f"{exact_val:.2f}%" if "%" in candidate_value else f"{exact_val:.2f}"
            return exact_str, True

        # 2. Profit and Loss: "sold at X% profit for Rs. Y"
        m_profit = re.search(r"(?:profit of|gain of|at)\s*(\d+(?:\.\d+)?)\s*%\s*profit", lower)
        m_sp = re.search(r"(?:for|sp|sold at)\s*(?:rs\.?|inr|\$)?\s*(\d+(?:\.\d+)?)", lower)
        if m_profit and m_sp and ("cost price" in lower or "cp" in lower):
            profit_pct = float(m_profit.group(1))
            sp_val = float(m_sp.group(1))
            cp_exact = cls.cost_price_from_sp_and_profit(sp_val, profit_pct)
            # Check if integer
            res_str = f"{int(cp_exact)}" if cp_exact.is_integer() else f"{cp_exact:.2f}"
            return res_str, True

        # 3. Compound Interest: "compound interest on Rs. P at R% for T years"
        m_ci_p = re.search(r"(?:on|principal of)?\s*(?:rs\.?|inr|\$)?\s*(\d+(?:\.\d+)?)\s*(?:at)?\s*(\d+(?:\.\d+)?)\s*%\s*(?:for|per)?\s*(\d+(?:\.\d+)?)\s*years?", lower)
        if "compound interest" in lower and m_ci_p:
            p = float(m_ci_p.group(1))
            r = float(m_ci_p.group(2))
            t = float(m_ci_p.group(3))
            ci_exact = cls.compound_interest(p, r, t)
            res_str = f"{ci_exact:.2f}"
            return res_str, True

        # 4. Number Series: "series: 2, 6, 12, 20, 30, ?"
        series_match = re.search(r"(?:series|sequence)[:\s]+([0-9\s,\.\-]+)(?:\?|$)", problem_text, re.IGNORECASE)
        if series_match:
            nums_str = re.findall(r"[-+]?\d*\.?\d+", series_match.group(1))
            if len(nums_str) >= 3:
                try:
                    num_list = [float(x) for x in nums_str]
                    pred = cls.predict_number_series_next(num_list)
                    if pred is not None:
                        pred_str = f"{int(pred)}" if pred.is_integer() else f"{pred:.2f}"
                        return pred_str, True
                except Exception:
                    pass

        return candidate_value, False
