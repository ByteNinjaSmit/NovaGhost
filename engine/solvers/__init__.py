"""
NovaGhost — Specialized Solvers Package.
Contains domain-specific prompt generators, post-processors, and verification logic.
"""

from .numerical_solver import NumericalSolver
from .data_interpretation_solver import DataInterpretationSolver
from .figure_series_solver import FigureSeriesSolver
from .figure_matrix_solver import FigureMatrixSolver
from .visual_reasoning_solver import VisualReasoningSolver
from .logical_reasoning_solver import LogicalReasoningSolver
from .verbal_reasoning_solver import VerbalReasoningSolver
from .technical_mcq_solver import TechnicalMcqSolver
from .answer_validator import AnswerValidator

__all__ = [
    "NumericalSolver",
    "DataInterpretationSolver",
    "FigureSeriesSolver",
    "FigureMatrixSolver",
    "VisualReasoningSolver",
    "LogicalReasoningSolver",
    "VerbalReasoningSolver",
    "TechnicalMcqSolver",
    "AnswerValidator",
]
