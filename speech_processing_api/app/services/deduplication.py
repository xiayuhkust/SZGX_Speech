from typing import List
import numpy as np
from openai import OpenAI
from app.core.config import settings

class DuplicationDetector:
    def __init__(self):
        self.embedding_model = "text-embedding-ada-002"
        self.similarity_threshold = 0.85
        self.token_usage = {"total_tokens": 0}

    async def get_embedding(self, text: str) -> List[float]:
        client = OpenAI()
        response = client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        self.token_usage["total_tokens"] += response.usage.total_tokens
        return response.data[0].embedding

    async def find_duplicates(self, segments: List[str]) -> List[str]:
        if not segments:
            return []

        # Get embeddings for all segments
        embeddings = []
        for segment in segments:
            embedding = await self.get_embedding(segment)
            embeddings.append(embedding)

        # Calculate similarity matrix
        n = len(segments)
        similarity_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                similarity = np.dot(embeddings[i], embeddings[j])
                similarity_matrix[i][j] = similarity
                similarity_matrix[j][i] = similarity

        # Find unique segments
        unique_segments = []
        used = set()
        
        for i in range(n):
            if i in used:
                continue
                
            unique_segments.append(segments[i])
            
            # Mark similar segments as used
            for j in range(i + 1, n):
                if similarity_matrix[i][j] > self.similarity_threshold:
                    used.add(j)

        return unique_segments
