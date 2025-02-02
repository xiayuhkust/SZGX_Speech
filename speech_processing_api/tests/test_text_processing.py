import pytest
from app.services.text_processor import TextProcessor
from app.worker import celery_app, process_text

def test_text_processing():
    # Test text with mixed emotions and potential biblical references
    test_text = """今天真是太开心了！真的太开心了！我终于完成了这个项目。
    这个项目让我学到了很多。我感到非常兴奋和激动，因为这是一个重要的里程碑。
    这真是一个重要的里程碑啊！让我们继续努力，继续前进。"""
    
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
    
    # Verify segment structure
    for segment in result["segments"]:
        assert "text" in segment
        assert "emotion" in segment
        assert "changes" in segment
        assert isinstance(segment["biblical_references"], list)
        
        # Verify emotion scoring
        assert "score" in segment["emotion"]
        assert isinstance(segment["emotion"]["score"], (int, float))
        assert 0 <= segment["emotion"]["score"] <= 5
