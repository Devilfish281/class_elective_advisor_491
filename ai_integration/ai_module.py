"""ai_integration.ai_module
================================

Utilities and test hooks for the AI integration layer of the Smart Elective
Advisor. This module exposes a small public API for generating course
recommendations and includes CLI-driven self-tests used by ``main.py``.

**Contents**

* Environment helpers (e.g., :func:`parse_bool_env`)
* JSON/CSV I/O helpers for local “fake” responses
* Public recommendation entry point (:func:`get_recommendations_ai`)
* Test dispatcher (:func:`main_test_ai`)

.. rubric:: Sphinx integration

The docstrings in this module use reStructuredText **info field lists** (e.g.,
``:param:``, ``:returns:``, ``:raises:``), which Sphinx's Python domain renders
nicely with ``sphinx.ext.autodoc``. An ``autosummary`` is provided below for
clean API index pages.

.. autosummary::
   :toctree: _autosummary
   :nosignatures:

   parse_bool_env
   _find_courses_json
   _parse_degree_electives_csv
   main_int_ai
   main_test_ai
   get_recommendations_ai
   fake_chatgpt_response
   real_chatgpt_response
"""

import importlib.util
import json
import logging
import os
import re
import sys
from typing import TYPE_CHECKING, Any, Optional

logger = logging.getLogger(__name__)

import csv
import io
import textwrap

# ----------------------------- NEW IMPORTS/HELPERS -----------------------------
from pathlib import Path
from typing import Any, Dict, List

from langchain.prompts import ChatPromptTemplate

if TYPE_CHECKING:
    from langchain_openai import ChatOpenAI


# Explicit module-level globals so other functions can guard against uninitialized state
model: Optional["ChatOpenAI"] = None  # Added Code
prompt_template: Optional[Any] = None  # Added Code


def parse_bool_env(name: str, default: bool = False) -> bool:
    """Parse a boolean environment variable.

    :param name: Environment variable name to read.
    :type name: str
    :param default: Value to use if the variable is unset.
    :type default: bool
    :returns: ``True`` if the variable is set to a recognized truthy token
              (``"1"``, ``"true"``, ``"yes"``, ``"y"``, ``"on"``, ``"t"``),
              otherwise ``False``.
    :rtype: bool
    """
    val = os.getenv(name, str(default))
    return str(val).strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
        "t",
    }


def _find_courses_json() -> Path:
    """Locate the bundled ``courses.json`` data file.

    Searches several locations relative to this file and the current working
    directory, returning the first existing path.

    :returns: Resolved path where ``courses.json`` is found (or the primary
              candidate if none exist, for error context).
    :rtype: :class:`pathlib.Path`
    """

    candidates = [
        Path.cwd() / "courses.json",
        Path(__file__).resolve().parents[1] / "courses.json",
        Path(__file__).resolve().parents[2] / "courses.json",
    ]
    for p in candidates:
        if p.exists():
            return p
    # Fall back to first candidate (for error message context)
    return candidates[0]


def _combine_prereqs(p1: str, p2: str, p3: str) -> str:
    """Join up to three prerequisite tokens into a single readable string.
    Examples:
      - ["CPSC 351", "CPSC 352", "CPSC 253"] -> "CPSC 351, CPSC 352 or CPSC 253"
      - ["CPSC 351 or CPSC 353", "", ""] -> "CPSC 351 or CPSC 353"
      - ["", "", ""] -> "None"
    """
    parts = [s.strip() for s in (p1 or "", p2 or "", p3 or "") if s and s.strip()]
    if not parts:
        return "None"
    if len(parts) == 1:
        return parts[0]
    # If there are 2+, prefer ", ".join(head) + " or tail" for readability.
    head, tail = parts[:-1], parts[-1]
    return f"{', '.join(head)} or {tail}"


def _normalize_elective_row(old: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce any legacy/CSV-shaped row to the canonical shape expected downstream.
    Canonical keys: prerequisites, course_code, units, name, description.
    """
    if "prerequisites" in old and "course_code" in old:
        return old

    # CSV/legacy keys -> canonical keys
    prereqs = _combine_prereqs(
        old.get("Prereq1", ""),
        old.get("Prereq2", ""),
        old.get("Prereq3", ""),
    )
    units = old.get("Units", None)
    try:
        units = int(units) if units not in ("", None) else None
    except Exception:
        units = None

    return {
        "prerequisites": prereqs,
        "course_code": str(old.get("Course Code", "")).strip(),
        "units": units,
        "name": str(old.get("Course Name", "")).strip(),
        "description": str(old.get("Description", "")).strip(),
    }


def _parse_degree_electives_csv(csv_text: str) -> List[Dict[str, Any]]:
    """Parse elective rows from CSV text into structured records.

    The incoming CSV may have up to seven columns: Prereq1, Prereq2, Prereq3,
    Course Code, Units, Course Name, Description. This parser normalizes them
    into the canonical schema used by the AI layer:
      - prerequisites: single readable string (e.g., "CPSC 351, CPSC 352 or CPSC 253")
      - course_code: string
      - units: int | None
      - name: string
      - description: string
    """

    fieldnames = [
        "Prereq1",
        "Prereq2",
        "Prereq3",
        "Course Code",
        "Units",
        "Course Name",
        "Description",
    ]
    reader = csv.reader(io.StringIO(csv_text))
    rows: List[Dict[str, Any]] = []
    for raw in reader:
        if not raw or all(not str(x).strip() for x in raw):
            continue
        row = list(raw) + [""] * (len(fieldnames) - len(raw))
        row = row[: len(fieldnames)]

        tmp: Dict[str, Any] = {}
        for key, val in zip(fieldnames, row):
            s = str(val).strip()
            tmp[key] = s

        # Convert to canonical shape
        rows.append(_normalize_elective_row(tmp))

    logger.debug("Parsed %d elective rows (normalized)", len(rows))
    for r in rows:
        logger.debug(r)
    return rows


# -------------------------------------------------------------------------------


def main_int_ai() -> bool:
    """Initialize the AI integration layer.

    In production this would set up model clients, keys, and rate-limiters.
    Currently it validates presence of ``OPENAI_API_KEY`` and logs status.

    :returns: ``True`` if an API key is present; ``False`` otherwise.
    :rtype: bool
    """

    global model, prompt_template

    logger.info("Initializing AI Module...")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set; AI features disabled.")
        return False
    logger.info("AI configuration found (client initialization placeholder).")

    try:
        from langchain_openai import (
            ChatOpenAI,
        )  # Local import to allow test mode without langchain

        # Create a ChatOpenAI model
        model = ChatOpenAI(model="gpt-4o")
    except Exception as e:
        logger.error(f"Error creating ChatOpenAI model: {e}")
        return False

    # Prompt with System and Human Messages (Using Tuples)
    logger.info("\n----- Setup Prompt with System and Human Messages (Tuple) -----\n")
    # Prompt with System and Human Messages (Using Tuples)
    # < career path> p_career_path
    # <START Electives> p_electives
    # < degree> p_degree
    messages = [
        (
            "system",
            """Role: College counselor
    Response length: detailed
    Explanation for each elective: Provide detailed explanations for each recommended elective course, ensuring that each explanation falls within a word count range of 100 to 200 words. These explanations should comprehensively address why the elective is beneficial.
    Response Style and Voice: detailed and academic style of the response should help the student understand the importance and relevance of each elective to their career of {p_career_path}.
    career path default: AI
    Prerequisite default: have not taken
    Response output:
    Line 1: Number 1,2,3,4,etc.
    Line 2: Course Code
    Line 3: Course Name
    Line 4: Rating
    Line 5: Explanation
    Line 6: Prerequisites, if all are blank, write "None

    Example of Response output:
    **Number:** 1
    **Course Code:** CPSC 483
    **Course Name:** Introduction to Machine Learning
    **Rating:** 100
    **Explanation:** Machine Learning is a cornerstone of AI development...add the reat of the explanation here
    **Prerequisites:** CPSC 335, MATH 338 


    I am a at CSU Fullerton college student what electives should I take to be best prepared for a degree in {p_degree} and specialize in {p_career_path} related fields. I need to take 5 electives, give me 10 to choose from.
    Rate each elective from 1 to 100, with 100 being the best.
    Sort the above by Rating, best which is 100 to worst which is 1.
    Explain why the elective is good for an  {p_career_path} education in great detail: Minium 100 words to max 200 words. ensure that responses adhere to the specified word count range of 100 to 200 words for each explanation
    If the user did not enter any Electives, then all Prerequisite Need to take. Do not assume that foundational courses are completed
    For each Prerequisite show “Need to take:” or “Completed:” base on the user input of class completed. Example: Completed CPSC 131, MATH 270B, etc.
    These suggestions not only consider the student's academic history and preferences but also the potential career paths they might be interested in, such as web development, AI engineering, machine learning, or game development.
    The system aims to streamline the decision-making process, ensuring students make informed choices that will benefit their future career trajectories.
    """,
        ),
        (
            "human",
            "Here are the electives I has to choose from in the format of: 'Prerequisite1,Prerequisite2,Prerequisite3,Course,Units,Name,Description' {p_electives} .",
        ),
    ]

    prompt_template = ChatPromptTemplate.from_messages(messages)

    logger.info("AI Integration Initialized done.")

    return True


def main_test_ai(option: int) -> bool:
    """Dispatch AI module self-tests for the CLI ``-ai`` flag.

    :param option: Test variant selector.
    :type option: int
    :returns: ``True`` on success, ``False`` on test failure.
    :rtype: bool

    **Variants**
      * ``1`` - call :func:`main_int_ai`.
      * ``2`` - verify and mask ``OPENAI_API_KEY``.
      * ``3`` - assert that the ``openai`` package is importable.
      * ``4`` - run a CSV→JSON recommendation smoke test and validate that
        items numbered 1..10 are present in the JSON payload.
    """
    logger.info("Running AI module test...")

    api_key = os.getenv("OPENAI_API_KEY")

    if option == 1:
        ret_value = main_int_ai()
        return ret_value

    elif option == 2:
        if not api_key:
            logger.warning("main_test_ai option 2: OPENAI_API_KEY not set.")
            return False
        masked = api_key[:8] + ("*" * max(0, len(api_key) - 8))
        logger.info("main_test_ai option 2: API key masked prefix: %s", masked)
        return True

    elif option == 3:
        spec = importlib.util.find_spec("openai")
        if spec is None:
            logger.warning("main_test_ai option 3: 'openai' package not found.")
            return False
        logger.info("main_test_ai option 3: 'openai' package is installed.")
        return True
    ################################################################S
    elif option == 4:
        try:
            # Provided CSV lines (kept verbatim; parser handles quotes/commas)
            # Build CSV safely using triple *single* quotes so embedded "..." in CSV don't clash.
            csv_text = """ 
            CPSC 335,MATH 338,,CPSC 483,3,Introduction to Machine Learning,"Design, implement and analyze machine learning algorithms, including supervised learning and unsupervised learning algorithms. Methods to address uncertainty. Projects with real-world data." 
            CPSC 131,MATH 338,,CPSC 375,3,Introduction to Data Science and Big Data ,"Techniques for data preparation, exploratory analysis, statistical modeling, machine learning and visualization. Methods for analyzing different types of data, such as natural language and time-series, from emerging applications, including Internet-of-Things. Big data platforms. Projects with real-world data." 
            CPSC 131,,,CPSC 485,3,Computational Bioinformatics,"Algorithmic approaches to biological problems. Specific topics include motif finding, genome rearrangement, DNA sequence comparison, sequence alignment, DNA sequencing, repeat finding and gene expression analysis." 
            MATH 270B,CPSC 131,,CPSC 452,3,Cryptography,"Introduction to cryptography and steganography. Encryption, cryptographic hashing, certificates, and signatures. Classical, symmetric-key, and public-key ciphers. Block modes of operation. Cryptanalysis including exhaustive search, man-in-the-middle, and birthday attacks. Programing projects involving implementation of cryptographic systems." 
            CPSC 351, CPSC 353,,CPSC 454,3,Cloud Computing and Security,"Cloud computing and cloud security, distributed computing, computer clusters, grid computing, virtual machines and virtualization, cloud computing platforms and deployment models, cloud programming and software environments, vulnerabilities and risks of cloud computing, cloud infrastructure protection, data privacy and protection." 
            CPSC 351 or CPSC 353,,,CPSC 455,3,Web Security,"Concepts of web application security. Web security mechanisms, including authentication, access control and protecting sensitive data. Common vulnerabilities, including code and SQL attacks, cross-site scripting and cross-site request forgery. Implement hands-on web application security mechanisms and security testing." 
            CPSC 351,,,CPSC 474,3,Parallel and Distributed Computing,"Concepts of distributed computing; distributed memory and shared memory architectures; parallel programming techniques; inter-process communication and synchronization; programming for parallel architectures such as multi-core and GPU platforms; project involving distributed application development." 
            CPSC 351,,,CPSC 479,3,Introduction to High Performance Computing,"Introduction to the concepts of high-performance computing and the paradigms of parallel programming in a high level programming language, design and implementation of parallel algorithms on distributed memory, machine learning techniques on large data sets, implementation of parallel algorithms." 
            CPSC 121 or MATH 320,MATH 270B or MATH 280,,CPSC 439,3,Theory of Computation,"Introduction to the theory of computation. Automata theory; finite state machines, context free grammars, and Turing machines; hierarchy of formal language classes. Computability theory and undecidable problems. Time complexity; P and NP-complete problems. Applications to software design and security." 
            MATH 250A ,,,MATH 335,3,Mathematical Probability,"Probability theory; discrete, continuous and multivariate probability distributions, independence, conditional probability distribution, expectation, moment generating functions, functions of random variables and the central limit theorem." 
            CPSC 131, MATH 150B, MATH 270B,CPSC 484,3,Principles of Computer Graphics,"Examine and analyze computer graphics, software structures, display processor organization, graphical input/output devices, display files. Algorithmic techniques for clipping, windowing, character generation and viewpoint transformation." 
            ,,,CPSC 499,3,Independent Study,"Special topic in computer science, selected in consultation with and completed under the supervision of instructor. May be repeated for a maximum of 9 units of Undergraduate credit and 6 units of Graduate credit. Requires approval by the Computer Science chair." 
            CPSC 351,CPSC 353 or CPSC 452,,CPSC 459,3,Blockchain Technologies,"Digital assets as a medium of exchange to secure financial transactions; decentralized and distributed ledgers that record verifiable transactions; smart contracts and Ethereum; Bitcoin mechanics and mining; the cryptocurrency ecosystem; blockchain mechanics and applications." 
            MATH 250B,MATH 320,CPSC 120 or CPSC 121,MATH 370,3,Mathematical Model Building,"Introduction to mathematical models in science and engineering: dimensional analysis, discrete and continuous dynamical systems, flow and diffusion models." 
            MATH 250B,MATH 320,CPSC 120 or CPSC 121,MATH 340,,Numerical Analysis,"Approximate numerical solutions of systems of linear and nonlinear equations, interpolation theory, numerical differentiation and integration, numerical solution of ordinary differential equations. Computer coding of numerical methods." 
            CPSC 351,,,CPSC 456,3,Network Security Fundamentals,"Learn about vulnerabilities of network protocols, attacks targeting confidentiality, integrity and availability of data transmitted across networks, and methods for diagnosing and closing security gaps through hands-on exercises." 
            CPSC 351,,,CPSC 458,3,Malware Analysis,"Introduction to principles and practices of malware analysis. Topics include static and dynamic code analysis, data decoding, analysis tools, debugging, shellcode analysis, reverse engineering of stealthy malware and written presentation of analysis results." 
            CPSC 332,,,CPSC 431,3,Database and Applications,"Database design and application development techniques for a real world system. System analysis, requirement specifications, conceptual modeling, logic design, physical design and web interface development. Develop projects using contemporary database management system and web-based application development platform." 
            CPSC 332,,,CPSC 449,3,Web Back-End Engineering,"Design and architecture of large-scale web applications. Techniques for scalability, session management and load balancing. Dependency injection, application tiers, message queues, web services and REST architecture. Caching and eventual consistency. Data models, partitioning and replication in relational and non-relational databases." 
            CPSC 240,,,CPSC 440,3,Computer System Architecture,"Computer performance, price/performance, instruction set design and examples. Processor design, pipelining, memory hierarchy design and input/output subsystems." 
            CPSC 131 ,,,CPSC 349 ,3, Web Front-End Engineering ,"Concepts and architecture of interactive web applications, including markup, stylesheets and behavior. Functional and object-oriented aspects of JavaScript. Model-view design patterns, templates and frameworks. Client-side technologies for asynchronous events, real-time interaction and access to back-end web services." 
            CPSC 131,,,CPSC 411,3,Mobile Device Application Programming,"Introduction to developing applications for mobile devices, including but not limited to runtime environments, development tools and debugging tools used in creating applications for mobile devices. Use emulators in lab. Students must provide their own mobile devices." 
            CPSC 362,,,CPSC 464,3,Software Architecture,"Basic principles and practices of software design and architecture. High-level design, software architecture, documenting software architecture, software and architecture evaluation, software product lines and some considerations beyond software architecture." 
            CPSC 362,,,CPSC 462,3,Software Design,"Concepts of software modeling, software process and some tools. Object-oriented analysis and design and Unified process. Some computer-aided software engineering (CASE) tools will be recommended to use for doing homework assignments." 
            CPSC 362,,,CPSC 463,3,Software Testing,"Software testing techniques, reporting problems effectively and planning testing projects. Students apply what they learned throughout the course to a sample application that is either commercially available or under development." 
            CPSC 362,,,CPSC 466,3,Software Process,"Practical guidance for improving the software development process. How to establish, maintain and improve software processes. Exposure to agile processes, ISO 12207 and CMMI." 
            CPSC 386,CPSC 484,,CPSC 486,3,Game Programming,"Survey of data structures and algorithms used for real-time rendering and computer game programming. Build upon existing mathematics and programming knowledge to create interactive graphics programs." 
            CPSC 486,,,CPSC 489,3,Game Development Project,"Individually or in teams, students design, plan and build a computer game." 
            CPSC 121,,,CPSC 386,3,Introduction to Game Design and Production,"Current and future technologies and market trends in game design and production. Game technologies, basic building tools for games and the process of game design, development and production." 
            ,,,CPSC 301,2,Programming Lab Practicum ,"Intensive programming covering concepts learned in lower-division courses. Procedural and object oriented design, documentation, arrays, classes, file input/output, recursion, pointers, dynamic variables, data and file structures." 
            """
            csv_text = textwrap.dedent(csv_text).strip()  # clean up indentation
            degree_electives = _parse_degree_electives_csv(csv_text)
            job_id = 1
            job_name = "Web Developer"
            degree_name = "Bachelor of Computer Science"

            from ai_integration.ai_module import (
                get_recommendations_ai,
            )  # self-import safe

            main_int_ai()  # ensure initialized
            result = get_recommendations_ai(
                job_id=job_id,
                job_name=job_name,
                degree_name=degree_name,
                degree_electives=degree_electives,
            )
            # ---- NEW VALIDATION: ensure Numbers 1..10 are present in the JSON ----
            try:
                payload = json.loads(result)
            except json.JSONDecodeError as e:
                logger.error("main_test_ai option 4: invalid JSON result: %s", e)
                return False

            if not isinstance(payload, list):
                logger.error("main_test_ai option 4: result JSON is not a list")
                return False

            found_numbers = set()
            for item in payload:
                if isinstance(item, dict) and "Number" in item:
                    n = item.get("Number")
                    if isinstance(n, int):
                        found_numbers.add(n)
                    else:
                        try:
                            found_numbers.add(int(str(n)))
                        except Exception:
                            pass

            required = set(range(1, 11))  # {1..10}
            missing = sorted(required - found_numbers)
            if missing:
                logger.error("main_test_ai option 4: missing Numbers %s", missing)
                return False

            logger.info(
                "main_test_ai option 4: found all Numbers 1..10; recommendations JSON length=%s",
                len(result) if isinstance(result, str) else 0,
            )
            return True

        except Exception:
            logger.exception("main_test_ai option 4 failed")
            return False

    else:
        logger.error("main_test_ai: unknown option %s", option)
        return False


##################################################################S
# ----------------------------- NEW PUBLIC API ----------------------------------
def get_recommendations_ai(
    job_id: int,
    job_name: str,
    degree_name: str,
    degree_electives: List[Dict[str, Any]],
) -> str:
    """Generate course recommendations for a degree given a target job.

    :param job_id: Numeric job identifier used by the application.
    :type job_id: int
    :param job_name: Human-readable job title (e.g., ``"Web Developer"``).
    :type job_name: str
    :param degree_name: Degree/program name.
    :type degree_name: str
    :param degree_electives: Parsed elective rows (see
        :func:`_parse_degree_electives_csv`).
    :type degree_electives: List[Dict[str, Any]]
    :returns: JSON string representing recommended courses (list of objects).
    :rtype: str
    :raises Exception: On file I/O or model invocation errors in real mode.
    """
    logger.debug(f"Job ID: {job_id}, Job Name: {job_name}, Degree Name: {degree_name}")

    ai_enabled = parse_bool_env("AI_ENABLED", default=False)
    if not ai_enabled:
        return fake_chatgpt_response(job_id, job_name, degree_name, degree_electives)

    result = real_chatgpt_response(job_id, job_name, degree_name, degree_electives)
    # Ensure we always return a string for callers while real path is WIP.
    return result if isinstance(result, str) else ""


# -------------------------------------------------------------------------------


def fake_chatgpt_response(
    job_id: int,
    job_name: str,
    degree_name: str,
    degree_electives: List[Dict[str, Any]],
) -> str:
    """Return canned recommendations from ``courses.json``.

    :param job_id: Numeric job identifier (unused; logged for context).
    :type job_id: int
    :param job_name: Human-readable job title (unused; logged for context).
    :type job_name: str
    :param degree_name: Degree/program name (unused; logged for context).
    :type degree_name: str
    :param degree_electives: Parsed elective rows (unused in fake mode).
    :type degree_electives: List[Dict[str, Any]]
    :returns: Pretty-printed JSON string loaded from the local file.
    :rtype: str
    :raises FileNotFoundError: If ``courses.json`` cannot be located.
    :raises json.JSONDecodeError: If the JSON file is malformed.
    :raises Exception: For any other unexpected I/O condition.
    """
    logger.warning("[FAKE CHATGPT] Returning canned response...")
    logger.info("AI_ENABLED=False: Loading recommendations from courses.json")

    path = _find_courses_json()
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info("Recommendations loaded successfully from courses.json")
        return json.dumps(data, indent=4)
    except FileNotFoundError as e:
        logger.error("courses.json not found at expected locations: %s", path)
        raise
    except json.JSONDecodeError as e:
        logger.error("Failed to parse courses.json: %s", e)
        raise
    except Exception as e:
        logger.exception("Unexpected error loading courses.json: %s", e)
        raise


def format_elective_string(prerequisites, course_code, units, name, description):
    """
    Formats a single elective line for the prompt builder.

    Parameters:
        prerequisites (str): Single, human-readable prerequisites string (e.g., "CPSC 351, CPSC 352 or CPSC 253").
        course_code (str): Course code, e.g., "CPSC 483".
        units (int|None): Number of units.
        name (str): Course name.
        description (str): Course description.

    Returns:
        str: "Prereq1,Prereq2,Prereq3,Course,Units,Name,Description" compatible string (placeholders auto-filled).
    """
    # Ensure the prerequisites string yields exactly 3 comma-separated slots for the downstream prompt schema.
    if not prerequisites or str(prerequisites).strip().lower() == "none":
        p1, p2, p3 = "None", "", ""
    else:
        tokens = [t.strip() for t in str(prerequisites).split(",") if t.strip()]
        while len(tokens) < 3:
            tokens.append("")
        p1, p2, p3 = tokens[:3]

    units_text = "" if units in (None, "") else str(units)
    return f"{p1},{p2},{p3},{course_code},{units_text},{name},{description}"


def extract_starred_lines(input_text):
    """
    Extracts lines that contain an asterisk (*) from the input text.
    For lines starting with "**Prerequisites:**", removes all text between "**Prerequisites:**" and the first colon ":".

    Args:
        input_text (str): The multiline string to process.

    Returns:
        list: A list of lines containing at least one asterisk, with modified prerequisites lines.
    """
    # Split the input text into individual lines
    lines = input_text.split("\n")

    starred_lines = []
    for line in lines:
        stripped_line = line.strip()
        if "*" in stripped_line:
            # Check if the line starts with "**Prerequisites:**"
            if stripped_line.startswith("**Prerequisites:**"):
                # Use regex to remove text between "**Prerequisites:**" and the first colon ":"
                # This will transform "**Prerequisites:** Need to take: CPSC 335, MATH 338" to "**Prerequisites:** CPSC 335, MATH 338"
                modified_line = re.sub(
                    r"(\*\*Prerequisites:\*\*)[^:]*:\s*", r"\1 ", stripped_line
                )
                starred_lines.append(modified_line)
            else:
                starred_lines.append(stripped_line)

    return starred_lines


def parse_course_data(starred_lines):
    """
    Parses the array of starred lines and converts them into a list of dictionaries.

    Args:
        starred_lines (list): A list of lines containing course details.

    Returns:
        list: A list of dictionaries, each representing a course.
    """
    courses = []
    course = {}
    explanation_key = "**Explanation:**"
    prerequisites_key = "**Prerequisites:**"
    current_key = None
    explanation_lines = []

    for line in starred_lines:
        # Check if the line starts with a key pattern
        key_match = re.match(r"\*\*(.+?):\*\*\s*(.*)", line)
        if key_match:
            key, value = key_match.groups()
            key = key.strip()
            value = value.strip()

            if key == "Number":
                # If there's an existing course being parsed, add it to the list
                if course:
                    # If there's any accumulated explanation lines, join them
                    if explanation_lines:
                        course["Explanation"] = " ".join(explanation_lines).strip()
                        explanation_lines = []
                    courses.append(course)
                    course = {}
                course["Number"] = int(value)
                current_key = "Number"

            elif key == "Course Code":
                course["Course Code"] = value
                current_key = "Course Code"

            elif key == "Course Name":
                course["Course Name"] = value
                current_key = "Course Name"

            elif key == "Rating":
                try:
                    course["Rating"] = int(value)
                except ValueError:
                    course["Rating"] = value  # Keep as string if not an integer
                current_key = "Rating"

            elif key == "Explanation":
                explanation_lines = [value]
                current_key = "Explanation"

            elif key == "Prerequisites":
                course["Prerequisites"] = value
                current_key = "Prerequisites"

            else:
                # Handle any unexpected keys
                course[key] = value
                current_key = key

        else:
            # Handle multiline fields like Explanation
            if current_key == "Explanation":
                explanation_lines.append(line)
                course["Explanation"] = " ".join(explanation_lines).strip()

    # Add the last course after the loop ends
    if course:
        if explanation_lines:
            course["Explanation"] = " ".join(explanation_lines).strip()
        courses.append(course)

    return courses


def real_chatgpt_response(
    job_id: int,
    job_name: str,
    degree_name: str,
    degree_electives: List[Dict[str, Any]],
):
    """Produce recommendations using a real LLM backend (placeholder).

    This stub logs intent and will be implemented to call a provider such as
    OpenAI via LangChain/LangGraph.

    :param job_id: Numeric job identifier.
    :type job_id: int
    :param job_name: Human-readable job title.
    :type job_name: str
    :param degree_name: Degree/program name.
    :type degree_name: str
    :param degree_electives: Parsed elective rows to inform prompting.
    :type degree_electives: List[Dict[str, Any]]
    :returns: Currently ``None`` (to be updated to a JSON string).
    :rtype: Optional[str]
    """
    logger.info("AI_ENABLED=True: Invoking AI model for recommendations.")
    logger.debug(
        "Job ID: %s, Job Name: %s, Degree Name: %s", job_id, job_name, degree_name
    )

    # No explicit return -> returns None for now.

    try:
        # Prepare the prompt with the provided parameters
        # Convert degree_electives to a formatted string
        # format of: 'Prerequisite1,Prerequisite2,Prerequisite3,Course,Units,Name,Description'
        # Format electives_str as 'Prerequisite1,Prerequisite2,Prerequisite3,Course,Units,Name,Description'
        electives_str = "\n".join(
            [
                format_elective_string(
                    e["prerequisites"],
                    e["course_code"],
                    e["units"],
                    e["name"],
                    e["description"],
                )
                for e in degree_electives
            ]
        )
        logger.debug(f"Formatted electives_str:\n{electives_str}")

        prompt = prompt_template.invoke(
            {
                "p_career_path": job_name,
                "p_degree": degree_name,
                "p_electives": electives_str,
            }
        )

        #         """
        # CPSC 335,MATH 338,,CPSC 483,3,Introduction to Machine Learning,"Design, implement and analyze machine learning algorithms, including supervised learning and unsupervised learning algorithms. Methods to address uncertainty. Projects with real-world data."
        # CPSC 131,MATH 338,,CPSC 375,3,Introduction to Data Science and Big Data ,"Techniques for data preparation, exploratory analysis, statistical modeling, machine learning and visualization. Methods for analyzing different types of data, such as natural language and time-series, from emerging applications, including Internet-of-Things. Big data platforms. Projects with real-world data."
        # CPSC 131,,,CPSC 485,3,Computational Bioinformatics,"Algorithmic approaches to biological problems. Specific topics include motif finding, genome rearrangement, DNA sequence comparison, sequence alignment, DNA sequencing, repeat finding and gene expression analysis."
        # MATH 270B,CPSC 131,,CPSC 452,3,Cryptography,"Introduction to cryptography and steganography. Encryption, cryptographic hashing, certificates, and signatures. Classical, symmetric-key, and public-key ciphers. Block modes of operation. Cryptanalysis including exhaustive search, man-in-the-middle, and birthday attacks. Programing projects involving implementation of cryptographic systems."
        # CPSC 351, CPSC 353,,CPSC 454,3,Cloud Computing and Security,"Cloud computing and cloud security, distributed computing, computer clusters, grid computing, virtual machines and virtualization, cloud computing platforms and deployment models, cloud programming and software environments, vulnerabilities and risks of cloud computing, cloud infrastructure protection, data privacy and protection."
        # CPSC 351 or CPSC 353,,,CPSC 455,3,Web Security,"Concepts of web application security. Web security mechanisms, including authentication, access control and protecting sensitive data. Common vulnerabilities, including code and SQL attacks, cross-site scripting and cross-site request forgery. Implement hands-on web application security mechanisms and security testing."
        # CPSC 351,,,CPSC 474,3,Parallel and Distributed Computing,"Concepts of distributed computing; distributed memory and shared memory architectures; parallel programming techniques; inter-process communication and synchronization; programming for parallel architectures such as multi-core and GPU platforms; project involving distributed application development."
        # CPSC 351,,,CPSC 479,3,Introduction to High Performance Computing,"Introduction to the concepts of high-performance computing and the paradigms of parallel programming in a high level programming language, design and implementation of parallel algorithms on distributed memory, machine learning techniques on large data sets, implementation of parallel algorithms."
        # CPSC 121 or MATH 320,MATH 270B or MATH 280,,CPSC 439,3,Theory of Computation,"Introduction to the theory of computation. Automata theory; finite state machines, context free grammars, and Turing machines; hierarchy of formal language classes. Computability theory and undecidable problems. Time complexity; P and NP-complete problems. Applications to software design and security."
        # MATH 250A ,,,MATH 335,3,Mathematical Probability,"Probability theory; discrete, continuous and multivariate probability distributions, independence, conditional probability distribution, expectation, moment generating functions, functions of random variables and the central limit theorem."
        # CPSC 131, MATH 150B, MATH 270B,CPSC 484,3,Principles of Computer Graphics,"Examine and analyze computer graphics, software structures, display processor organization, graphical input/output devices, display files. Algorithmic techniques for clipping, windowing, character generation and viewpoint transformation."
        # ,,,CPSC 499,3,Independent Study,"Special topic in computer science, selected in consultation with and completed under the supervision of instructor. May be repeated for a maximum of 9 units of Undergraduate credit and 6 units of Graduate credit. Requires approval by the Computer Science chair."
        # CPSC 351,CPSC 353 or CPSC 452,,CPSC 459,3,Blockchain Technologies,"Digital assets as a medium of exchange to secure financial transactions; decentralized and distributed ledgers that record verifiable transactions; smart contracts and Ethereum; Bitcoin mechanics and mining; the cryptocurrency ecosystem; blockchain mechanics and applications."
        # MATH 250B,MATH 320,CPSC 120 or CPSC 121,MATH 370,3,Mathematical Model Building,"Introduction to mathematical models in science and engineering: dimensional analysis, discrete and continuous dynamical systems, flow and diffusion models."
        # MATH 250B,MATH 320,CPSC 120 or CPSC 121,MATH 340,,Numerical Analysis,"Approximate numerical solutions of systems of linear and nonlinear equations, interpolation theory, numerical differentiation and integration, numerical solution of ordinary differential equations. Computer coding of numerical methods."
        # CPSC 351,,,CPSC 456,3,Network Security Fundamentals,"Learn about vulnerabilities of network protocols, attacks targeting confidentiality, integrity and availability of data transmitted across networks, and methods for diagnosing and closing security gaps through hands-on exercises."
        # CPSC 351,,,CPSC 458,3,Malware Analysis,"Introduction to principles and practices of malware analysis. Topics include static and dynamic code analysis, data decoding, analysis tools, debugging, shellcode analysis, reverse engineering of stealthy malware and written presentation of analysis results."
        # CPSC 332,,,CPSC 431,3,Database and Applications,"Database design and application development techniques for a real world system. System analysis, requirement specifications, conceptual modeling, logic design, physical design and web interface development. Develop projects using contemporary database management system and web-based application development platform."
        # CPSC 332,,,CPSC 449,3,Web Back-End Engineering,"Design and architecture of large-scale web applications. Techniques for scalability, session management and load balancing. Dependency injection, application tiers, message queues, web services and REST architecture. Caching and eventual consistency. Data models, partitioning and replication in relational and non-relational databases."
        # CPSC 240,,,CPSC 440,3,Computer System Architecture,"Computer performance, price/performance, instruction set design and examples. Processor design, pipelining, memory hierarchy design and input/output subsystems."
        # CPSC 131 ,,,CPSC 349 ,3, Web Front-End Engineering ,"Concepts and architecture of interactive web applications, including markup, stylesheets and behavior. Functional and object-oriented aspects of JavaScript. Model-view design patterns, templates and frameworks. Client-side technologies for asynchronous events, real-time interaction and access to back-end web services."
        # CPSC 131,,,CPSC 411,3,Mobile Device Application Programming,"Introduction to developing applications for mobile devices, including but not limited to runtime environments, development tools and debugging tools used in creating applications for mobile devices. Use emulators in lab. Students must provide their own mobile devices."
        # CPSC 362,,,CPSC 464,3,Software Architecture,"Basic principles and practices of software design and architecture. High-level design, software architecture, documenting software architecture, software and architecture evaluation, software product lines and some considerations beyond software architecture."
        # CPSC 362,,,CPSC 462,3,Software Design,"Concepts of software modeling, software process and some tools. Object-oriented analysis and design and Unified process. Some computer-aided software engineering (CASE) tools will be recommended to use for doing homework assignments."
        # CPSC 362,,,CPSC 463,3,Software Testing,"Software testing techniques, reporting problems effectively and planning testing projects. Students apply what they learned throughout the course to a sample application that is either commercially available or under development."
        # CPSC 362,,,CPSC 466,3,Software Process,"Practical guidance for improving the software development process. How to establish, maintain and improve software processes. Exposure to agile processes, ISO 12207 and CMMI."
        # CPSC 386,CPSC 484,,CPSC 486,3,Game Programming,"Survey of data structures and algorithms used for real-time rendering and computer game programming. Build upon existing mathematics and programming knowledge to create interactive graphics programs."
        # CPSC 486,,,CPSC 489,3,Game Development Project,"Individually or in teams, students design, plan and build a computer game."
        # CPSC 121,,,CPSC 386,3,Introduction to Game Design and Production,"Current and future technologies and market trends in game design and production. Game technologies, basic building tools for games and the process of game design, development and production."
        # ,,,CPSC 301,2,Programming Lab Practicum ,"Intensive programming covering concepts learned in lower-division courses. Procedural and object oriented design, documentation, arrays, classes, file input/output, recursion, pointers, dynamic variables, data and file structures."

        # """,
        #     }
        # )

        logger.info("---Working---")
        result = model.invoke(prompt)
        logger.info("---DONE---")

        logger.debug("---Raw AI Response---")
        logger.debug(result.content)
        logger.debug("---End Raw AI Response---")

        # Extract lines containing '*'
        starred_lines = extract_starred_lines(result.content)

        # Print the resulting array
        logger.debug("---Lines containing '*': Extracted---")
        for idx, line in enumerate(starred_lines, start=1):
            logger.debug(line)

        # Parse the raw data
        courses = parse_course_data(starred_lines)

        logger.debug("---Parsed Courses---")
        logger.debug(courses)

        # Convert the list of courses to JSON
        json_data = json.dumps(courses, indent=4)

        # Print the JSON data
        print("Print the JSON data:")
        print(json_data)

        # After converting to JSON
        with open("courses.json", "w", encoding="utf-8") as json_file:
            json_file.write(json_data)
            logger.info("AI recommendations written to courses.json")

        return json_data

    except Exception as e:
        logger.error(
            f"Error during Prompt with System and Human Messages (Tuple):OpenAI agent execution: {e}"
        )
        raise RuntimeError("real_chatgpt_response failed") from e
