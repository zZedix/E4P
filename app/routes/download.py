"""Download API endpoints."""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path
import aiofiles

from app.services.tokens import TokenManager
from app.services.storage import StorageManager

router = APIRouter()

# Global instances
token_manager = TokenManager()
storage_manager = StorageManager()


@router.get("/download/{token}")
async def download_file(token: str):
    """
    Download a file using a secure token.
    
    Args:
        token: Download token
        
    Returns:
        File download response
    """
    # Validate token
    token_data = token_manager.validate_token(token)
    
    if not token_data:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired download token"
        )
    
    file_path = Path(token_data["file_path"])
    filename = token_data["filename"]
    
    # Check if file exists
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )
    
    # Return file for download
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type='application/octet-stream'
    )


@router.get("/download-stream/{token}")
async def download_file_stream(token: str):
    """
    Stream download a file using a secure token.
    
    Args:
        token: Download token
        
    Returns:
        Streaming file download response
    """
    # Validate token
    token_data = token_manager.validate_token(token)
    
    if not token_data:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired download token"
        )
    
    file_path = Path(token_data["file_path"])
    filename = token_data["filename"]
    
    # Check if file exists
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )
    
    # Stream file content
    async def file_generator():
        async with aiofiles.open(file_path, 'rb') as f:
            while True:
                chunk = await f.read(8192)  # 8KB chunks
                if not chunk:
                    break
                yield chunk
    
    return StreamingResponse(
        file_generator(),
        media_type='application/octet-stream',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )


@router.get("/api/token-info/{token}")
async def get_token_info(token: str):
    """
    Get information about a download token.
    
    Args:
        token: Download token
        
    Returns:
        Token information
    """
    token_info = token_manager.get_token_info(token)
    
    if not token_info:
        raise HTTPException(
            status_code=400,
            detail="Invalid token"
        )
    
    return {
        "filename": token_info["filename"],
        "expires": token_info["expires"],
        "timestamp": token_info["timestamp"],
        "is_expired": token_info["is_expired"]
    }
