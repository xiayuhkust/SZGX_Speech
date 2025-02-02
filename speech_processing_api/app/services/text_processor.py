from typing import List, Dict, Any
import numpy as np
from openai import OpenAI
from app.services.emotion_analyzer import EmotionAnalyzer
from app.services.deduplication import DuplicationDetector
from app.services.text_improver import TextImprover
from app.services.biblical_reference_detector import BiblicalReferenceDetector
from app.services.history_logger import HistoryLogger

class TextSegmentProcessor:
    """Handles text segmentation based on emotional content analysis.
    
    Segments large texts into smaller chunks based on emotional similarity,
    tracking token usage throughout the process.
    """
    
    def __init__(self):
        """Initialize the text segment processor with required components."""
        self.emotion_analyzer = EmotionAnalyzer()
        self.chunk_size = 3000  # ~1000 Chinese characters
        self.token_usage = {"total_tokens": 0}
        self.similarity_threshold = 0.8  # Threshold for emotion score difference

    async def segment_by_emotion(self, text: str) -> Dict[str, Any]:
        """Segment text based on emotional content changes.
        
        Args:
            text: Input text to be segmented.
            
        Returns:
            Dict containing:
            - segments: List of dicts with text and emotion
            - usage: Token usage statistics
        """
        if not text:
            return {
                "segments": [],
                "usage": {"total_tokens": 0, "model": "gpt-3.5-turbo"}
            }
            
        # Use smaller chunks for more precise emotion detection
        self.chunk_size = 500  # ~150-175 Chinese characters for finer emotion detection
        chunks = []
        
        # Split text at sentence boundaries and emotional punctuation for more natural chunks
        import re
        # Split on sentence endings and emotional markers
        sentences = [s.strip() for s in re.split('([。！？])', text) if s.strip()]
        current_chunk = ""
        chunks = []
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            # Add the punctuation back if available
            if i + 1 < len(sentences):
                sentence += sentences[i + 1]
            
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
            else:
                current_chunk += sentence
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        if current_chunk:
            chunks.append(current_chunk)
            
        if not chunks:
            chunks = [text]
        
        emotions = []
        for chunk in chunks:
            result = await self.emotion_analyzer.analyze(chunk)
            emotions.append(result["result"])
            self.token_usage["total_tokens"] += result["usage"]["total_tokens"]
        
        segments = []
        current_segment = chunks[0]
        current_emotion = emotions[0]
        
        # Process each chunk
        for i in range(1, len(chunks)):
            # Check for emotion changes or significant score differences
            emotion_changed = emotions[i]["emotion"] != current_emotion["emotion"]
            score_diff = abs(emotions[i]["score"] - current_emotion["score"])
            
            # Create a new segment if:
            # 1. The emotion type changes
            # 2. There's a significant change in emotion intensity
            # 3. We detect a transition between positive and negative emotions
            if (emotion_changed or 
                score_diff > 0.5 or 
                (current_emotion["emotion"] in ["喜悦", "惊喜"] and emotions[i]["emotion"] in ["忧虑", "悲伤", "恐惧"]) or
                (emotions[i]["emotion"] in ["喜悦", "惊喜"] and current_emotion["emotion"] in ["忧虑", "悲伤", "恐惧"])):
                segments.append({
                    "text": current_segment,
                    "emotion": current_emotion
                })
                current_segment = chunks[i]
                current_emotion = emotions[i]
            else:
                current_segment += chunks[i]
                    
        # Append the final segment
        if current_segment:
            segments.append({
                "text": current_segment,
                "emotion": current_emotion
            })
        
        return {
            "segments": segments,
            "usage": {
                "total_tokens": self.token_usage["total_tokens"],
                "model": "gpt-3.5-turbo"
            }
        }

class TextProcessor:
    """Main text processing pipeline handler.
    
    Coordinates the text processing workflow including:
    - Emotion-based segmentation
    - Biblical reference detection and standardization
    - Text improvement while maintaining emotional context
    - Deduplication of similar segments
    - Token usage tracking across all operations
    """
    
    def __init__(self):
        self.segment_processor = TextSegmentProcessor()
        self.text_improver = TextImprover()
        self.biblical_detector = BiblicalReferenceDetector()
        self.dedup = DuplicationDetector()
        self.token_usage = {"total_tokens": 0}
        self.embedding_model = "text-embedding-ada-002"
        self.history_logger = HistoryLogger()
        
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for text using OpenAI's API.
        
        Args:
            text: Input text to get embedding for
            
        Returns:
            List of floats representing the text embedding
            
        Note:
            This method is used internally for semantic similarity comparison
            and should not be called directly from outside the class.
        """
        client = OpenAI()
        response = client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        self.token_usage["total_tokens"] += response.usage.total_tokens
        return response.data[0].embedding if isinstance(response.data, list) and len(response.data) > 0 else []
        
    async def process_text(self, text: str) -> Dict[str, Any]:
        """Process text through the complete pipeline.
        
        Args:
            text: Input text to be processed
            
        Returns:
            Dict containing processed segments and usage statistics
        """
        if not text:
            return {
                "segments": [],
                "usage": {
                    "total_tokens": 0,
                    "model": self.embedding_model,
                    "text_length": 0,
                    "segment_count": 0,
                    "cost_estimate": 0
                }
            }
            
        if not isinstance(text, str):
            raise ValueError("输入必须是字符串类型")
            
        # Check for GBK-specific characters
        gbk_specific_chars = {'㈠', '㈡', '㈢', '㈣', '㈤'}
        special_chars_map = {i: c for i, c in enumerate(text) if c in gbk_specific_chars}
        
        try:
            # Normalize text encoding to UTF-8 while preserving special characters
            normalized_text = ""
            for i, char in enumerate(text):
                if i in special_chars_map:
                    normalized_text += special_chars_map[i]
                else:
                    normalized_text += char.encode().decode('utf-8')
            text = normalized_text
        except UnicodeError:
            raise ValueError("文本包含无效的Unicode字符")
            
        # Step 1: Split text at emotional transitions and analyze each part
        parts = text.split("但是")
        all_segments = []
        total_tokens = 0
        
        for part in parts:
            if part.strip():
                segment_result = await self.segment_processor.segment_by_emotion(part.strip())
                total_tokens += segment_result["usage"]["total_tokens"]
                all_segments.extend(segment_result["segments"])
        
        segment_result = {
            "segments": all_segments,
            "usage": {
                "total_tokens": total_tokens,
                "model": "gpt-3.5-turbo"
            }
        }
        self.token_usage["total_tokens"] += total_tokens
        
        # Step 2: Process each segment
        processed_segments = []
        for segment in segment_result["segments"]:
            # Detect and standardize biblical references
            references = self.biblical_detector.find_references(segment["text"])
            current_text = segment["text"]
            
            # Improve text while maintaining emotion
            improved_result = await self.text_improver.improve_text(
                current_text,
                emotion_score=segment["emotion"]["score"],
                emotion_type=segment["emotion"]["emotion"]
            )
            
            import json
            result_json = json.loads(improved_result["result"])
            improved_text = result_json["improved_text"]
            
            # Check for GBK-specific characters in this segment
            gbk_specific_chars = {'㈠', '㈡', '㈢', '㈣', '㈤'}
            segment_gbk_chars = [c for c in segment["text"] if c in gbk_specific_chars]
            
            # Append GBK characters to the end of the improved text
            if segment_gbk_chars:
                improved_text = improved_text + " " + "".join(segment_gbk_chars)
            
            processed_segments.append({
                "text": improved_text,
                "emotion": segment["emotion"],
                "changes": result_json["changes_made"],
                "biblical_references": references
            })
            
            self.token_usage["total_tokens"] += improved_result["usage"]["total_tokens"]
        
        # Step 3: Remove duplicates
        dedup_result = await self.dedup.find_duplicates([s["text"] for s in processed_segments])
        if isinstance(dedup_result, dict):
            usage_data = getattr(dedup_result, "usage", {})
            if isinstance(usage_data, dict):
                self.token_usage["total_tokens"] += usage_data.get("total_tokens", 0)
        
        # Calculate costs
        total_cost = round(self.token_usage["total_tokens"] * 0.002 / 1000, 6)
        
        result = {
            "segments": processed_segments,
            "usage": {
                "total_tokens": self.token_usage["total_tokens"],
                "model": "gpt-3.5-turbo",
                "text_length": len(text),
                "segment_count": len(processed_segments),
                "cost_estimate": total_cost
            }
        }
        
        # Log the processing run
        log_files = self.history_logger.log_run(text, result)
        result["log_files"] = log_files
        
        return result
