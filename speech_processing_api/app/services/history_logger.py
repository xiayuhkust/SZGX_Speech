from typing import Dict, Any, List
import json
from datetime import datetime
import os
from pathlib import Path

class HistoryLogger:
    """Handles logging of text processing history and token usage."""
    
    def __init__(self):
        self.log_dir = Path("logs/history")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_timestamp(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def log_run(self, input_text: str, result: Dict[str, Any]) -> Dict[str, str]:
        """Log the results of a text processing run.
        
        Args:
            input_text: Original input text
            result: Processing result containing segments and usage info
            
        Returns:
            Dict containing paths to the generated log files
        """
        timestamp = self._get_timestamp()
        
        # Log token usage
        usage_file = self.log_dir / f"token_usage_{timestamp}.json"
        usage_data = {
            "timestamp": timestamp,
            "total_tokens": result["usage"]["total_tokens"],
            "model": result["usage"]["model"],
            "text_length": result["usage"]["text_length"],
            "segment_count": result["usage"]["segment_count"],
            "cost_estimate": result["usage"]["cost_estimate"]
        }
        usage_file.write_text(json.dumps(usage_data, indent=2, ensure_ascii=False))
        
        # Log text processing details
        processing_file = self.log_dir / f"processing_details_{timestamp}.json"
        processing_data = {
            "timestamp": timestamp,
            "input_text": input_text,
            "segments": result["segments"]
        }
        processing_file.write_text(json.dumps(processing_data, indent=2, ensure_ascii=False))
        
        return {
            "usage_log": str(usage_file),
            "processing_log": str(processing_file)
        }
