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
        
        # Enhanced Chinese text segmentation with comprehensive punctuation handling
        import re
        # Split on sentence endings, emotional markers, and rhetorical breaks
        pattern = '([。！？；：，…]+|\.{3,}|\!{2,}|\?{2,}|[!?。！？][—…]+)'
        sentences = [s.strip() for s in re.split(pattern, text) if s.strip()]
        
        # Handle emotional transition markers
        transition_markers = ['但是', '然而', '不过', '可是', '却', '反而', '相反']
        for marker in transition_markers:
            new_sentences = []
            for sentence in sentences:
                if marker in sentence:
                    parts = sentence.split(marker)
                    for i, part in enumerate(parts):
                        if part.strip():
                            if i > 0:
                                new_sentences.append(marker + part.strip())
                            else:
                                new_sentences.append(part.strip())
                else:
                    new_sentences.append(sentence)
            sentences = new_sentences
            
        current_chunk = ""
        chunks = []
        
        for i in range(0, len(sentences)):
            sentence = sentences[i]
            
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
            
            # Enhanced emotion transition detection with comprehensive emotional states
            positive_emotions = ["喜悦", "惊喜", "期待", "满意"]
            negative_emotions = ["忧虑", "悲伤", "恐惧", "愤怒", "失望", "焦虑"]
            neutral_emotions = ["平静", "中性"]
            
            if (emotion_changed or 
                score_diff > 0.5 or 
                (current_emotion["emotion"] in positive_emotions and emotions[i]["emotion"] in negative_emotions) or
                (emotions[i]["emotion"] in positive_emotions and current_emotion["emotion"] in negative_emotions) or
                (current_emotion["emotion"] not in neutral_emotions and emotions[i]["emotion"] in neutral_emotions) or
                any(marker in chunks[i] for marker in transition_markers)):
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
            
        # Enhanced GBK character support
        gbk_specific_chars = {
            '㈠', '㈡', '㈢', '㈣', '㈤', '㈥', '㈦', '㈧', '㈨', '㈩',
            '㊀', '㊁', '㊂', '㊃', '㊄', '㊅', '㊆', '㊇', '㊈', '㊉',
            '㋀', '㋁', '㋂', '㋃', '㋄', '㋅', '㋆', '㋇', '㋈', '㋉', '㋊', '㋋'
        }
        special_chars_map = {i: c for i, c in enumerate(text) if c in gbk_specific_chars}
        
        try:
            # Handle special characters and traditional Chinese conversion
            normalized_text = ""
            for i, char in enumerate(text):
                if i in special_chars_map:
                    normalized_text += special_chars_map[i]
                elif char in {'說':'说', '話':'话', '時':'时', '經':'经', '會':'会', 
                            '這':'这', '個':'个', '們':'们', '從':'从', '應':'应',
                            '將':'将', '為':'为', '與':'与', '無':'无', '實':'实'}:
                    normalized_text += {'說':'说', '話':'话', '時':'时', '經':'经', '會':'会', 
                                      '這':'这', '個':'个', '們':'们', '從':'从', '應':'应',
                                      '將':'将', '為':'为', '與':'与', '無':'无', '實':'实'}[char]
                else:
                    normalized_text += char.encode().decode('utf-8')
            text = normalized_text
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
