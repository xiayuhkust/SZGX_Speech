from typing import List, Dict, Any
import numpy as np
from openai import OpenAI
from app.services.emotion_analyzer import EmotionAnalyzer
from app.services.deduplication import DuplicationDetector

class TextProcessor:
    def __init__(self):
        self.embedding_model = "text-embedding-ada-002"
        self.chunk_size = 1000  # 每个文本块的最大字符数
        self.emotion_analyzer = EmotionAnalyzer()
        self.token_usage = {"total_tokens": 0}
        
    async def get_embedding(self, text: str) -> List[float]:
        client = OpenAI()
        response = client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        self.token_usage["total_tokens"] += response.usage.total_tokens
        return response.data[0].embedding if isinstance(response.data, list) and len(response.data) > 0 else []
        
    async def segment_text(self, text: str) -> Dict[str, Any]:
        """基于语义相似度的文本分段"""
        # 如果文本较短，直接返回
        if len(text) < self.chunk_size:
            # Get embedding for the single segment
            _ = await self.get_embedding(text)
            return {
                "segments": [text],
                "usage": {
                    "total_tokens": self.token_usage["total_tokens"],
                    "model": self.embedding_model,
                    "text_length": len(text),
                    "segment_count": 1,
                    "cost_estimate": round(self.token_usage["total_tokens"] * 0.0001 / 1000, 6)
                }
            }
            
        # 将文本分成初始块
        chunks = [text[i:i+self.chunk_size] for i in range(0, len(text), self.chunk_size)]
        
        # 获取每个块的embedding
        embeddings = []
        for chunk in chunks:
            embedding = await self.get_embedding(chunk)
            embeddings.append(embedding)
            
        # 计算相邻块之间的相似度
        similarities = []
        for i in range(len(embeddings)-1):
            similarity = np.dot(embeddings[i], embeddings[i+1])
            similarities.append(similarity)
            
        # 根据相似度确定分段点
        segments = []
        current_segment = chunks[0]
        
        for i, similarity in enumerate(similarities):
            if similarity < 0.8:  # 相似度阈值
                segments.append(current_segment)
                current_segment = chunks[i+1]
            else:
                current_segment += chunks[i+1]
                
        segments.append(current_segment)
        
        # 去除重复段落
        from app.services.deduplication import DuplicationDetector
        dedup = DuplicationDetector()
        unique_segments = await dedup.find_duplicates(segments)
        
        # Combine token usage from segmentation and deduplication
        total_embedding_usage = {
            "total_tokens": self.token_usage["total_tokens"] + dedup.token_usage["total_tokens"],
            "model": self.embedding_model
        }
        
        total_tokens = total_embedding_usage["total_tokens"]
        return {
            "segments": unique_segments,
            "usage": {
                **total_embedding_usage,
                "text_length": len(text),
                "segment_count": len(unique_segments),
                "cost_estimate": round(total_tokens * 0.0001 / 1000, 6)
            }
        }
