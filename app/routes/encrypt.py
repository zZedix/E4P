"""Encryption API endpoints."""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List
import aiofiles

from app.services.tasks import TaskManager
from app.services.storage import StorageManager
from app.config import settings

router = APIRouter()

# Global instances
task_manager = TaskManager(settings.max_concurrency)
storage_manager = StorageManager()


@router.post("/api/encrypt")
async def encrypt_files(
    files: List[UploadFile] = File(...),
    password: str = Form(...),
    algorithm: str = Form(default="AES-256-GCM")
):
    """
    Encrypt uploaded files.
    
    Args:
        files: List of uploaded files
        password: User password
        algorithm: Encryption algorithm (AES-256-GCM or XCHACHA20-POLY1305)
    
    Returns:
        JSON response with task ID and file list
    """
    # Validate algorithm
    if algorithm not in ["AES-256-GCM", "XCHACHA20-POLY1305"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid algorithm. Must be AES-256-GCM or XCHACHA20-POLY1305"
        )
    
    # Validate password
    if not password or len(password) < 1:
        raise HTTPException(
            status_code=400,
            detail="Password is required"
        )
    
    # Validate file count
    if not files or len(files) == 0:
        raise HTTPException(
            status_code=400,
            detail="At least one file is required"
        )
    
    if len(files) > 10:  # Reasonable limit
        raise HTTPException(
            status_code=400,
            detail="Too many files. Maximum 10 files allowed"
        )
    
    try:
        file_list = []
        
        for file in files:
            # Validate file size
            if file.size > settings.max_file_size_mb * 1024 * 1024:
                raise HTTPException(
                    status_code=413,
                    detail=f"File {file.filename} is too large. Maximum size is {settings.max_file_size_mb}MB"
                )
            
            # Save uploaded file
            try:
                content = await file.read()
                temp_path = await storage_manager.save_uploaded_file(content, file.filename)
                
                # Create encrypted file path
                encrypted_path = storage_manager.create_temp_file(
                    file.filename,
                    suffix=".e4p"
                )
                
                file_info = {
                    "original_name": file.filename,
                    "temp_path": str(temp_path),
                    "encrypted_path": str(encrypted_path),
                    "size": file.size
                }
                
                file_list.append(file_info)
            except Exception as e:
                print(f"Error processing file {file.filename}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error processing file {file.filename}: {str(e)}"
                )
        
        # Create encryption task
        task_id = await task_manager.create_task(
            files=file_list,
            password=password,
            algorithm=algorithm
        )
        
        return JSONResponse({
            "task_id": task_id,
            "files": [
                {
                    "original_name": f["original_name"],
                    "size": f["size"]
                }
                for f in file_list
            ],
            "algorithm": algorithm,
            "status": "pending"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Encryption error: {e}")
        import traceback
        traceback.print_exc()
        
        # Clean up any saved files on error
        for file_info in file_list:
            if "temp_path" in file_info:
                await storage_manager.delete_file(file_info["temp_path"])
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during encryption: {str(e)}"
        )


@router.get("/api/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get encryption task status.
    
    Args:
        task_id: Task ID
        
    Returns:
        Task status information
    """
    status = task_manager.get_task_status(task_id)
    
    if not status:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )
    
    return JSONResponse(status)


@router.delete("/api/task/{task_id}")
async def cancel_task(task_id: str):
    """
    Cancel an encryption task.
    
    Args:
        task_id: Task ID
        
    Returns:
        Success message
    """
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )
    
    if task.status.value in ["completed", "failed"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel completed or failed task"
        )
    
    # Mark task as failed
    from app.services.tasks import TaskStatus
    task.status = TaskStatus.FAILED
    task.error_message = "Task cancelled by user"
    
    # Clean up files
    await storage_manager.cleanup_task_files(task.files)
    
    return JSONResponse({"message": "Task cancelled successfully"})
