from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import APIKeyHeader
from typing import List, Dict, Any
import os
from pathlib import Path
from datetime import datetime
from app.core.config import settings

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Depends(API_KEY_HEADER)):
    if api_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return api_key

@router.get("/usage", response_model=Dict[str, Any])
async def get_usage_statistics(api_key: str = Depends(verify_api_key)):
    logs_dir = Path("logs")
    if not logs_dir.exists():
        return {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0,
            "processing_history": []
        }
    
    total_tokens = 0
    total_cost = 0
    processing_history = []
    
    for log_file in logs_dir.glob("*.log"):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                log_data = eval(f.read())
                total_tokens += log_data.get("usage", {}).get("total_tokens", 0)
                total_cost += log_data.get("usage", {}).get("cost_estimate", 0)
                processing_history.append({
                    "timestamp": log_file.stem,
                    "file_name": log_data.get("file_name", "unknown"),
                    "tokens": log_data.get("usage", {}).get("total_tokens", 0),
                    "cost": log_data.get("usage", {}).get("cost_estimate", 0)
                })
        except Exception:
            continue
    
    processing_history.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return {
        "total_requests": len(processing_history),
        "total_tokens": total_tokens,
        "total_cost": round(total_cost, 4),
        "processing_history": processing_history
    }

@router.get("/files", response_model=List[Dict[str, Any]])
async def get_processed_files(api_key: str = Depends(verify_api_key)):
    processed_dir = Path("processed_files")
    if not processed_dir.exists():
        return []
    
    files = []
    for file_path in processed_dir.glob("*_result.txt"):
        try:
            stats = file_path.stat()
            files.append({
                "file_id": file_path.stem.split("_")[0],
                "created_at": datetime.fromtimestamp(stats.st_ctime).isoformat(),
                "size": stats.st_size,
                "expires_at": datetime.fromtimestamp(stats.st_ctime + 24*60*60).isoformat()
            })
        except Exception:
            continue
    
    return sorted(files, key=lambda x: x["created_at"], reverse=True)
