from pathlib import Path
import json
from typing import Dict, Any

def load_test_data(name: str = "default") -> Dict[str, Any]:
    """Load test data from JSON files."""
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    data_file = data_dir / f"{name}.json"
    if not data_file.exists():
        # Create default test data if it doesn't exist
        default_data = {
            "short_text": "今天真是太开心了！我终于完成了这个项目。这个项目让我学到了很多。",
            "mixed_emotions": """今天真是太开心了！我终于完成了这个项目。
            这个项目让我学到了很多。我感到非常兴奋和激动，因为这是一个重要的里程碑。
            但是想到前方的困难，我心里也充满忧虑。""",
            "biblical_text": """正如圣经所说：「应当一无挂虑，
            只要凡事藉着祷告、祈求和感谢，将你们所要的告诉神。」（腓立比书4:6）""",
            "special_chars": "㈠㈡㈢㈣㈤",
            "max_length": 3000  # Maximum length for test text
        }
        data_file.write_text(json.dumps(default_data, indent=2, ensure_ascii=False))
        return default_data
    
    return json.loads(data_file.read_text())
