#!/bin/bash
curl -X POST "http://localhost:8000/api/v1/text/process" -H "Content-Type: application/json" -d '{"text": "今天真是太开心了！真的太开心了！我终于完成了这个项目。这个项目让我学到了很多。我感到非常兴奋和激动，因为这是一个重要的里程碑。这真是一个重要的里程碑啊！让我们继续努力，继续前进。"}'