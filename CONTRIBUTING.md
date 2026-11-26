# Contributing to NovaGhost

Thank you for your interest in contributing to NovaGhost. This project is built to provide an open, accurate, and privacy-respecting visual aptitude practice tool for students, educators, and developers.

Contributions of all types are welcome, including new aptitude domain solvers, computer vision enhancements, bug fixes, UI improvements, and documentation.

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Windows 10/11 environment (recommended for display affinity and gesture hooks)
- Git

### Local Development Setup

1. Fork the repository on GitHub and clone your fork locally:
   ```bash
   git clone https://github.com/<your-username>/NovaGhost.git
   cd NovaGhost
   ```

2. Create and activate a clean Python virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. Install all project dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

4. Launch the application to verify your setup:
   ```powershell
   python main.py
   ```

---

## Development Workflow

1. Create a dedicated feature branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Write clean, modular Python code following PEP 8 conventions.
3. Keep the architecture local-only:
   - Do not introduce cloud account requirements, login barriers, or telemetry.
   - User settings and API keys must remain strictly on the local machine (`~/.novaghost/settings.json`).
4. Add comprehensive unit tests in the `tests/` directory for any new logic, solvers, or helpers.

---

## Testing Guidelines

Before opening a pull request, run the entire test suite and ensure all tests pass:

```powershell
python -m unittest discover tests -v
```

All 57 existing automated tests (and any newly added tests) must pass with zero errors and zero failures.

---

## Adding a New Domain Solver

To add a new specialized aptitude solver:

1. Create your solver class inside `engine/solvers/` (e.g., `engine/solvers/my_domain_solver.py`).
2. Implement your solver methods returning the standardized `StructuredAnswer` schema defined in `engine/schemas.py`.
3. Integrate your solver in `engine/processor.py` or `engine/solvers/__init__.py`.
4. Add unit test coverage in `tests/test_solvers.py`.
5. Verify test pass rates with `python -m unittest discover tests -v`.

---

## Submitting a Pull Request

1. Push your feature branch to your GitHub fork:
   ```bash
   git push origin feature/your-feature-name
   ```
2. Open a Pull Request against the `main` branch of `ByteNinjaSmit/NovaGhost`.
3. Fill out the Pull Request template completely, describing:
   - What problem your change addresses
   - How you verified and tested the solution
   - Any relevant screenshots or logs
4. Address review comments promptly. Once approved and checks pass, your pull request will be merged.

---

## Reporting Issues

If you find a bug or have a suggestion:
- Check existing issues to see if it has already been reported.
- Open a new issue using our Bug Report or Feature Request templates.
- Include your Python version, OS version, logs from `~/.novaghost/novaghost.log`, and steps to reproduce.
