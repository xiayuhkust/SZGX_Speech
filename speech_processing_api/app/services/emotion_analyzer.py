from typing import Dict, Any
import json
from openai import OpenAI

class EmotionAnalyzer:
    def __init__(self):
        self.system_prompt = """
你是一个情感分析专家。你需要分析给定文本的情感强度，并给出0-5的评分。评分标准如下：
0: 完全中性或无情感
1: 轻微情感波动
2: 明显但温和的情感
3: 强烈的情感
4: 非常强烈的情感
5: 极其强烈的情感

同时，你需要给出主要情感类型（如：喜悦、愤怒、悲伤、惊讶等）。

请以JSON格式返回，包含以下字段：
- score: 情感强度评分（0-5）
- emotion: 主要情感类型
- explanation: 简短解释（不超过50字）
"""

    async def analyze(self, text: str) -> Dict[str, Any]:
        try:
            client = OpenAI()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
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
                "result": json.loads(content),
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                    "model": "gpt-3.5-turbo",
                    "cost_estimate": round((usage.prompt_tokens * 0.001 + usage.completion_tokens * 0.002) / 1000, 6)
                }
            }
        except Exception as e:
            raise Exception(f"Error analyzing emotion: {str(e)}")
