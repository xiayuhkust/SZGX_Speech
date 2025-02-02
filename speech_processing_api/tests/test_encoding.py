import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.main import app

client = TestClient(app)

@pytest.mark.timeout(30)  # Set timeout to 30 seconds
@pytest.mark.asyncio
async def test_file_upload_with_different_encodings():
    test_files_dir = Path("tests/test_files")
    
    # Test each encoding
    test_cases = [
        ("utf8_test.txt", "UTF-8"),
        ("gb2312_test.txt", "GB2312"),
        ("gbk_test.txt", "GBK", "㈠㈡㈢㈣㈤")  # GBK-specific characters
    ]
    
    for test_case in test_cases:
        filename, expected_encoding = test_case[:2]
        expected_content = test_case[2] if len(test_case) > 2 else None
        
        file_path = test_files_dir / filename
        with open(file_path, "rb") as f:
            content = f.read()
            files = {"file": (filename, content, "text/plain")}
            response = client.post("/api/v1/file/upload", files=files)
            assert response.status_code == 200, f"Failed to upload {filename}"
            
            data = response.json()
            assert "file_id" in data, "Response missing file_id"
            assert "download_url" in data, "Response missing download_url"
            
            # Verify encoding info in response
            assert "encoding_info" in data, "Response missing encoding_info"
            assert data["encoding_info"]["encoding"].upper() == expected_encoding, \
                f"Expected {expected_encoding} encoding, got {data['encoding_info']['encoding']}"
            
            # For GBK test, verify that GBK-specific characters are preserved
            if expected_content:
                download_response = client.get(f"/api/v1/file/download/{data['file_id']}")
                assert download_response.status_code == 200, f"Failed to download processed {filename}"
                result_text = download_response.text
                assert expected_content in result_text, \
                    f"GBK-specific characters not preserved in {filename}"
