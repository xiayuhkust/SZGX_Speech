#!/usr/bin/env bash

# Change to the speech_processing_api directory
cd "$(dirname "$0")/.." || exit 1

# Create a test file with varying emotions
cat > test_input.txt << 'EOL'
今天真是太开心了！真的太开心了！我终于完成了这个项目。这个项目让我学到了很多。我感到非常兴奋和激动，因为这是一个重要的里程碑。这真是一个重要的里程碑啊！让我们继续努力，继续前进。

昨天的会议让我很失望。我们的提案被否决了，团队的努力似乎都白费了。这种挫折感让人难以接受，但我知道这是工作中必须面对的现实。

最近工作压力很大，每天都在加班。虽然很累，但看到项目一步步推进，内心还是充满希望。我相信通过我们的努力，一定能够达到目标。

听说公司要调整部门架构，大家都很紧张。不知道这会给我们带来什么样的变化。希望一切都能往好的方向发展。
EOL

# Start the FastAPI app
poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000 &
APP_PID=$!

sleep 3  # wait for server to spin up

# Test file upload endpoint
curl -X POST "http://127.0.0.1:8000/api/v1/file/upload" \
    -H "Content-Type: multipart/form-data" \
    -F "file=@test_input.txt"

# Clean up
rm test_input.txt
kill $APP_PID
