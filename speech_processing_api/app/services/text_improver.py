from typing import Dict, Any
from openai import OpenAI

class TextImprover:
    def __init__(self):
        self.model = "gpt-3.5-turbo"
        self.system_prompt = """你是中文写作专家。请优化下面文本，使其更通顺流畅并消除语病，但需保持全部原意。
如果发现经文引用或圣经章节，请严格按照《和合本》的格式和内容处理，不要修改这些部分。
请以JSON格式返回，包含以下字段：
- improved_text: 优化后的文本
- changes_made: 修改说明（如果没有修改则返回"无需修改"）
"""

    async def improve_text(self, text: str) -> Dict[str, Any]:
        try:
            client = OpenAI()
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": text}
                ],
                response_format={"type": "json_object"}
            )
            
            if not response.choices or not response.choices[0].message.content:
                raise Exception("Empty response from OpenAI")
                
            content = response.choices[0].message.content
            usage = response.usage
            if not usage:
                raise Exception("No usage information available")
                
            return {
                "result": content,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                    "model": self.model,
                    "cost_estimate": round((usage.prompt_tokens * 0.001 + usage.completion_tokens * 0.002) / 1000, 6)
                }
            }
        except Exception as e:
            raise Exception(f"Error improving text: {str(e)}")
