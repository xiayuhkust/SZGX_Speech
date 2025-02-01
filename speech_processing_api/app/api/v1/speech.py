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
        
        # Check for biblical references
        has_biblical_refs = processor.biblical_detector.contains_references(request.text)
        biblical_refs = processor.biblical_detector.find_references(request.text) if has_biblical_refs else []
        
        # Process text and analyze emotion
        segments_result = await processor.segment_text(request.text)
        emotion_result = await processor.emotion_analyzer.analyze(request.text)
        
        return {
            "status": "success",
            "message": "Processed text segments with emotion analysis",
            "data": {
                "segments": segments_result["segments"],
                "biblical_references": biblical_refs if biblical_refs else None,
                "emotion": emotion_result["result"]
            },
            "usage": {
                "embedding": segments_result["usage"]["embedding"],
                "improvement": segments_result["usage"]["improvement"],
                "emotion_analysis": emotion_result["usage"],
                "total_cost_estimate": round(
                    segments_result["usage"]["total_cost_estimate"] + 
                    emotion_result["usage"]["cost_estimate"],
                    6
                )
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
