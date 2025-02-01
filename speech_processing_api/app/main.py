from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import speech, file

app = FastAPI(
    title="Speech Processing API",
    description="Speech processing service with text analysis and biblical reference handling",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(speech.router)
app.include_router(file.router)

@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Speech Processing API is running",
        "version": "0.1.0"
    }
