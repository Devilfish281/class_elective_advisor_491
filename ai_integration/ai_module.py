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
from typing import Optional

logger = logging.getLogger(__name__)

import csv
import io
import textwrap

# ----------------------------- NEW IMPORTS/HELPERS -----------------------------
from pathlib import Path
from typing import Any, Dict, List


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


def _parse_degree_electives_csv(csv_text: str) -> List[Dict[str, Any]]:
    """Parse elective rows from CSV text into structured records.

    The CSV is normalized to seven stable columns and coerces the ``Units``
    field to :class:`int` when possible.

    :param csv_text: Raw CSV text containing elective rows.
    :type csv_text: str
    :returns: List of row dictionaries with keys:
              ``Prereq1``, ``Prereq2``, ``Prereq3``, ``Course Code``, ``Units``,
              ``Course Name``, ``Description``.
    :rtype: List[Dict[str, Any]]
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
        if not raw or all(not str(x).strip() for x in raw):  # skip empty lines
            continue
        # Normalize row to 7 columns
        row = list(raw) + [""] * (len(fieldnames) - len(raw))
        row = row[: len(fieldnames)]
        # Strip whitespace and coerce Units to int when possible
        cleaned: Dict[str, Any] = {}
        for key, val in zip(fieldnames, row):
            s = str(val).strip()
            if key == "Units":
                try:
                    cleaned[key] = int(s) if s else None
                except ValueError:
                    cleaned[key] = None
            else:
                cleaned[key] = s
        rows.append(cleaned)
    return rows


# -------------------------------------------------------------------------------


def main_int_ai() -> bool:
    """Initialize the AI integration layer.

    In production this would set up model clients, keys, and rate-limiters.
    Currently it validates presence of ``OPENAI_API_KEY`` and logs status.

    :returns: ``True`` if an API key is present; ``False`` otherwise.
    :rtype: bool
    """
    logger.info("Initializing AI Module...")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set; AI features disabled.")
        return False
    logger.info("AI configuration found (client initialization placeholder).")

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
