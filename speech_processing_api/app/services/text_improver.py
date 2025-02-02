from typing import Dict, Any, Optional
from openai import OpenAI

class TextImprover:
    """Improves Chinese text while maintaining emotional context and biblical references."""
    def __init__(self):
        self.model = "gpt-3.5-turbo"
        self.system_prompt = """你是中文写作专家。请优化下面文本，使其更通顺流畅并消除语病，但需要：
1. 保持全部原意
2. 保持情感强度（情感分数：{emotion_score}，情感类型：{emotion_type}）
3. 如果发现经文引用或圣经章节，请严格按照《和合本》的格式和内容处理，不要修改这些部分。

请以JSON格式返回，包含以下字段：
- improved_text: 优化后的文本
- changes_made: 修改说明（如果没有修改则返回"无需修改"）
"""

    async def improve_text(self, text: str, emotion_score: Optional[float] = None, emotion_type: Optional[str] = None) -> Dict[str, Any]:
        """Improve Chinese text while maintaining emotional context.
        
        Args:
            text: Input text to improve
            emotion_score: Optional emotion intensity score
            emotion_type: Optional emotion type/category
            
        Returns:
            Dict containing improved text and usage statistics
        """
        try:
            client = OpenAI()
            prompt = self.system_prompt
            if emotion_score is not None and emotion_type is not None:
                prompt = prompt.format(emotion_score=emotion_score, emotion_type=emotion_type)
            else:
                prompt = prompt.format(emotion_score="保持原有", emotion_type="保持原有")
                
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
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
