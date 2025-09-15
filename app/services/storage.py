"""File storage and cleanup management."""

import asyncio
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
import aiofiles

from app.config import settings


class StorageManager:
    """Manages temporary file storage and cleanup."""
    
    def __init__(self):
        self.temp_dir = Path(settings.temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start the periodic cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """Periodic cleanup loop."""
        while True:
            try:
                await self.cleanup_old_files()
                await asyncio.sleep(settings.clean_interval_min * 60)
            except Exception as e:
                print(f"Cleanup error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def cleanup_old_files(self):
        """Remove files older than the TTL."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=settings.file_ttl_min)
        
        for file_path in self.temp_dir.rglob("*"):
            if file_path.is_file():
                try:
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_mtime < cutoff_time:
                        file_path.unlink()
                        print(f"Cleaned up old file: {file_path}")
                except Exception as e:
                    print(f"Error cleaning up {file_path}: {e}")
    
    def create_temp_file(self, filename: str, suffix: str = "") -> Path:
        """
        Create a temporary file path.
        
        Args:
            filename: Original filename
            suffix: Optional suffix to add
            
        Returns:
            Path to temporary file
        """
        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)
        if suffix:
            name, ext = os.path.splitext(safe_filename)
            safe_filename = f"{name}{suffix}{ext}"
        
        # Ensure unique filename
        counter = 1
        base_path = self.temp_dir / safe_filename
        while base_path.exists():
            name, ext = os.path.splitext(safe_filename)
            safe_filename = f"{name}_{counter}{ext}"
            base_path = self.temp_dir / safe_filename
            counter += 1
        
        return base_path
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove or replace dangerous characters
        dangerous_chars = '<>:"/\\|?*'
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        # Ensure filename is not empty
        if not filename or filename == '.' or filename == '..':
            filename = 'unnamed_file'
        
        return filename
    
    async def save_uploaded_file(self, file_content: bytes, filename: str) -> Path:
        """
        Save uploaded file to temporary storage.
        
        Args:
            file_content: File content bytes
            filename: Original filename
            
        Returns:
            Path to saved file
        """
        temp_path = self.create_temp_file(filename)
        
        async with aiofiles.open(temp_path, 'wb') as f:
            await f.write(file_content)
        
        return temp_path
    
    async def copy_file(self, source: Path, dest: Path) -> None:
        """Copy file asynchronously."""
        def _copy():
            shutil.copy2(source, dest)
        
        await asyncio.get_event_loop().run_in_executor(None, _copy)
    
    async def move_file(self, source: Path, dest: Path) -> None:
        """Move file asynchronously."""
        def _move():
            shutil.move(str(source), str(dest))
        
        await asyncio.get_event_loop().run_in_executor(None, _move)
    
    async def delete_file(self, file_path: Path) -> None:
        """Delete file asynchronously."""
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
    
    def get_file_size(self, file_path: Path) -> int:
        """Get file size in bytes."""
        try:
            return file_path.stat().st_size
        except Exception:
            return 0
    
    def get_file_info(self, file_path: Path) -> Optional[dict]:
        """Get file information."""
        try:
            stat = file_path.stat()
            return {
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
        except Exception:
            return None
    
    async def cleanup_task_files(self, task_files: List[dict]):
        """Clean up files associated with a task."""
        for file_info in task_files:
            for path_key in ["temp_path", "encrypted_path"]:
                if path_key in file_info:
                    await self.delete_file(Path(file_info[path_key]))
    
    async def shutdown(self):
        """Shutdown the storage manager."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
