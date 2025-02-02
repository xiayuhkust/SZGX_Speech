from fastapi import APIRouter, UploadFile, HTTPException, File
from fastapi.responses import JSONResponse
from typing import Dict, Any
import os
import uuid
from tempfile import NamedTemporaryFile
from app.services.text_processor import TextProcessor
from app.worker import celery_app

router = APIRouter(prefix="/api/v1/file", tags=["file"])

# Store processed files in memory
PROCESSED_FILES: Dict[str, Dict[str, Any]] = {}

@router.post("/upload")
async def upload_file(file: UploadFile = File(..., description="Document to process")):
    if not file.filename or not file.filename.lower().endswith(('.txt', '.doc', '.docx')):
        raise HTTPException(status_code=400, detail="Only .txt, .doc, and .docx files are allowed")
    
    try:
        # Create a temporary file to store the uploaded content
        with NamedTemporaryFile(delete=False, suffix='.txt', mode='wb') as temp_file:
            content = await file.read()
            if len(content) == 0:
                raise HTTPException(status_code=400, detail="Empty file uploaded")
            temp_file.write(content)
            temp_file.flush()
        
        try:
            # Process the text content
            with open(temp_file.name, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            # Process text using the comprehensive pipeline asynchronously
            task = celery_app.send_task('process_text', args=[text_content])
            result = task.get(timeout=300)  # 5 minutes timeout
            
            # Create result file
            result_file = NamedTemporaryFile(delete=False, suffix='_result.txt', mode='w', encoding='utf-8')
            result_file.write("Text Analysis Results\n")
            result_file.write("===================\n\n")
            
            result_file.write("Processed Segments:\n")
            for i, segment in enumerate(result["segments"], 1):
                result_file.write(f"\nSegment {i}:\n")
                result_file.write(f"Text: {segment['text']}\n")
                result_file.write(f"Emotion: {segment['emotion']['emotion']} (Score: {segment['emotion']['score']})\n")
                if segment['changes']:
                    result_file.write("Changes Made:\n")
                    for change in segment['changes']:
                        result_file.write(f"- {change}\n")
                if segment['biblical_references']:
                    result_file.write("Biblical References:\n")
                    for ref in segment['biblical_references']:
                        result_file.write(f"- {ref}\n")
            
            result_file.write("\nProcessing Statistics:\n")
            result_file.write(f"Total Text Length: {result['usage']['text_length']} characters\n")
            result_file.write(f"Number of Segments: {result['usage']['segment_count']}\n")
            result_file.write(f"Total Tokens Used: {result['usage']['total_tokens']}\n")
            result_file.write(f"Model Used: {result['usage']['model']}\n")
            result_file.write(f"Estimated Cost: ${result['usage']['cost_estimate']}\n")
            
            total_cost = result['usage']['cost_estimate']
            result_file.write(f"\nTotal Estimated Cost: ${total_cost}")
            
            result_file.close()
            
            # Generate unique ID for the processed result
            file_id = str(uuid.uuid4())
            
            # Read the result file content
            result_file.seek(0)
            result_content = result_file.read()
            
            # Store the result in memory
            PROCESSED_FILES[file_id] = {
                'content': result_content,
                'filename': f"{os.path.splitext(file.filename)[0]}_analysis_result.txt"
            }
            
            return JSONResponse({
                'file_id': file_id,
                'download_url': f'/api/v1/file/download/{file_id}',
                'token_usage': {
                    'total_tokens': result['usage']['total_tokens'],
                    'cost_estimate': total_cost
                }
            })
            
        finally:
            # Clean up temporary files
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            if os.path.exists(result_file.name):
                os.unlink(result_file.name)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{file_id}")
async def download_file(file_id: str):
    if file_id not in PROCESSED_FILES:
        raise HTTPException(status_code=404, detail="File not found")
    
    return JSONResponse({
        'content': PROCESSED_FILES[file_id]['content'],
        'filename': PROCESSED_FILES[file_id]['filename']
    })
