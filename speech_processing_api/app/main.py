from fastapi import FastAPI, Response
import json

app = FastAPI(
    title="Speech Processing API",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

@app.get("/")
def root():
    return Response(
        content=json.dumps({"status": "ok", "message": "Speech Processing API is running"}),
        media_type="application/json"
    )

@app.get("/health")
def health():
    return Response(
        content=json.dumps({"status": "healthy"}),
        media_type="application/json"
    )
