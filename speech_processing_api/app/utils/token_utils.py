from typing import Union, List, Any, Callable
import asyncio
import os
import tiktoken
from tenacity import retry, stop_after_attempt, wait_exponential

def estimate_tokens(text: Union[str, List[str]], model: str = "gpt-3.5-turbo") -> int:
    encoding = tiktoken.encoding_for_model(model)
    if isinstance(text, str):
        return len(encoding.encode(text))
    return sum(len(encoding.encode(t)) for t in text)

# Load configuration from environment variables with defaults
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "16000"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "2000"))
SYSTEM_PROMPT_TOKENS = int(os.getenv("SYSTEM_PROMPT_TOKENS", "385"))

# Retry configuration for long-running processes
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5"))
MIN_RETRY_WAIT = int(os.getenv("MIN_RETRY_WAIT", "60"))
MAX_RETRY_WAIT = int(os.getenv("MAX_RETRY_WAIT", "300"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "1800"))  # 30 minutes per request

@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=MIN_RETRY_WAIT, max=MAX_RETRY_WAIT),
    retry_error_callback=lambda retry_state: {"error": str(retry_state.outcome.exception())}
)
async def retry_with_timeout(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    try:
        return await asyncio.wait_for(func(*args, **kwargs), timeout=REQUEST_TIMEOUT)
    except asyncio.TimeoutError:
        raise Exception("Request timed out")
