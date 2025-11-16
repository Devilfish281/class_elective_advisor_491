Checklist:

- Gather standards references (ISO/IEC/IEEE 29119-3; note IEEE 829 status).
- Align plan with your repo layout, tests, tools (pytest, Poetry, Tkinter, SQLite, LangChain).
- Define scope, approach, environments, entry/exit, risks, schedule, deliverables.
- Map current tests to components and add gaps/backlog.
- Describe CI (GitHub Actions), coverage, and optional Codecov upload.

````markdown
# docs/test_plan.md

# Smart Elective Advisor — Test Plan (CPSC 491-08)

**Repository:** `https://github.com/Devilfish281/class_elective_advisor`  
**Project Directory (local):** `C:\Users\Me\Documents\Python\CPSC491\Projects\class_elective_advisor_491`  
**Primary Technologies:** Python 3.12, Poetry, Tkinter (GUI), SQLite (DB), LangChain/LangGraph, OpenAI (gpt-4o)  
**CI:** GitHub Actions (`.github/workflows/pytest.yml`)  
**Test Runner:** `pytest` with coverage and HTML report (`pytest.ini`)

---

## 1. Purpose & Scope

This plan defines the strategy, activities, environments, responsibilities, and exit criteria for testing the Smart Elective Advisor. It covers unit, component, integration (DB + GUI harnesses), and CI automation. It is tailored to ISO/IEC/IEEE 29119-3 test documentation guidance (templates/examples) and acknowledges the historical IEEE 829 outline that has been superseded by 29119-3. :contentReference[oaicite:0]{index=0}

### In Scope

- **Unit tests** for `ai_integration`, `utilities`, `database`, `ui`, and `main` modules.
- **Component/integration tests**:
  - SQLite schema & CRUD smoke tests.
  - Tkinter headless GUI harness tests (non-visual).
  - AI layer “fake” path using local JSON/CSV; “real” path initialization only.
- **CI** execution on PR/push; coverage generation and HTML artifact.
- **Release readiness checks**: basic smoke on version/about dialog.

### Out of Scope (current iteration)

- End-to-end human-in-the-loop usability testing.
- Load/perf testing of AI requests.
- Full contract testing against live OpenAI API responses (beyond init).

---

## 2. References

- ISO/IEC/IEEE 29119-3: Test documentation (templates, examples). :contentReference[oaicite:1]{index=1}
- IEEE 829 (superseded by ISO/IEC/IEEE 29119-3; retained for outline inspiration). :contentReference[oaicite:2]{index=2}
- Pytest parameterization and fixtures guidance. :contentReference[oaicite:3]{index=3}
- GitHub Actions—building and testing Python. :contentReference[oaicite:4]{index=4}
- Codecov upload options (optional enhancement). :contentReference[oaicite:5]{index=5}

---

## 3. Test Items

Modules and artifacts under test:

- `main.py` (CLI/test dispatcher)
- `ai_integration/ai_module.py` (parsing, “fake” recommendations, env flags, init)
- `database/db_setup.py`, `database/DB_table_setup.py`, CRUD utilities (`db_add.py`, `delete_Info.py`, `edit_info.py`)
- `ui/app_version.py`, `ui/gui.py`, `ui/zulu_timestamp.py`
- `utilities/load_env.py`, `utilities/logger_setup.py`

Existing tests (baseline):

- `tests/test_ai_module.py`, `tests/test_ai_fake_errors.py`
- `tests/test_db_setup.py`
- `tests/test_find_courses_json.py`
- `tests/test_gui.py`
- `tests/test_load_env.py`, `tests/test_parse_bool_env.py`

---

## 4. Test Approach

### 4.1 Unit & Component Strategy

- **Utilities & Parsing**: deterministic unit tests (pure Python).
- **AI Layer**:
  - **Fake mode** (`AI_ENABLED=False`): file discovery, JSON decode behavior, CSV→records parser, numbered payload validation.
  - **Real mode** (`AI_ENABLED=True`): init-only smoke (model creation guarded), no external network assertions; use env fixtures to avoid secrets in CI.
- **Database**:
  - In-memory schema creation; temp-file smoke insert/select tests.
  - No persistence across tests; each test isolated.
- **GUI (Tkinter)**:
  - Headless stubs for `Tk`, `Label`, `after()` (immediate call) to assert lifecycle without real windows.
- **Parametrization/fixtures**: reduce duplication and expand coverage per pytest best practices. :contentReference[oaicite:6]{index=6}

### 4.2 CI Workflow

- Trigger on `push` and `pull_request`.
- Steps: checkout → set up Python → install Poetry deps → run `pytest` with coverage → upload HTML coverage as artifact. (See GitHub’s Python workflow patterns). :contentReference[oaicite:7]{index=7}
- **Optional**: Upload coverage to Codecov via `codecov/codecov-action@v5` or CLI. :contentReference[oaicite:8]{index=8}

---

## 5. Test Environment

- **OS**: Windows 11 (dev), GitHub Actions Ubuntu runner (CI).
- **Python**: 3.12 (see workflow).
- **Dependencies**: Managed by Poetry; `pytest`, `pytest-cov`, `tkinter` (std), `sqlite3` (std), `langchain`, `langchain-openai`, `bcrypt`, `python-dotenv`.
- **Data**: `database/courses.csv`, `courses.json`, `version.json`.
- **Headless GUI**: No display required; monkeypatched Tk objects.

---

## 6. Entry & Exit Criteria

### Entry

- Dependencies resolve via Poetry.
- Secrets not required for fake-path tests; when needed, tests inject a safe, fake `OPENAI_API_KEY` via fixtures.

### Exit

- ✅ All tests green in CI on `main` and PR branches.
- ✅ Line coverage threshold met (see §10 Metrics).
- ✅ HTML coverage report generated and uploaded as artifact (and optionally to Codecov).

---

## 7. Risks & Mitigations

| Risk                        | Impact                | Mitigation                                                                     |
| --------------------------- | --------------------- | ------------------------------------------------------------------------------ |
| External AI API instability | Flaky tests           | Keep network off in tests; test “real mode” init only with safe env injection. |
| GUI timing/race conditions  | Intermittent failures | Use stubbed `after()` immediate callbacks; avoid sleeps.                       |
| SQLite file locking on CI   | CI failures           | Prefer `:memory:` or temp files; close connections deterministically.          |
| Secrets leakage             | Compliance risk       | Never log secrets; use masked envs/fixtures; CI secrets only where required.   |

---

## 8. Test Case Inventory (Baseline → Component)

| Area           | Test File                         | Focus                                        |
| -------------- | --------------------------------- | -------------------------------------------- |
| AI env/init    | `tests/test_ai_module.py`         | `main_int_ai()` True/False with/without key  |
| AI packaging   | `tests/test_ai_module.py`         | options 1..4 behavior                        |
| AI file errors | `tests/test_ai_fake_errors.py`    | missing/malformed `courses.json`             |
| AI utilities   | `tests/test_find_courses_json.py` | path resolution precedence                   |
| DB schema      | `tests/test_db_setup.py`          | `:memory:` create; temp-file insert/select   |
| GUI harness    | `tests/test_gui.py`               | create/destroy/root loop stub and auto-close |
| Env loader     | `tests/test_load_env.py`          | `.env` missing raises; valid key passes      |
| Booleans       | `tests/test_parse_bool_env.py`    | truthy tokens and defaults                   |

**Backlog (to add):**

- `ui/app_version.py` (formatting edge cases, dialog construction).
- `ui/gui.py` recommendation pipeline happy path using fake AI JSON.
- DB CRUD functions (`db_add.py`, `delete_Info.py`, `edit_info.py`) with isolated temp DB paths.

---

## 9. Test Design Techniques

- **Equivalence classes & boundaries** for parsers (empty lines, invalid JSON/CSV).
- **Behavioral stubbing** for GUI (`after`, `mainloop`).
- **Parametrized tests** to exercise truthy env tokens, DB paths, and CSV row shapes using `@pytest.mark.parametrize` and fixture parametrization. :contentReference[oaicite:9]{index=9}

---

## 10. Metrics & Reporting

- **Coverage**: statement/branch coverage via `pytest-cov`; HTML report in `htmlcov/` and uploaded as CI artifact.
- **Threshold (initial)**: overall ≥ 80% on `utilities`, `database`, and `ai_integration` packages; GUI excluded from threshold but reported.
- **Trend**: (optional) Codecov dashboards for PR annotations and historical trends. :contentReference[oaicite:10]{index=10}

---

## 11. Tooling & Commands

- **Local run (examples)**

  ### With coverage + HTML (your pytest.ini already configures coverage and htmlcov/):

  ### Open htmlcov/index.html for the coverage report.

  - `poetry run pytest`

  ### Local quick run:

  - `poetry run pytest -q`
  - `poetry run pytest --cov --cov-report=term-missing --cov-report=html`

- **CI**: See `.github/workflows/pytest.yml` (runs on PR/push; installs Poetry deps; executes pytest; preserves HTML coverage).

- **Optional Codecov** (enhancement): add `codecov/codecov-action@v5` step or use the Codecov CLI uploader after tests complete. :contentReference[oaicite:11]{index=11}

---

## 12. Defect Management

- Report issues in GitHub Issues with labels: `bug`, `test-fail`, `area:ui`, `area:ai`, `area:db`.
- Include: failing test name, stack trace, repro steps, environment, commit SHA, and coverage deltas.

---

## 13. Schedule & Milestones

- **M1 (Now)**: Adopt this plan; ensure CI green on `main`.
- **M2**: Add backlog tests (app_version, GUI recommendations, CRUD) and raise coverage to targets.
- **M3**: Decide on Codecov adoption and add status badges.

---

## 14. Roles & Responsibilities

- **Matthew Dobley (Developer/Owner)**: author tests, triage CI, maintain thresholds.
- **Collaborators/Reviewers**: PR review, verify failing tests, approve changes.
- **CI**: automated execution and artifact retention.

---

## 15. Deliverables

- This test plan (`docs/test_plan.md`).
- Test suites under `tests/`.
- CI configuration (`.github/workflows/pytest.yml`).
- Coverage artifacts (HTML) on each CI run, optionally Codecov uploads.

---

## 16. Traceability

| Requirement/Area          | Test(s)                           |
| ------------------------- | --------------------------------- |
| Load environment securely | `tests/test_load_env.py`          |
| Boolean env parsing       | `tests/test_parse_bool_env.py`    |
| AI module init & options  | `tests/test_ai_module.py`         |
| Fake response errors      | `tests/test_ai_fake_errors.py`    |
| Course file resolution    | `tests/test_find_courses_json.py` |
| DB schema/connectivity    | `tests/test_db_setup.py`          |
| GUI lifecycle/headless    | `tests/test_gui.py`               |

---

## Appendix: Acronyms

- CI: Continuous Integration
- DB: Database
- GUI: Graphical User Interface
- JSON: JavaScript Object Notation
- CSV: Comma-Separated Values

```bash
poetry run python main.py
```
````

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your changes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

````
- **AI-Powered Recommendations:** Utilizes advanced AI to suggest courses tailored to individual preferences.
- **User-Friendly Interface:** Built with Tkinter for easy navigation and interaction.
- **Local Data Management:** Employs SQLite for efficient data storage and retrieval.
- **Comprehensive Documentation:** Maintained using Sphinx for easy reference and onboarding.
## Installation
### Prerequisites
- **Python 3.12.7**
- **Poetry:** For dependency management and virtual environment setup.
### Steps
1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/class_elective_advisor_491.git
   cd class_elective_advisor_491
````

2. **Install Dependencies:**
   ```bash
   poetry install
   ```
3. **Activate the Virtual Environment (Poetry 2.x):**
   ```powershell
   & ((poetry env info --path) + "/Scripts/activate.ps1")
   ```
   _Note:_ Poetry 2.x replaced `poetry shell` with the `poetry env activate` flow (which prints an activation command). The one-liner above uses `poetry env info --path` to get the venv path and activates it directly in PowerShell.
4. **Set Up Environment Variables:**
   Rename the `.env.example` file to `.env` and update the variables inside with your own values.
   Create a `.env` file in the root directory and add your OpenAI API key:
   ```env
   OPENAI_API_KEY=your_api_key_here
   ```
5. **Initialize the Database:**
   ```bash
   poetry run python -m db.init
   ```
   The above command will set up the database and launch the GUI.

## Usage

Run the application using:

```bash
    poetry run python main.py
```
