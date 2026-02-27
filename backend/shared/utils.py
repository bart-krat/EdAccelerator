"""
Shared Utilities

Common helper functions used across the backend.
"""

import json
import logging
from typing import Any, Optional

logger = logging.getLogger("shared.utils")


def safe_json_parse(content: str, default: Optional[dict] = None) -> dict:
    """
    Safely parse JSON content from LLM responses.

    Args:
        content: JSON string to parse
        default: Default value if parsing fails (defaults to empty dict)

    Returns:
        Parsed dict or default value on failure
    """
    if default is None:
        default = {}

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e} - Content: {content[:200]}...")
        return default
    except Exception as e:
        logger.error(f"Unexpected error parsing JSON: {e}")
        return default
