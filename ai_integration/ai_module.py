import importlib.util
import json
import logging
import os
import re
import sys
from typing import Optional

logger = logging.getLogger(__name__)  # Reuse the global logger


def main_int_ai() -> bool:
    """
    Initialize AI integration.
    - In production, this would set up OpenAI/LLM clients, keys, rate-limiters, etc.
    - For now, we log initialization and verify OPENAI_API_KEY presence.
    """
    logger.info("Initializing AI Module...")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set; AI features disabled.")
        return False
    logger.info("AI configuration found (client initialization placeholder).")

    # TODO: Initialize OpenAI/LangChain client here, e.g.:
    # from openai import OpenAI
    # client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    # store client object in a module-global or pass it to downstream functions.
    # Keep initialization idempotent and raise exceptions on critical failure.

    return True


def main_test_ai(option: int) -> bool:
    """
    Lightweight test for AI integration used by CLI -ai.
    Returns True if basic check passes (API key present), False otherwise.
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
        # check if openai package is installed (import test)
        spec = importlib.util.find_spec("openai")
        if spec is None:
            logger.warning("main_test_ai option 3: 'openai' package not found.")
            return False
        logger.info("main_test_ai option 3: 'openai' package is installed.")
        return True

    else:
        logger.error("main_test_ai: unknown option %s", option)
        return False
