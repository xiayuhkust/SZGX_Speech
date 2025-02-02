from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.speech import router as speech_router
from app.api.v1.file import router as file_router
from app.api.v1.text import router as text_router
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Speech Processing API",
    description="Speech processing service using DeepSeek/OpenAI API",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(speech_router)
app.include_router(file_router)
app.include_router(text_router)

@app.get("/")
async def root():
    return {"status": "ok", "message": "Speech Processing API is running"}
