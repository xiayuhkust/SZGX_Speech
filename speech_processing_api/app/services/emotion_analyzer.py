from typing import Dict, Any
from openai import OpenAI
from app.core.config import settings

class EmotionAnalyzer:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
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
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": text}
                ],
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error analyzing emotion: {str(e)}")
