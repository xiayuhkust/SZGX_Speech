from typing import Union, List, Any, Callable
import asyncio
import tiktoken
from tenacity import retry, stop_after_attempt, wait_exponential

def estimate_tokens(text: Union[str, List[str]], model: str = "gpt-3.5-turbo") -> int:
    encoding = tiktoken.encoding_for_model(model)
    if isinstance(text, str):
        return len(encoding.encode(text))
    return sum(len(encoding.encode(t)) for t in text)

# Constants for token limits
MAX_TOKENS = 16000  # Leave buffer for system prompts
CHUNK_SIZE = 2000   # Reduced from 4000 to prevent timeouts
SYSTEM_PROMPT_TOKENS = 385  # Estimated tokens for system prompt

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry_error_callback=lambda retry_state: {"error": str(retry_state.outcome.exception())}
)
async def retry_with_timeout(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Execute function with retry logic and timeout handling."""
    try:
        return await asyncio.wait_for(func(*args, **kwargs), timeout=30)
    except asyncio.TimeoutError:
        raise Exception("Request timed out")
