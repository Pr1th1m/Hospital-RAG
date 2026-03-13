"""
Shared Groq client with automatic API key fallback.

When the primary key hits rate limits or token limits, the client
automatically retries the same call with the backup key.
If all keys are exhausted, waits briefly and retries once more.
"""

import os
import time
import logging
from dotenv import load_dotenv
from groq import Groq, RateLimitError, APIStatusError

load_dotenv()

logger = logging.getLogger(__name__)

# Load both keys
_PRIMARY_KEY = os.getenv("GROQ_API_KEY")
_BACKUP_KEY = os.getenv("GROQ_API_KEY_BACKUP")

# Build the key rotation list
_api_keys = [k for k in [_PRIMARY_KEY, _BACKUP_KEY] if k]
_current_key_index = 0


def _create_client(api_key: str) -> Groq:
    return Groq(api_key=api_key)


# Initialise with primary key
client = _create_client(_api_keys[0]) if _api_keys else None


def _is_rate_limit_error(error: Exception) -> bool:
    """Check if an error is a rate-limit / quota-exceeded error."""
    # Check by exception type first (most reliable)
    if isinstance(error, RateLimitError):
        return True

    # Check for 429 status in API errors
    if isinstance(error, APIStatusError) and error.status_code == 429:
        return True

    # Fallback: check error message strings
    error_str = str(error).lower()
    rate_limit_indicators = [
        "rate_limit",
        "rate limit",
        "quota",
        "tokens per minute",
        "requests per minute",
        "too many requests",
        "429",
        "resource_exhausted",
        "limit reached",
        "exceeded",
    ]
    return any(indicator in error_str for indicator in rate_limit_indicators)


def call_with_fallback(api_call, max_retries=2, retry_delay=10):
    """
    Execute a Groq API call with automatic key fallback and retry.

    Flow:
    1. Try with current key
    2. On rate limit → switch to next key and retry
    3. If ALL keys fail → wait `retry_delay` seconds and retry the full cycle once more

    Args:
        api_call: A callable that receives a Groq client and makes the API call.
        max_retries: Number of full retry cycles after all keys are exhausted.
        retry_delay: Seconds to wait before retrying after all keys fail.

    Returns:
        The result of the API call.

    Raises:
        The last exception if all retries are exhausted.
    """
    global client, _current_key_index

    last_error = None

    for retry in range(max_retries):
        for key_attempt in range(len(_api_keys)):
            try:
                result = api_call(client)
                return result
            except Exception as e:
                last_error = e
                if _is_rate_limit_error(e) and len(_api_keys) > 1:
                    # Rotate to the next key
                    old_index = _current_key_index
                    _current_key_index = (_current_key_index + 1) % len(_api_keys)
                    next_key = _api_keys[_current_key_index]
                    logger.warning(
                        f"Rate limit hit on key #{old_index + 1}. "
                        f"Switching to key #{_current_key_index + 1}..."
                    )
                    client = _create_client(next_key)
                elif _is_rate_limit_error(e) and len(_api_keys) == 1:
                    # Only one key, break to retry with delay
                    break
                else:
                    # Not a rate-limit error — re-raise immediately
                    raise

        # All keys exhausted for this cycle
        if retry < max_retries - 1:
            logger.warning(
                f"All API keys exhausted. Waiting {retry_delay}s before retry "
                f"({retry + 1}/{max_retries - 1})..."
            )
            time.sleep(retry_delay)

    # All retries exhausted
    logger.error("All Groq API keys and retries exhausted.")
    raise last_error
