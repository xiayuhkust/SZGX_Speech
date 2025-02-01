from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.text_processor import TextProcessor

router = APIRouter(prefix="/api/v1/text", tags=["text"])

class SpeechRequest(BaseModel):
    text: str

@router.post("/process")
async def process_speech(request: SpeechRequest):
    try:
        processor = TextProcessor()
        # Reset token usage before processing
        processor.token_usage = {"total_tokens": 0}
        
        # Process text and analyze emotion
        segments_result = await processor.segment_text(request.text)
        emotion_result = await processor.emotion_analyzer.analyze(request.text)
        
        return {
            "status": "success",
            "message": "Processed text segments with emotion analysis",
            "data": {
                "segments": segments_result["segments"],
                "emotion": emotion_result["result"]
            },
            "usage": {
                "openai_embedding_tokens": {
                    "total_tokens": segments_result["usage"]["total_tokens"],
                    "model": segments_result["usage"]["model"]
                },
                "openai_chat_tokens": emotion_result["usage"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
