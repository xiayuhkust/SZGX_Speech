#!/usr/bin/env bash

# Change to the speech_processing_api directory
cd "$(dirname "$0")/.." || exit 1

# Create a test file
echo "今天真是太开心了！真的太开心了！我终于完成了这个项目。这个项目让我学到了很多。我感到非常兴奋和激动，因为这是一个重要的里程碑。这真是一个重要的里程碑啊！让我们继续努力，继续前进。" > test_input.txt

# Start the FastAPI app
poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000 &
APP_PID=$!

sleep 3  # wait for server to spin up

# Test file upload endpoint
curl -X POST "http://127.0.0.1:8000/api/v1/file/upload" \
    -H "Content-Type: multipart/form-data" \
    -F "file=@test_input.txt" \
    --output test_output.txt

# Clean up
rm test_input.txt
kill $APP_PID
