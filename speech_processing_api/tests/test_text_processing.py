import pytest
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to Python path and load environment variables
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
load_dotenv(project_root / ".env")

from app.services.text_processor import TextProcessor
from app.worker import celery_app, process_text
from app.utils.token_utils import estimate_tokens

def test_text_processing():
    # Test text with mixed emotions, biblical references, and GBK characters
    test_text = """今天真是太开心了！真的太开心了！我终于完成了这个项目。
    这个项目让我学到了很多。我感到非常兴奋和激动，因为这是一个重要的里程碑。
    这真是一个重要的里程碑啊！让我们继续努力，继续前进。
    但是想到前方的困难，我心里也充满忧虑。正如圣经所说：「应当一无挂虑，
    只要凡事藉着祷告、祈求和感谢，将你们所要的告诉神。」（腓立比书4:6）
    这给了我很大的安慰和鼓励。㈠㈡㈢㈣㈤"""
    
    # Test synchronous processing through Celery
    task = process_text.delay(test_text)
    result = task.get(timeout=30)
    
    # Verify result structure
    assert "segments" in result
    assert "usage" in result
    assert len(result["segments"]) > 0
    
    # Verify token usage tracking
    assert "total_tokens" in result["usage"]
    assert "cost_estimate" in result["usage"]
    assert "model" in result["usage"]
    
    # Verify segment structure and content
    emotions_found = set()
    biblical_refs_found = False
    gbk_chars_preserved = False
    
    for segment in result["segments"]:
        assert "text" in segment
        assert "emotion" in segment
        assert "changes" in segment
        assert isinstance(segment["biblical_references"], list)
        
        # Verify emotion scoring
        assert "score" in segment["emotion"]
        assert isinstance(segment["emotion"]["score"], (int, float))
        assert 0 <= segment["emotion"]["score"] <= 5
        
        # Track emotions found
        emotions_found.add(segment["emotion"]["emotion"])
        
        # Check for biblical references
        if segment["biblical_references"]:
            biblical_refs_found = True
            assert any("腓立比书4:6" in ref for ref in segment["biblical_references"])
        
        # Check for GBK characters
        if any(char in segment["text"] for char in "㈠㈡㈢㈣㈤"):
            gbk_chars_preserved = True
    
    # Print debug information
    print("\nDebug: Emotions found:", emotions_found)
    print("Debug: Segments:", [
        {
            "text": s["text"][:50] + "...",
            "emotion": s["emotion"]
        } for s in result["segments"]
    ])
    
    # Verify multiple emotions detected
    assert len(result["segments"]) >= 2, f"Should detect at least 2 segments, found {len(result['segments'])}"
    assert len(emotions_found) >= 2, f"Should detect multiple emotions, found: {emotions_found}"
    
    # Get emotion sequence
    emotion_sequence = [segment["emotion"]["emotion"] for segment in result["segments"]]
    print("Debug: Emotion sequence:", emotion_sequence)
    
    # Verify emotions and their sequence
    assert "喜悦" in emotions_found, f"Should detect joyful emotions, found: {emotions_found}"
    assert "忧虑" in emotions_found, f"Should detect worried emotions, found: {emotions_found}"
    assert emotion_sequence[0] == "喜悦", f"First segment should be joyful, got: {emotion_sequence[0]}"
    assert any(e == "忧虑" for e in emotion_sequence[1:]), f"Later segment should be worried, sequence: {emotion_sequence}"
    
    # Verify biblical reference detection
    assert biblical_refs_found, "Should detect Philippians 4:6 reference"
    
    # Verify GBK character preservation
    assert gbk_chars_preserved, "Should preserve GBK-specific characters"

@pytest.mark.asyncio
async def test_large_text_processing():
    processor = TextProcessor()
    # Generate large text (>16K tokens)
    large_text = "这是一个测试。" * 5000
    
    try:
        result = await processor.process_text(large_text)
        assert result["segments"], "Should have processed segments"
        assert result["usage"]["total_tokens"] > 0, "Should track token usage"
        assert all(s["emotion"] for s in result["segments"]), "All segments should have emotion"
        
        # Verify token estimation
        total_tokens = estimate_tokens(large_text)
        assert total_tokens > 16000, "Test text should exceed token limit"
        
        # Check segment sizes
        for segment in result["segments"]:
            segment_tokens = estimate_tokens(segment["text"])
            assert segment_tokens <= 16000, "Each segment should be within token limit"
            
    except Exception as e:
        assert False, f"Should handle large text without errors: {str(e)}"
