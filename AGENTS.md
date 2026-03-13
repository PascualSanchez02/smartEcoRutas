# AGENTS.md

## Goal
Build a correct, competitive, and reproducible Python solution for the SmartEcoRutas challenge.

## Repository facts
- The main student file to implement is `student/algoritmoSmartEcoRutas.py`.
- The required entry point is:
  `solve(problem, time_limit_s: float, seed: int | None = None) -> list[list[str]]`
- Do not read raw dataset files directly in the solver.
- Use the provided `ProblemInstance` API and the framework utilities already present in the repository.

## Working rules
- Read the repository before making changes.
- Keep changes minimal and localized.
- Respect the existing API, folder structure, and expected output format.
- Do not add unnecessary dependencies.
- Prefer a single-file solution in `student/` unless modularization clearly helps.
- Prioritize correctness first, then solution quality, then code clarity.
- Explain which files were changed and why.

## What to inspect first
- `README.md`
- `run.py`
- `framework/problem_instance.py`
- `framework/evaluator.py`
- `framework/geo_export.py`
- `student/`

## Solver requirements
- Implement the solution in `student/algoritmoSmartEcoRutas.py`.
- The solver must return `list[list[str]]`.
- Each route must start at `BASE` and end with `... DUMP, BASE`.
- Every container must be visited exactly once.
- Never exceed `max_containers_before_dump` between dump visits.
- Never exceed `route_max_work_s` for a route.
- Use the provided travel/service-time helpers instead of reimplementing the evaluator logic.

## Objective
- Primary objective: minimize the total number of routes across the 4 official instances.
- Secondary objective: minimize total travel time as tie-breaker.

## Time-budget rules
- The official limit is 15 minutes per instance, with a small tolerance.
- Use time-aware search and early stopping.
- Always return the best valid solution found so far before timeout.

## Recommended workflow
1. Analyze the repository and execution flow before editing.
2. Confirm the exact contract of `solve(...)`.
3. Build a valid baseline solver first.
4. Validate it with the repository workflow.
5. Improve iteratively with measurable changes.
6. Prefer small, testable improvements over large rewrites.

## Validation commands
- Environment setup:
  - `conda create -n smartecorutas python=3.11 -y`
  - `conda activate smartecorutas`
  - `pip install -r requirements.txt`
- Standard execution:
  - `python run.py`
- Fast reproducible execution:
  - `python run.py --seed 0 --no-geo`

## Definition of done
A change is only done if:
- the repository still runs,
- the solver output format is valid,
- constraints are respected,
- no unrelated files are broken,
- and the change is explained clearly.

## Review guidelines
- Do not invent assumptions if the repository already defines the behavior.
- Flag ambiguities explicitly.
- Keep diffs scoped.
- Prefer robust heuristics over clever but fragile code.
- When optimizing, explain expected impact before large edits.
