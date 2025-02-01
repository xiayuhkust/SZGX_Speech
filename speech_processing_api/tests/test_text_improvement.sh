#!/usr/bin/env bash

# Change to the speech_processing_api directory
cd "$(dirname "$0")/.." || exit 1

# Create a test file with grammar errors and biblical references
cat > test_input_improvement.txt << 'EOL'
我今天心情特别的好，因为项目终于完成了。这个项目让我学会很多东西。就像马太福音5:3说的那样："虚心的人有福了！因为天国是他们的。"

这段时间工作压力大，每天加班到很晚。但是就像腓立比书4章13节所说："我靠着那加给我力量的，凡事都能做。"这句话一直激励着我前进。

我们团队遇到一些困难，但是大家互相帮助。有时候觉得好像走不下去，但是想到约翰福音16章33节的话："在世上你们有苦难。但你们可以放心，我已经胜了世界。"就充满了信心。

这段文字有一些语病需要修正，比如重复词语使用过多。有些句子也不够通顺流畅。但是经文引用部分应该保持原样不变。
EOL

# Start the FastAPI app
poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000 &
APP_PID=$!

sleep 3  # wait for server to spin up

# Test text improvement endpoint
echo "Testing text improvement API..."
curl -X POST "http://127.0.0.1:8000/api/v1/text/process" \
    -H "Content-Type: application/json" \
    -d @<(cat <<EOF
{
    "text": "$(cat test_input_improvement.txt)"
}
EOF
)

echo -e "\n\nTesting file upload endpoint..."
curl -X POST "http://127.0.0.1:8000/api/v1/file/upload" \
    -H "Content-Type: multipart/form-data" \
    -F "file=@test_input_improvement.txt"

# Clean up
rm test_input_improvement.txt
kill $APP_PID
