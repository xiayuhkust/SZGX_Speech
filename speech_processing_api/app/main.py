from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "ok", "message": "Speech Processing API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
