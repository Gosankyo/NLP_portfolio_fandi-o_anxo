<!-- Auto-generated guidance for AI coding agents. Edit with care. -->
# Repo-specific Copilot Instructions

This repository currently contains a small Jupyter notebook with exercise code. The goal of this document is to give AI coding agents the minimal, concrete context needed to be productive here.

Summary
- This repo is a single-notebook exercise project. Key file: `S01_exercises.ipynb`.
- No package manifests (`requirements.txt`, `pyproject.toml`, or `package.json`) or test suite were found.

How to be productive
- Open `S01_exercises.ipynb` in the VS Code Jupyter editor and run cells to inspect behavior before changing code.
- Prefer adding new `.py` modules for reusable code instead of editing large notebook cells in-place. Example: extract functions from a solution cell into `solutions/<topic>.py`.
- If you add dependencies, create `requirements.txt` at the repo root and include `pip install -r requirements.txt` in your recommended run steps.

Patterns and conventions observed (repo-specific)
- Notebook-first workflow: changes should preserve notebook cell outputs unless the user asks to clear them.
- Small, self-contained exercises: implement minimal, well-named functions (avoid monolithic cell edits).

Developer workflows (what worked / what to suggest)
- Manual run: open notebook in VS Code and run selected cells (no CI detected).
- Export to script for testability: recommend `python -m nbconvert --to script S01_exercises.ipynb` to create an editable `.py` version when preparing unit tests or larger refactors.

Integration points & external dependencies
- None detected. If adding external APIs or data, document credentials and endpoints in a new `README.md` and avoid adding secrets to the repo.

What to avoid
- Do not commit large notebook outputs or sensitive files. If asked to modify the notebook, prefer small, incremental changes and explain them in the commit message.

Examples from this codebase
- Inspect `S01_exercises.ipynb` to find exercise cells and implement helpers in `solutions/` (create the folder when needed).
- When extracting code, ensure the notebook imports the new module (e.g., `from solutions.example import my_func`) and re-run the dependent cells.

When uncertain, ask the user
- Ask before: (a) changing notebook cell structure or outputs, (b) adding new dependencies, (c) creating or removing files at repository root.

Checklist for PRs from AI agents
- Include a short description explaining why you modified the notebook instead of adding a module.
- If adding dependencies, include `requirements.txt` and a brief run command.
- Prefer small commits that clearly state intent (e.g., "extract sum helper from notebook cell to solutions/sum_helper.py").

If anything here is unclear or you want additional guidance (tests, CI, packaging), tell me what you'd like prioritized and I'll iterate.
