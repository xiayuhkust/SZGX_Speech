from fastapi import APIRouter, UploadFile, HTTPException, File
from fastapi.responses import FileResponse
from typing import Dict, Any
import os
from tempfile import NamedTemporaryFile
from app.services.text_processor import TextProcessor

router = APIRouter(prefix="/api/v1/file", tags=["file"])

@router.post("/upload")
async def upload_file(file: UploadFile = File(..., description="Text file to analyze")):
    if not file.filename or not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Only .txt files are allowed")
    
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
            
            processor = TextProcessor()
            
            # Check for biblical references
            has_biblical_refs = processor.biblical_detector.contains_references(text_content)
            biblical_refs = processor.biblical_detector.find_references(text_content) if has_biblical_refs else []
            
            # Process text
            segments_result = await processor.segment_text(text_content)
            emotion_result = await processor.emotion_analyzer.analyze(text_content)
            
            # Create result file
            result_file = NamedTemporaryFile(delete=False, suffix='_result.txt', mode='w', encoding='utf-8')
            result_file.write("Text Analysis Results\n")
            result_file.write("===================\n\n")
            
            if biblical_refs:
                result_file.write("Biblical References Found:\n")
                for ref in biblical_refs:
                    result_file.write(f"- {ref['reference']}\n")
                result_file.write("\n")
            
            result_file.write("Processed Segments:\n")
            for i, segment in enumerate(segments_result["segments"], 1):
                result_file.write(f"\nSegment {i}:\n{segment}\n")
            
            result_file.write("\nEmotion Analysis:\n")
            result_file.write(f"Score: {emotion_result['result']['score']}\n")
            result_file.write(f"Emotion: {emotion_result['result']['emotion']}\n")
            result_file.write(f"Explanation: {emotion_result['result']['explanation']}\n")
            
            result_file.write("\nProcessing Statistics:\n")
            result_file.write(f"Total Text Length: {segments_result['usage']['text_length']} characters\n")
            result_file.write(f"Number of Segments: {segments_result['usage']['segment_count']}\n")
            
            result_file.write("\nToken Usage and Costs:\n")
            result_file.write("1. Embedding (Text Segmentation):\n")
            result_file.write(f"   - Total Tokens: {segments_result['usage']['embedding']['total_tokens']}\n")
            result_file.write(f"   - Model: {segments_result['usage']['embedding']['model']}\n")
            result_file.write(f"   - Estimated Cost: ${segments_result['usage']['embedding']['cost_estimate']}\n")
            
            result_file.write("\n2. Text Improvement:\n")
            result_file.write(f"   - Total Tokens: {segments_result['usage']['improvement']['total_tokens']}\n")
            result_file.write(f"   - Model: {segments_result['usage']['improvement']['model']}\n")
            result_file.write(f"   - Estimated Cost: ${segments_result['usage']['improvement']['cost_estimate']}\n")
            
            result_file.write("\n3. Emotion Analysis:\n")
            result_file.write(f"   - Prompt Tokens: {emotion_result['usage']['prompt_tokens']}\n")
            result_file.write(f"   - Completion Tokens: {emotion_result['usage']['completion_tokens']}\n")
            result_file.write(f"   - Total Tokens: {emotion_result['usage']['total_tokens']}\n")
            result_file.write(f"   - Model: {emotion_result['usage']['model']}\n")
            result_file.write(f"   - Estimated Cost: ${emotion_result['usage']['cost_estimate']}\n")
            
            total_cost = segments_result['usage']['total_cost_estimate'] + emotion_result['usage']['cost_estimate']
            result_file.write(f"\nTotal Estimated Cost: ${total_cost}")
            
            result_file.close()
            
            # Return the result file
            return FileResponse(
                result_file.name,
                media_type='text/plain',
                filename=f"{os.path.splitext(file.filename)[0]}_analysis_result.txt"
            )
            
        finally:
            # Clean up the input temp file
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
