# utilities/load_env.py

import logging
import os
import re
from pathlib import Path
from typing import Optional

from dotenv import find_dotenv, load_dotenv

logger = logging.getLogger(__name__)


def _validate_api_key(key: str) -> bool:
    """
    Conservative validation for the OpenAI API key:
    - must be at least 20 characters (adjust to your provider's expected length)
    - contains at least one alphanumeric character
    """
    if not key:
        return False
    if len(key) < 20:
        return False
    if not re.search(r"[A-Za-z0-9]", key):
        return False
    return True


def load_environment() -> None:
    """
    Load environment variables from .env (if present) and validate required vars.
    Raises ValueError on missing/invalid critical variables.
    """
    logger.info("Loading environment variables.")

    # Locate a .env file in the project (if present) and load it without overriding existing env vars.
    env_path = find_dotenv()
    if env_path:
        load_dotenv(env_path, override=False)
        logger.debug("Loaded .env from %s", env_path)
    else:
        logger.debug(
            ".env file not found; continuing with existing environment variables"
        )

    apikey = os.getenv("OPENAI_API_KEY")
    if not _validate_api_key(apikey or ""):
        logger.error("OPENAI_API_KEY is missing or invalid")
        raise ValueError("OPENAI_API_KEY environment variable missing or invalid")

    # Do NOT print or log the actual API key - never divulge secrets.
    logger.info("API Key loaded successfully.")
