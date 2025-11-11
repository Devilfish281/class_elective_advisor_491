# tests/test_parse_course_data.py  # Added Code
import pytest  # Added Code

from ai_integration.ai_module import parse_course_data  # Added Code


def _mk_lines(*items):  # Added Code
    """Build a starred_lines list quickly."""  # Added Code
    return list(items)  # Added Code


def test_parse_course_data_happy_path_two_courses():  # Added Code
    starred_lines = _mk_lines(  # Added Code
        "**Number:** 1",  # Added Code
        "**Course Code:** CPSC 483",  # Added Code
        "**Course Name:** Introduction to Machine Learning",  # Added Code
        "**Rating:** 100",  # Added Code
        "**Explanation:** Machine Learning is a cornerstone of AI development",  # Added Code
        "It covers supervised/unsupervised learning and real datasets.",  # Added Code
        "**Prerequisites:** CPSC 335, MATH 338",  # Added Code
        "**Number:** 2",  # Added Code
        "**Course Code:** CPSC 375",  # Added Code
        "**Course Name:** Introduction to Data Science and Big Data",  # Added Code
        "**Rating:** 95",  # Added Code
        "**Explanation:** Strong foundation in data pipelines and modeling.",  # Added Code
        "Includes IoT/time-series examples and big-data platforms.",  # Added Code
        "**Prerequisites:** CPSC 131, MATH 338",  # Added Code
    )  # Added Code

    courses = parse_course_data(starred_lines)  # Added Code
    assert isinstance(courses, list) and len(courses) == 2  # Added Code

    c1, c2 = courses  # Added Code
    assert c1["Number"] == 1  # Added Code
    assert c1["Course Code"] == "CPSC 483"  # Added Code
    assert c1["Course Name"] == "Introduction to Machine Learning"  # Added Code
    assert c1["Rating"] == 100  # Added Code
    # Explanation lines must be joined with spaces and trimmed.  # Added Code
    assert (
        "cornerstone of AI development It covers supervised/unsupervised"
        in c1["Explanation"]
    )  # Added Code
    assert c1["Prerequisites"] == "CPSC 335, MATH 338"  # Added Code

    assert c2["Number"] == 2  # Added Code
    assert c2["Course Code"] == "CPSC 375"  # Added Code
    assert (
        c2["Course Name"] == "Introduction to Data Science and Big Data"
    )  # Added Code
    assert c2["Rating"] == 95  # Added Code
    assert (
        "Strong foundation in data pipelines and modeling." in c2["Explanation"]
    )  # Added Code
    assert "big-data platforms." in c2["Explanation"]  # Added Code
    assert c2["Prerequisites"] == "CPSC 131, MATH 338"  # Added Code


def test_parse_course_data_out_of_order_keys_and_string_rating():  # Added Code
    # Keys may appear in a different order; ensure the parser remains robust.  # Added Code
    starred_lines = _mk_lines(  # Added Code
        "**Number:** 7",  # Added Code
        "**Rating:** N/A",  # Added Code
        "**Course Name:** Cloud Computing and Security",  # Added Code
        "**Course Code:** CPSC 454",  # Added Code
        "**Explanation:** Discusses distributed systems and cloud risks.",  # Added Code
        "Touches virtualization and deployment models.",  # Added Code
        "**Prerequisites:** CPSC 351, CPSC 353",  # Added Code
    )  # Added Code
    courses = parse_course_data(starred_lines)  # Added Code
    assert len(courses) == 1  # Added Code
    c = courses[0]  # Added Code
    assert c["Number"] == 7  # Added Code
    assert c["Course Code"] == "CPSC 454"  # Added Code
    assert c["Course Name"] == "Cloud Computing and Security"  # Added Code
    # When Rating isn't an int, implementation stores the raw string.  # Added Code
    assert c["Rating"] == "N/A"  # Added Code
    assert "distributed systems and cloud risks." in c["Explanation"]  # Added Code
    assert "virtualization and deployment models." in c["Explanation"]  # Added Code
    assert c["Prerequisites"] == "CPSC 351, CPSC 353"  # Added Code


def test_parse_course_data_explanation_runs_until_next_key_or_eof():  # Added Code
    # Explanation lines continue until the parser hits another **Key:** or EOF.  # Added Code
    starred_lines = _mk_lines(  # Added Code
        "**Number:** 3",  # Added Code
        "**Course Code:** CPSC 455",  # Added Code
        "**Course Name:** Web Security",  # Added Code
        "**Explanation:** Covers XSS and CSRF in depth.",  # Added Code
        "Also covers SQLi and auth patterns.",  # Added Code
        "Hands-on security testing practice.",  # Added Code
        # No more keys for this course; must still flush the course at EOF.  # Added Code
    )  # Added Code
    courses = parse_course_data(starred_lines)  # Added Code
    assert len(courses) == 1  # Added Code
    c = courses[0]  # Added Code
    assert c["Number"] == 3  # Added Code
    assert c["Course Code"] == "CPSC 455"  # Added Code
    assert c["Course Name"] == "Web Security"  # Added Code
    assert "XSS and CSRF in depth." in c["Explanation"]  # Added Code
    assert "auth patterns." in c["Explanation"]  # Added Code
    assert "security testing practice." in c["Explanation"]  # Added Code


def test_parse_course_data_multiple_courses_back_to_back_number_boundaries():  # Added Code
    # Ensure a new **Number:** boundary properly appends the previous course.  # Added Code
    starred_lines = _mk_lines(  # Added Code
        "**Number:** 9",  # Added Code
        "**Course Code:** CPSC 474",  # Added Code
        "**Course Name:** Parallel and Distributed Computing",  # Added Code
        "**Explanation:** Focus on multi-core and GPU.",  # Added Code
        "**Prerequisites:** CPSC 351",  # Added Code
        "**Number:** 10",  # Added Code
        "**Course Code:** CPSC 479",  # Added Code
        "**Course Name:** Introduction to High Performance Computing",  # Added Code
        "**Rating:** 88",  # Added Code
        "**Explanation:** Parallel algorithms on large datasets.",  # Added Code
        "**Prerequisites:** CPSC 351",  # Added Code
    )  # Added Code
    courses = parse_course_data(starred_lines)  # Added Code
    assert [c["Number"] for c in courses] == [9, 10]  # Added Code
    assert courses[0]["Course Code"] == "CPSC 474"  # Added Code
    assert courses[1]["Course Code"] == "CPSC 479"  # Added Code


def test_parse_course_data_gracefully_handles_unknown_keys():  # Added Code
    # Unknown keys should be stored verbatim on the course dict.  # Added Code
    starred_lines = _mk_lines(  # Added Code
        "**Number:** 1",  # Added Code
        "**Course Code:** CPSC 431",  # Added Code
        "**Course Name:** Database and Applications",  # Added Code
        "**Rating:** 92",  # Added Code
        "**Instructor:** Dr. Smith",  # Added Code
        "**Explanation:** Real-world DB design and app dev.",  # Added Code
    )  # Added Code
    courses = parse_course_data(starred_lines)  # Added Code
    assert len(courses) == 1  # Added Code
    c = courses[0]  # Added Code
    assert c["Instructor"] == "Dr. Smith"  # Added Code
