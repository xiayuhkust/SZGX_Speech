import json
from pathlib import Path
from app.services.history_logger import HistoryLogger

def test_logging():
    logger = HistoryLogger()
    test_input = "测试文本"
    test_result = {
        "segments": [{"text": "测试文本", "emotion": {"emotion": "平静", "score": 0}}],
        "usage": {
            "total_tokens": 10,
            "model": "test-model",
            "text_length": len(test_input),
            "segment_count": 1,
            "cost_estimate": 0.0002
        }
    }
    
    # Log the test data
    log_files = logger.log_run(test_input, test_result)
    print(f"\nLog files created: {log_files}")
    
    # Get the latest log folder
    log_dir = Path("logs/history")
    folders = sorted([f for f in log_dir.iterdir() if f.is_dir()], key=lambda x: x.name, reverse=True)
    if not folders:
        print("No log folders found!")
        return
        
    latest_folder = folders[0]
    print(f"\nChecking log folder: {latest_folder}")
    
    # Verify all required files exist
    required_files = ["processingdetail.json", "tokenusage.json", "finalresult.json"]
    for file_name in required_files:
        file_path = latest_folder / file_name
        if file_path.exists():
            data = json.loads(file_path.read_text(encoding='utf-8'))
            print(f"\n{file_name} exists and contains valid JSON:")
            print(f"Keys: {list(data.keys())}")
        else:
            print(f"ERROR: {file_name} not found!")

if __name__ == "__main__":
    test_logging()
