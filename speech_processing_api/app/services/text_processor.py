from typing import List, Dict
import numpy as np
from openai import OpenAI
from app.services.emotion_analyzer import EmotionAnalyzer

class TextProcessor:
    def __init__(self):
        self.embedding_model = "text-embedding-ada-002"
        self.chunk_size = 1000  # 每个文本块的最大字符数
        self.emotion_analyzer = EmotionAnalyzer()
        
    async def get_embedding(self, text: str) -> List[float]:
        """获取文本的embedding向量"""
        client = OpenAI()
        response = client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding
        
    async def segment_text(self, text: str) -> List[str]:
        """基于语义相似度的文本分段"""
        # 如果文本较短，直接返回
        if len(text) < self.chunk_size:
            return [text]
            
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
        
        return unique_segments
