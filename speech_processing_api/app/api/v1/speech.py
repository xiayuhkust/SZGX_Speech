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
        segments = await processor.segment_text(request.text)
        emotion_analysis = await processor.emotion_analyzer.analyze(request.text)
        return {
            "status": "success",
            "message": "Processed text segments with emotion analysis",
            "data": {
                "segments": segments,
                "emotion": emotion_analysis
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
