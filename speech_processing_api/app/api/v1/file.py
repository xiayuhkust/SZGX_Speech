from fastapi import APIRouter, UploadFile, HTTPException, File
from fastapi.responses import JSONResponse, FileResponse
from typing import Dict, Any
import os
import uuid
from tempfile import NamedTemporaryFile
from pathlib import Path
from datetime import datetime, timedelta
from app.services.text_processor import TextProcessor
from app.worker import celery_app

router = APIRouter(prefix="/api/v1/file", tags=["file"])

# Create directory for storing processed files
PROCESSED_FILES_DIR = Path("processed_files")
PROCESSED_FILES_DIR.mkdir(exist_ok=True)

# Store processed files metadata with creation time
PROCESSED_FILES: Dict[str, Dict[str, Any]] = {}

@celery_app.task
def cleanup_old_files():
    """Remove processed files older than 24 hours."""
    current_time = datetime.now()
    files_to_remove = []
    
    for file_id, file_data in PROCESSED_FILES.items():
        if current_time - file_data['created_at'] > timedelta(hours=24):
            try:
                Path(file_data['path']).unlink(missing_ok=True)
                files_to_remove.append(file_id)
            except Exception:
                pass
    
    for file_id in files_to_remove:
        PROCESSED_FILES.pop(file_id, None)

# Schedule cleanup task to run every hour
celery_app.conf.beat_schedule = {
    'cleanup-old-files': {
        'task': 'app.api.v1.file.cleanup_old_files',
        'schedule': timedelta(hours=1),
    },
}
PROCESSED_FILES: Dict[str, Dict[str, Any]] = {}

@router.post("/upload")
async def upload_file(file: UploadFile = File(..., description="Document to process")):
    if not file.filename or not file.filename.lower().endswith(('.txt', '.doc', '.docx')):
        raise HTTPException(status_code=400, detail="Only .txt, .doc, and .docx files are allowed")
    
    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        text_content = content.decode('utf-8')
            
            # Process text using the comprehensive pipeline asynchronously
            task = celery_app.send_task('process_text', args=[text_content])
            result = task.get(timeout=300)  # 5 minutes timeout
            
            # Generate unique ID for the processed result
            file_id = str(uuid.uuid4())
            
            # Create result file in the processed files directory
            result_path = PROCESSED_FILES_DIR / f"{file_id}_result.txt"
            with open(result_path, 'w', encoding='utf-8') as result_file:
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
            
            # Store the file metadata with creation time
            PROCESSED_FILES[file_id] = {
                'path': str(result_path),
                'filename': f"{os.path.splitext(file.filename)[0]}_analysis_result.txt",
                'created_at': datetime.now()
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
            pass  # No temporary files to clean up
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{file_id}")
async def download_file(file_id: str):
    """Download a processed file by its ID."""
    if file_id not in PROCESSED_FILES:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_data = PROCESSED_FILES[file_id]
    file_path = Path(file_data['path'])
    
    if not file_path.exists():
        PROCESSED_FILES.pop(file_id, None)
        raise HTTPException(status_code=404, detail="File has been removed")
    
    try:
        return FileResponse(
            path=str(file_path),
            filename=file_data['filename'],
            media_type='text/plain',
            headers={
                'Content-Disposition': f'attachment; filename="{file_data["filename"]}"'
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error downloading file: {str(e)}"
        )
