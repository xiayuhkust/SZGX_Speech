import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "speech_processing_api"))
from app.services.text_processor import TextProcessor

async def test_processing():
    processor = TextProcessor()
    result = await processor.process_text("今天真是太开心了！真的太开心了！我终于完成了这个项目。这个项目让我学到了很多。我感到非常兴奋和激动，因为这是一个重要的里程碑。这真是一个重要的里程碑啊！让我们继续努力，继续前进。")
    print("Processing Result:")
    print("=================")
    for segment in result["segments"]:
        print("\nText:", segment["text"])
        print("Emotion:", segment["emotion"])
        print("Changes:", segment["changes"])
        if segment["biblical_references"]:
            print("Biblical References:", segment["biblical_references"])
    print("\nToken Usage:", result["usage"])
    print("Log Files:", result["log_files"])

if __name__ == "__main__":
    asyncio.run(test_processing())
