"""Decryption API endpoints."""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path

from app.services.storage import StorageManager
from app.services.tokens import TokenManager
from app.crypto.stream import StreamProcessor

router = APIRouter()

# Global instances
storage_manager = StorageManager()
token_manager = TokenManager()
processor = StreamProcessor()


@router.post("/api/decrypt")
async def decrypt_file(
    file: UploadFile = File(...),
    password: str = Form(...)
):
    """
    Decrypt an E4P file.
    
    Args:
        file: Uploaded E4P file
        password: User password
        
    Returns:
        JSON response with download token
    """
    # Validate password
    if not password or len(password) < 1:
        raise HTTPException(
            status_code=400,
            detail="Password is required"
        )
    
    # Validate file
    if not file.filename or not file.filename.endswith('.e4p'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only .e4p files are supported"
        )
    
    try:
        # Save uploaded file
        content = await file.read()
        temp_path = await storage_manager.save_uploaded_file(content, file.filename)
        
        # Get file info from header
        file_info = await processor.get_file_info(temp_path)
        
        if not file_info:
            await storage_manager.delete_file(temp_path)
            raise HTTPException(
                status_code=400,
                detail="Invalid E4P file format"
            )
        
        # Create decrypted file path
        original_name = file_info.original_name
        decrypted_path = storage_manager.create_temp_file(
            original_name,
            suffix="_decrypted"
        )
        
        # Decrypt the file
        success = await processor.decrypt_file(
            input_path=temp_path,
            output_path=decrypted_path,
            password=password
        )
        
        if not success:
            await storage_manager.delete_file(temp_path)
            await storage_manager.delete_file(decrypted_path)
            raise HTTPException(
                status_code=400,
                detail="Decryption failed. Please check your password."
            )
        
        # Create download token
        download_token = token_manager.create_download_token(
            file_path=str(decrypted_path),
            filename=original_name
        )
        
        # Clean up uploaded file
        await storage_manager.delete_file(temp_path)
        
        return JSONResponse({
            "download_token": download_token,
            "filename": original_name,
            "size": file_info.original_size,
            "algorithm": file_info.algorithm,
            "status": "success"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up files on error
        if 'temp_path' in locals():
            await storage_manager.delete_file(temp_path)
        if 'decrypted_path' in locals():
            await storage_manager.delete_file(decrypted_path)
        
        raise HTTPException(
            status_code=500,
            detail="Internal server error during decryption"
        )


@router.get("/api/file-info")
async def get_file_info(file: UploadFile = File(...)):
    """
    Get information about an E4P file without decryption.
    
    Args:
        file: Uploaded E4P file
        
    Returns:
        File information
    """
    if not file.filename or not file.filename.endswith('.e4p'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only .e4p files are supported"
        )
    
    try:
        # Save uploaded file temporarily
        content = await file.read()
        temp_path = await storage_manager.save_uploaded_file(content, file.filename)
        
        # Get file info
        file_info = await processor.get_file_info(temp_path)
        
        # Clean up
        await storage_manager.delete_file(temp_path)
        
        if not file_info:
            raise HTTPException(
                status_code=400,
                detail="Invalid E4P file format"
            )
        
        return JSONResponse({
            "filename": file_info.original_name,
            "size": file_info.original_size,
            "algorithm": file_info.algorithm,
            "timestamp": file_info.timestamp,
            "kdf": file_info.kdf,
            "kdf_params": file_info.kdf_params
        })
        
    except HTTPException:
        raise
    except Exception as e:
        if 'temp_path' in locals():
            await storage_manager.delete_file(temp_path)
        
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
