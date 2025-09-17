# AI Integration – Developer Notes

Module: `ai_integration/ai_module.py`
Purpose: Load or generate course-recommendation JSON for the Smart Elective Advisor and provide a minimal test harness.

Quick checklist (for any update)

- [ ] Confirm env vars (`AI_ENABLED`, `OPENAI_API_KEY`) are set as expected.
- [ ] Run `poetry run python main.py -ai 4` to sanity-check JSON output (expects Numbers 1..10).
- [ ] Keep public API stable: `get_recommendations_ai(...) -> str` (JSON string).
- [ ] Log clearly on success/failure; prefer `logger.exception` in `except` blocks.
- [ ] Update Sphinx docstrings when adding/changing functions.
- [ ] If touching real AI calls, follow OpenAI docs and handle errors/rate limits.

1. Overview

This module provides two operating modes:

1. Fake mode (`AI_ENABLED` false): Loads canned recommendations from `courses.json`.
2. Real mode (`AI_ENABLED` true): Placeholder hook for calling an LLM (OpenAI via LangChain/LangGraph), to be implemented in `real_chatgpt_response`.

It also includes a test entrypoint, `main_test_ai(option)`, used by the CLI to verify configuration and data flow.

2. Public API

get_recommendations_ai(job_id, job_name, degree_name, degree_electives) -> str

- Inputs: job and degree metadata plus a pre-parsed list of elective rows (dicts).
- Output: A JSON string with an array of recommendation objects. In fake mode it returns the contents of `courses.json`; in real mode it should return model output (same schema).
- Switch: `AI_ENABLED` (parsed by `parse_bool_env`) gates fake/real paths.

3. Test entrypoints

   `main_test_ai(option: int) -> bool`

Options:

- 1 – Calls `main_int_ai()`; returns `True` if an `OPENAI_API_KEY` exists (basic initialization).
- 2 – Verifies presence/masking of `OPENAI_API_KEY` (logs a masked prefix).
- 3 – Confirms the `openai` package is importable.
- 4 – Full path smoke test:

  - Builds CSV text (dedented) for elective rows.
  - Parses CSV via `_parse_degree_electives_csv`.
  - Calls `get_recommendations_ai(...)`.
  - Validates the returned JSON list contains items with `"Number"` values 1..10. Returns `True` only if all are found.

> Tip: In development you can run only this AI test via `poetry run python main.py -ai 4` or set `TEST_RUN=True` in the environment and run `main.py` (the repo already wires the “tests-only” path in `main.py`).

4. Environment & configuration

   `parse_bool_env(name: str, default: bool = False) -> bool`

Recognizes common truthy values (`1, true, yes, y, on, t`). Anything else is falsey.

Environment variables used:

- `AI_ENABLED` – Gate for real/fake modes (bool).
- `OPENAI_API_KEY` – Required for true AI mode (validated by app setup).
- `TEST_RUN` – Used by `main.py` to drive a one-off AI test path in development.

.env loading: The app uses `python-dotenv` in `utilities/load_env.py` (`load_dotenv` / `find_dotenv`) so you can keep secrets out of VCS while still loading them during development. Defaults do not override existing environment variables and the loader searches upward for a `.env` file, which is consistent with the package’s README guidance.

5. Data sources & parsing

- `courses.json` discovery: `_find_courses_json()` checks common locations using `pathlib.Path` (current working dir and parent folders). The `pathlib` API is the recommended cross-platform way to work with filesystem paths.
- CSV parsing: `_parse_degree_electives_csv(csv_text)` uses `csv.reader` over a `StringIO` buffer, normalizes rows to seven columns, strips whitespace, and coerces `Units` to `int` when possible.
- Fake response: `fake_chatgpt_response(...)` loads and returns `courses.json` (pretty-printed via `json.dumps(..., indent=4)`).

6. Logging & error handling

- The module consistently uses `logger.info/warning/error` and `logger.exception` within `except` blocks. `logger.exception` automatically includes the current exception info, which is the intended usage pattern per the logging docs.
- The top-level CLI paths (`main.py`) print a user-friendly summary and also log full tracebacks, which is generally recommended for CLI tools (operator-friendly messages + dev-grade logs).

7. Sphinx documentation

- Docstrings should be valid reStructuredText. Sphinx autodoc pulls docstrings directly and renders `:param:`, `:type:`, `:returns:`, etc., as “info field lists.”

Practical tips

- Keep summaries one line; add detail paragraphs below.
- Document return types and possible exceptions for public functions.
- When you change function signatures or behavior, update docstrings in the same PR.

8. Real AI integration (to implement)

   `real_chatgpt_response(...)` is intentionally a placeholder. When implementing:

   1. Choose integration style:

   - Direct OpenAI API (Python SDK): Use the official API with your key and selected model (e.g., GPT-4-class models). Follow the _API Reference_ for request/response formats and error handling.
   - LangChain + OpenAI: Wrap prompts and output parsing using LangChain’s OpenAI integrations. LangChain also provides tooling for structured outputs, retrievers, etc.
   - LangGraph: For multi-step tools/agents or graph-shaped control flow, use LangGraph, which is part of the LangChain ecosystem. It helps orchestrate LLM calls, tools, and state machines.

   2. Contract with the UI/DB:

   - Return a JSON string (keep backward compatibility with current callers).
   - Preserve the schema your tests expect (`Number`, `Course Code`, `Course Name`, `Rating`, `Prerequisites`, `Explanation`).
   - If you expand the schema, update both `courses.json` and tests accordingly.

   3. Reliability & guardrails:

   - Validate model output with a JSON schema check; on failure, log and return a meaningful error JSON.
   - Set sensible timeouts, catch network errors, and handle rate limits (retry with backoff).
   - Consider deterministic runs during tests (e.g., fixed seed/temperature).

   4. Prompting sketch (LangChain example):

   - System: role + output schema.
   - Human: degree/electives as structured context (CSV parsed to dicts).
   - Output parser: enforce JSON array with items 1..10 (raise on mismatch; log via `logger.error`).

9. Testing

- CLI: `poetry run python main.py -ai 4`
  Ensures the pipeline from CSV → recommendations JSON works and that `"Number": 1..10` are present (logs missing values, returns `False` otherwise).
- Unit tests: Add small tests for:

  - `parse_bool_env` truth table.
  - `_parse_degree_electives_csv` (empty lines, bad `Units`, trimming).
  - `fake_chatgpt_response` error paths (missing or malformed `courses.json`).

10. Common pitfalls & troubleshooting

- “courses.json not found”: Ensure the file exists at repo root or one of the searched parent paths. The module uses `pathlib` to probe multiple locations; verify working directory when running tools.
- Invalid recommendation JSON: If the model returns malformed JSON, catch it in `main_test_ai(option=4)`—the code already attempts `json.loads(...)` and logs a clear error.
- Logging looks duplicated or missing: Confirm `utilities/logger_setup.py` initialized the root logging config before running tests; check `app.log` for file output.

11. Roadmap for next steps

- Implement `real_chatgpt_response` with:

- Output-schema enforcement and structured parsing.
- Optional reranking of courses via simple scoring rules if the model output lacks ratings.
- Add pydantic models for the recommendation schema to make type/shape explicit.
- Expand Sphinx docs: module overview + function pages with autodoc and autosummary.
- Integrate with the DB/UI layers: persist last recommendation run; display nicely in Tkinter; add a manual “refresh” button.
