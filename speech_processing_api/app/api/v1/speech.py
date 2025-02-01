from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/speech", tags=["speech"])

class SpeechRequest(BaseModel):
    text: str

@router.post("/process")
async def process_speech(request: SpeechRequest):
    try:
        return {"status": "success", "message": "Text received for processing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))