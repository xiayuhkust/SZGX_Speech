from typing import Dict, Any
import json
import logging
from openai import OpenAI

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class EmotionAnalyzer:
    def __init__(self):
        self.system_prompt = """你是一个专业的中文情感分析专家。你需要分析给定文本的情感强度，并给出0-5的评分。

你必须以严格的JSON格式返回。emotion字段必须从以下选择之一：喜悦、愤怒、悲伤、惊讶、忧虑、恐惧、期待、满意、焦虑。score必须是0-5的整数。explanation不超过50字。

示例格式：
{
    "emotion": "喜悦",
    "score": 4,
    "explanation": "文本表达了强烈的喜悦之情"
}

注意事项：
1. 不要返回"unknown"或列表外的情感
2. score必须是整数，不能是小数
3. 必须严格按照此JSON格式返回，不要添加注释或其他字段
4. 如果文本包含多种情感，选择最主要或最后出现的情感

评分标准如下：
0: 完全中性或无情感
1: 轻微情感波动
2: 明显但温和的情感
3: 强烈的情感
4: 非常强烈的情感
5: 极其强烈的情感

你需要识别文本中最主要的一种情感。主要情感类型包括：喜悦、愤怒、悲伤、惊讶、忧虑、恐惧、期待、满意、焦虑等。
分析文本时请特别注意以下几点：
1. 转折词处理：
   - 主要转折词：但是、然而、不过、可是、却、反而、相反
   - 递进转折词：不仅如此、而且、甚至、反倒
   - 让步转折词：虽然、尽管、固然、即使

2. 情感标记词：
   - 积极情感：欢喜、开心、快乐、幸福、满意、期待
   - 消极情感：困难、担忧、忧虑、痛苦、悲伤、恐惧
   - 强烈情感：极其、非常、特别、格外、十分

3. 语气词和修辞手法：
   - 感叹语气和反问语气可能暗示更强的情感
   - 比喻和夸张可能加强情感强度
   - 反讽和反语可能表达相反的情感

4. 上下文分析：
   - 分析情感转折的渐变过程
   - 考虑整体语境对局部情感的影响
   - 注意句群之间的情感联系

选择对当前文本段落最具代表性的情感作为主要情感。如果存在明显的情感转折，应该优先选择转折后的情感。

请以JSON格式返回，包含以下字段：
- score: 情感强度评分（0-5）
- emotion: 主要情感类型（单个情感，不要使用组合情感）
- explanation: 简短解释（不超过50字）
"""

    async def _make_deepseek_call(self, text: str) -> Dict[str, Any]:
        import os
        import httpx
        
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not set")
            
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": text}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.3,
                    "max_tokens": 150
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"DeepSeek API error: {response.text}")
                
            result = response.json()
            if not result.get("choices") or not result["choices"][0].get("message", {}).get("content"):
                raise Exception("Empty response from DeepSeek")
                
            content = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})
            
            return {
                "emotion": json.loads(content),
                "usage": {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                    "model": "deepseek-chat",
                    "cost_estimate": round((usage.get("total_tokens", 0) * 0.002) / 1000, 6)
                }
            }

    async def analyze(self, text: str, retry_count: int = 0) -> Dict[str, Any]:
        try:
            from app.utils.token_utils import estimate_tokens, MAX_TOKENS, retry_with_timeout
            
            # Check token count
            estimated_tokens = estimate_tokens(text)
            if estimated_tokens > MAX_TOKENS:
                raise ValueError(f"Text too long ({estimated_tokens} tokens)")
                
            async def _make_openai_call():
                client = OpenAI(timeout=30.0, max_retries=2)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": text}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3,
                    max_tokens=150
                )
                if not response.choices or not response.choices[0].message.content:
                    raise Exception("Empty response from OpenAI")
                    
                content = response.choices[0].message.content
                usage = response.usage
                if not usage:
                    raise Exception("No usage information available")
                
                logging.info(f"Input text: {text[:200]}...")
                logging.info(f"Raw OpenAI API Response: {response}")
                
                try:
                    result = json.loads(content)
                    logging.info(f"Parsed result: {result}")
                    
                    if not isinstance(result, dict):
                        raise ValueError(f"Expected dict response, got {type(result)}")
                        
                    if "emotion" not in result or "score" not in result:
                        raise ValueError(f"Missing required fields in response: {result}")
                        
                    if result.get("emotion") == "unknown":
                        raise ValueError(f"Model returned unknown emotion: {result}")
                        
                    if result["emotion"] not in ["喜悦", "愤怒", "悲伤", "惊讶", "忧虑", "恐惧", "期待", "满意", "焦虑"]:
                        raise ValueError(f"Invalid emotion type: {result['emotion']}")
                        
                    if not isinstance(result["score"], (int, float)) or not (0 <= float(result["score"]) <= 5):
                        raise ValueError(f"Invalid emotion score: {result['score']}")
                        
                except json.JSONDecodeError as e:
                    logging.error(f"Failed to parse JSON response: {e}")
                    logging.error(f"Raw content: {content}")
                    raise ValueError(f"Invalid JSON response from OpenAI API: {content}")
                except ValueError as e:
                    logging.error(str(e))
                    raise
                
                emotion_data = {
                    "emotion": result["emotion"],
                    "score": float(result["score"])
                }
                
                return {
                    "emotion": emotion_data,
                    "usage": {
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens": usage.total_tokens,
                        "model": "gpt-3.5-turbo",
                        "cost_estimate": round((usage.prompt_tokens * 0.001 + usage.completion_tokens * 0.002) / 1000, 6)
                    }
                }
            
            try:
                result = await retry_with_timeout(_make_openai_call)
                return result
            except Exception as e:
                logging.error(f"OpenAI API error: {str(e)}")
                if retry_count < 3:
                    logging.info(f"Falling back to DeepSeek API (attempt {retry_count + 1})")
                    try:
                        return await self._make_deepseek_call(text)
                    except Exception as e:
                        logging.error(f"DeepSeek API error: {str(e)}")
                        if retry_count < 2:
                            logging.info(f"Retrying with OpenAI (attempt {retry_count + 2})")
                            return await self.analyze(text, retry_count + 1)
                        raise Exception(f"Both APIs failed after retries: {str(e)}")
                raise
        except Exception as e:
            raise Exception(f"Error analyzing emotion: {str(e)}")
