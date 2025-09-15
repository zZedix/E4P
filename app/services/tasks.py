"""Task management for encryption jobs."""

import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

from app.crypto.stream import StreamProcessor


class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class EncryptionTask:
    """Encryption task data structure."""
    
    task_id: str
    status: TaskStatus
    files: list[Dict[str, Any]]
    password: str
    algorithm: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: float = 0.0


class TaskManager:
    """Manages encryption tasks and processing queue."""
    
    def __init__(self, max_concurrency: int = 2):
        self.max_concurrency = max_concurrency
        self.tasks: Dict[str, EncryptionTask] = {}
        self.queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.processor = StreamProcessor()
        self._worker_task: Optional[asyncio.Task] = None
        self._start_worker()
    
    def _start_worker(self):
        """Start the background worker task."""
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._worker())
    
    async def _worker(self):
        """Background worker that processes tasks from the queue."""
        while True:
            try:
                task_id = await self.queue.get()
                await self._process_task(task_id)
                self.queue.task_done()
            except Exception as e:
                print(f"Worker error: {e}")
                await asyncio.sleep(1)
    
    async def _process_task(self, task_id: str):
        """Process a single encryption task."""
        async with self.semaphore:
            task = self.tasks.get(task_id)
            if not task:
                return
            
            try:
                task.status = TaskStatus.PROCESSING
                task.progress = 0.0
                
                total_files = len(task.files)
                processed_files = 0
                
                for file_info in task.files:
                    input_path = Path(file_info["temp_path"])
                    output_path = Path(file_info["encrypted_path"])
                    
                    # Encrypt the file
                    header = await self.processor.encrypt_file(
                        input_path=input_path,
                        output_path=output_path,
                        password=task.password,
                        algorithm=task.algorithm
                    )
                    
                    # Update file info with header data
                    file_info["header"] = header.to_dict()
                    file_info["size"] = output_path.stat().st_size
                    
                    # Generate download token for the encrypted file
                    from app.services.tokens import TokenManager
                    token_manager = TokenManager()
                    download_token = token_manager.create_download_token(
                        file_path=str(output_path),
                        filename=file_info["original_name"] + ".e4p"
                    )
                    file_info["download_token"] = download_token
                    
                    processed_files += 1
                    task.progress = (processed_files / total_files) * 100
                
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                task.completed_at = datetime.utcnow()
    
    async def create_task(
        self,
        files: list[Dict[str, Any]],
        password: str,
        algorithm: str = "AES-256-GCM"
    ) -> str:
        """
        Create a new encryption task.
        
        Args:
            files: List of file information dictionaries
            password: User password
            algorithm: Encryption algorithm
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        
        task = EncryptionTask(
            task_id=task_id,
            status=TaskStatus.PENDING,
            files=files,
            password=password,
            algorithm=algorithm
        )
        
        self.tasks[task_id] = task
        await self.queue.put(task_id)
        
        return task_id
    
    def get_task(self, task_id: str) -> Optional[EncryptionTask]:
        """Get task by ID."""
        return self.tasks.get(task_id)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status information."""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return {
            "task_id": task.task_id,
            "status": task.status.value,
            "progress": task.progress,
            "files": task.files,
            "created_at": task.created_at.isoformat(),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error_message": task.error_message
        }
    
    async def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up old completed tasks."""
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        
        tasks_to_remove = []
        for task_id, task in self.tasks.items():
            if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED] and
                task.created_at.timestamp() < cutoff_time):
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
    
    async def shutdown(self):
        """Shutdown the task manager."""
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
