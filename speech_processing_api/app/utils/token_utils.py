from typing import Union, List
import tiktoken

def estimate_tokens(text: Union[str, List[str]], model: str = "gpt-3.5-turbo") -> int:
    encoding = tiktoken.encoding_for_model(model)
    if isinstance(text, str):
        return len(encoding.encode(text))
    return sum(len(encoding.encode(t)) for t in text)

# Constants for token limits
MAX_TOKENS = 16000  # Leave buffer for system prompts
CHUNK_SIZE = 4000   # Roughly 1000-1500 Chinese characters
SYSTEM_PROMPT_TOKENS = 385  # Estimated tokens for system prompt
