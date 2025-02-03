from typing import List, Dict, Any
import numpy as np
import logging
from openai import OpenAI
from app.services.emotion_analyzer import EmotionAnalyzer
from app.services.deduplication import DuplicationDetector
from app.services.text_improver import TextImprover
from app.services.biblical_reference_detector import BiblicalReferenceDetector
from app.services.history_logger import HistoryLogger

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class TextSegmentProcessor:
    """Handles text segmentation based on emotional content analysis."""
    
    def __init__(self):
        self.emotion_analyzer = EmotionAnalyzer()
        from app.utils.token_utils import CHUNK_SIZE
        self.chunk_size = CHUNK_SIZE
        self.token_usage = {"total_tokens": 0}
        self.similarity_threshold = 0.8
        
    def _split_into_sentences(self, text: str) -> List[str]:
        import re
        pattern = '([。！？]+)'
        sentences = []
        parts = [p.strip() for p in re.split(pattern, text) if p.strip()]
        
        current = ""
        for part in parts:
            if re.match(pattern, part):
                current += part
                if current:
                    sentences.append(current)
                current = ""
            else:
                current = part
                
        if current:
            sentences.append(current)
            
        # Handle emotional transitions without breaking context
        transition_markers = ['但是', '然而', '不过', '可是', '却']
        result = []
        for sentence in sentences:
            split_needed = False
            for marker in transition_markers:
                if marker in sentence:
                    parts = sentence.split(marker)
                    if len(parts) == 2 and all(len(p.strip()) > 5 for p in parts):
                        before, after = parts
                        if before.strip():
                            result.append(before.strip())
                        if after.strip():
                            result.append(marker + after.strip())
                        split_needed = True
                        break
            if not split_needed:
                result.append(sentence)
                
        return [s for s in result if len(s.strip()) > 5]

    async def segment_by_emotion(self, text: str) -> Dict[str, Any]:
        if not text:
            return {
                "segments": [],
                "usage": {"total_tokens": 0, "model": "gpt-3.5-turbo"}
            }
            
        from app.utils.token_utils import estimate_tokens, CHUNK_SIZE
        
        # Split text into manageable chunks
        chunks = []
        current_chunk = ""
        current_tokens = 0
        
        for sentence in self._split_into_sentences(text):
            sentence_tokens = estimate_tokens(sentence)
            if current_tokens + sentence_tokens > CHUNK_SIZE:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
                current_tokens = sentence_tokens
            else:
                current_chunk += sentence
                current_tokens += sentence_tokens
                
        if current_chunk:
            chunks.append(current_chunk)
            
        if not chunks:
            chunks = [text]
            
        # Process each chunk
        all_segments = []
        total_tokens = 0
        current_segment = ""
        current_emotion = None
        
        for chunk in chunks:
            try:
                result = await self.emotion_analyzer.analyze(chunk)
                if "error" in result:
                    continue
                    
                emotion_data = result.get("emotion", {"emotion": "unknown", "score": 0})
                
                if current_emotion is None:
                    current_emotion = emotion_data
                    current_segment = chunk
                else:
                    emotion_changed = emotion_data["emotion"] != current_emotion["emotion"]
                    score_diff = abs(emotion_data["score"] - current_emotion["score"])
                    
                    positive_emotions = ["喜悦", "惊喜", "期待", "满意"]
                    negative_emotions = ["忧虑", "悲伤", "恐惧", "愤怒", "失望", "焦虑"]
                    neutral_emotions = ["平静", "中性"]
                    
                    if (emotion_changed or 
                        score_diff > 0.5 or 
                        (current_emotion["emotion"] in positive_emotions and emotion_data["emotion"] in negative_emotions) or
                        (emotion_data["emotion"] in positive_emotions and current_emotion["emotion"] in negative_emotions) or
                        (current_emotion["emotion"] not in neutral_emotions and emotion_data["emotion"] in neutral_emotions)):
                        
                        all_segments.append({
                            "text": current_segment,
                            "emotion": current_emotion,
                            "changes": []
                        })
                        current_segment = chunk
                        current_emotion = emotion_data
                    else:
                        current_segment += chunk
                        
                total_tokens += result.get("usage", {}).get("total_tokens", 0)
                
            except ValueError as e:
                if "Text too long" in str(e):
                    continue
                raise
                
        if current_segment:
            all_segments.append({
                "text": current_segment,
                "emotion": current_emotion,
                "changes": []
            })
            
        return {
            "segments": all_segments,
            "usage": {
                "total_tokens": total_tokens,
                "model": "gpt-3.5-turbo",
                "text_length": len(text),
                "segment_count": len(all_segments)
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
            
        # Handle text encoding
        from app.utils.token_utils import normalize_encoding
        try:
            text = normalize_encoding(text)
        except UnicodeError as e:
            logging.error(f"文本编码错误: {str(e)}, 文本: {text[:100]}...")
            raise ValueError(f"文本编码错误: {str(e)}")
        except Exception as e:
            logging.error(f"处理文本时出错: {str(e)}, 文本: {text[:100]}...")
            raise ValueError(f"处理文本时出错: {str(e)}")
            
        if len(text.strip()) < 10:
            logging.warning(f"文本过短: {text}")
            raise ValueError("文本长度必须大于10个字符")
            
        # Step 1: Split text at emotional transitions and analyze each part
        try:
            parts = text.split("但是")
            all_segments = []
            total_tokens = 0
            
            for part in parts:
                if part.strip():
                    try:
                        segment_result = await self.segment_processor.segment_by_emotion(part.strip())
                        total_tokens += segment_result["usage"]["total_tokens"]
                        all_segments.extend(segment_result["segments"])
                    except Exception as e:
                        logging.error(f"处理文本段落时出错: {str(e)}, 段落: {part[:100]}...")
                        continue
                        
            if not all_segments:
                logging.error("文本分段处理失败，没有生成任何有效段落")
                raise ValueError("文本处理失败：无法生成有效的文本段落")
                
        except Exception as e:
            logging.error(f"文本分段处理失败: {str(e)}")
            raise
            
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
            try:
                improved_result = await self.text_improver.improve_text(
                    current_text,
                    emotion_score=segment["emotion"]["score"],
                    emotion_type=segment["emotion"]["emotion"]
                )
                
                import json
                result_json = json.loads(improved_result["result"])
                improved_text = result_json["improved_text"]
                
                if not improved_text or len(improved_text.strip()) < 5:
                    logging.warning(f"文本改进结果无效: {current_text[:100]}...")
                    improved_text = current_text
            except Exception as e:
                logging.error(f"改进文本时出错: {str(e)}, 原文: {current_text[:100]}...")
                improved_text = current_text
            
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
        try:
            dedup_result = await self.dedup.find_duplicates([s["text"] for s in processed_segments])
            if isinstance(dedup_result, dict):
                usage_data = getattr(dedup_result, "usage", {})
                if isinstance(usage_data, dict):
                    self.token_usage["total_tokens"] += usage_data.get("total_tokens", 0)
                    
                # Filter out duplicate segments
                unique_segments = []
                seen_texts = set()
                for segment in processed_segments:
                    if segment["text"] not in seen_texts:
                        unique_segments.append(segment)
                        seen_texts.add(segment["text"])
                processed_segments = unique_segments
                
                if len(unique_segments) < len(processed_segments):
                    logging.info(f"去重完成: 从{len(processed_segments)}段减少到{len(unique_segments)}段")
        except Exception as e:
            logging.error(f"文本去重时出错: {str(e)}")
            # Continue with original segments if deduplication fails
        
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
        
        # Log the processing run and handle any errors
        try:
            log_files = self.history_logger.log_run(text, result)
            result["log_files"] = log_files
        except Exception as e:
            logging.error(f"记录处理历史时出错: {str(e)}")
            result["log_files"] = []
            
        # Add processing summary to result
        result["summary"] = {
            "original_length": len(text),
            "processed_length": sum(len(s["text"]) for s in processed_segments),
            "segment_count": len(processed_segments),
            "has_duplicates": len(unique_segments) < len(processed_segments) if 'unique_segments' in locals() else False,
            "processing_status": "success"
        }
        
        logging.info(f"文本处理完成: {result['summary']}")
        return result
