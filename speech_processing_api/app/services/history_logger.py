from typing import Dict, Any, List
import json
from datetime import datetime
import os
from pathlib import Path

class HistoryLogger:
    def __init__(self):
        self.log_dir = Path("logs/history")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_timestamp(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def _create_run_folder(self, timestamp: str) -> Path:
        folder = self.log_dir / timestamp
        folder.mkdir(exist_ok=True)
        return folder
        
    def log_run(self, input_text: str, result: Dict[str, Any]) -> Dict[str, str]:
        timestamp = self._get_timestamp()
        run_folder = self._create_run_folder(timestamp)
        
        try:
            # Log token usage
            usage_file = run_folder / "tokenusage.json"
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
            processing_file = run_folder / "processingdetail.json"
            processing_data = {
                "timestamp": timestamp,
                "input_text": input_text,
                "segments": result["segments"]
            }
            processing_file.write_text(json.dumps(processing_data, indent=2, ensure_ascii=False))
            
            # Log final result
            final_file = run_folder / "finalresult.json"
            final_data = {
                "timestamp": timestamp,
                "summary": {
                    "original_length": len(input_text),
                    "processed_length": sum(len(s["text"]) for s in result["segments"]),
                    "segment_count": len(result["segments"]),
                    "has_duplicates": any(s.get("is_duplicate", False) for s in result["segments"]),
                    "processing_status": "success"
                },
                "segments": [
                    {
                        "text": segment["text"],
                        "emotion": segment["emotion"],
                        "changes": segment.get("changes", []),
                        "biblical_references": segment.get("biblical_references", [])
                    }
                    for segment in result["segments"]
                ]
            }
            final_file.write_text(json.dumps(final_data, indent=2, ensure_ascii=False))
            
            return {
                "usage_log": str(usage_file),
                "processing_log": str(processing_file),
                "final_result": str(final_file)
            }
            
        except Exception as e:
            error_file = run_folder / "error.json"
            error_data = {
                "timestamp": timestamp,
                "error": str(e),
                "input_text_length": len(input_text)
            }
            error_file.write_text(json.dumps(error_data, indent=2, ensure_ascii=False))
            raise
