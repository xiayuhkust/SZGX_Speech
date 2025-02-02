import pytest
import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to Python path and load environment variables
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
load_dotenv(project_root / ".env")

from app.services.text_processor import TextProcessor
from app.worker import celery_app, process_text
from app.utils.token_utils import estimate_tokens
from tests.test_data import load_test_data

@pytest.mark.asyncio
async def test_text_processing():
    processor = TextProcessor()
    test_data = load_test_data()
    test_text = test_data["mixed_emotions"][:3000]  # Use first 3000 characters
    
    result = await processor.process_text(test_text)
    
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
    for segment in result["segments"]:
        assert "text" in segment
        assert "emotion" in segment
        assert "changes" in segment
        
        # Verify emotion scoring
        assert "score" in segment["emotion"]
        assert isinstance(segment["emotion"]["score"], (int, float))
        assert 0 <= segment["emotion"]["score"] <= 5
        
        emotions_found.add(segment["emotion"]["emotion"])
    
    # Verify multiple emotions detected
    assert len(emotions_found) >= 2, f"Should detect multiple emotions, found: {emotions_found}"
    
    # Verify log files
    assert "log_files" in result
    assert all(key in result["log_files"] for key in ["usage_log", "processing_log", "final_result"])
    
    # Check final result format
    final_path = Path(result["log_files"]["final_result"])
    assert final_path.suffix == ".txt"
    content = final_path.read_text(encoding='utf-8')
    
    # Verify content is clean text
    assert "{" not in content
    assert "}" not in content
    assert len(content.strip()) > 0

@pytest.mark.asyncio
async def test_output_format():
    processor = TextProcessor()
    test_data = load_test_data()
    result = await processor.process_text(test_data["mixed_emotions"])
    
    # Verify log files structure
    assert "log_files" in result
    assert all(key in result["log_files"] for key in ["usage_log", "processing_log", "final_result"])
    
    # Check file types
    final_path = Path(result["log_files"]["final_result"])
    processing_path = Path(result["log_files"]["processing_log"])
    usage_path = Path(result["log_files"]["usage_log"])
    
    assert final_path.suffix == ".txt"
    assert processing_path.suffix == ".json"
    assert usage_path.suffix == ".json"
    
    # Verify content formats
    final_content = final_path.read_text(encoding='utf-8')
    processing_content = json.loads(processing_path.read_text(encoding='utf-8'))
    usage_content = json.loads(usage_path.read_text(encoding='utf-8'))
    
    # Check final result is clean text
    assert "{" not in final_content
    assert "}" not in final_content
    assert len(final_content.strip()) > 0
    
    # Check processing details
    assert "segments" in processing_content
    assert "timestamp" in processing_content
    assert "input_text" in processing_content
    
    # Check usage tracking
    assert "total_tokens" in usage_content
    assert "model" in usage_content
    assert "cost_estimate" in usage_content
