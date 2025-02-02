from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.text_processor import TextProcessor

router = APIRouter(prefix="/api/v1/text", tags=["text"])

class TextRequest(BaseModel):
    text: str

@router.post("/process")
async def process_text(request: TextRequest):
    """Process text through the emotion-aware pipeline."""
    try:
        processor = TextProcessor()
        result = await processor.process_text(request.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
