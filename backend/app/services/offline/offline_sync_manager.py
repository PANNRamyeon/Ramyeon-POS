import os
import json
import shutil
from datetime import datetime
from pathlib import Path
import logging
import asyncio

logger = logging.getLogger(__name__)

class FileBasedSyncManager:
    """
    REFACTORED: File-based offline sync manager (replaces MongoDB)
    """
    
    def __init__(self, storage_path=None):
        # Set storage path relative to backend folder
        if storage_path is None:
            backend_dir = Path(__file__).parent.parent.parent  # Goes up to backend folder
            self.storage_path = backend_dir / "offline_storage"
        else:
            self.storage_path = Path(storage_path)
            
        self.is_online = False
        self.create_storage_structure()
    
    def create_storage_structure(self):
        """Create the folder structure for offline data"""
        folders = ['active', 'archived', 'cache', 'logs']
        for folder in folders:
            folder_path = self.storage_path / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created folder: {folder_path}")
    
    def save_offline_transaction(self, transaction_type, data):
        """
        REFACTORED: Save transaction to timestamp-based file
        """
        try:
            # Create timestamp filename (your requirement)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
            filename = f"{transaction_type}_{timestamp}.json"
            filepath = self.storage_path / "active" / filename
            
            # Add sync metadata
            transaction_data = {
                "_metadata": {
                    "file_id": filename,
                    "created_at": datetime.now().isoformat(),
                    "type": transaction_type,
                    "sync_status": "pending",
                    "sync_attempts": 0
                },
                "data": data
            }
            
            # Save as JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(transaction_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Saved offline {transaction_type} to: {filename}")
            return {"success": True, "file_id": filename, "file_path": str(filepath)}
            
        except Exception as e:
            logger.error(f"❌ Failed to save offline transaction: {e}")
            return {"success": False, "error": str(e)}
    
    def get_pending_files(self, transaction_type=None):
        """Get all files waiting to be synced"""
        active_dir = self.storage_path / "active"
        if not active_dir.exists():
            return []
        
        all_files = list(active_dir.glob("*.json"))
        
        if transaction_type:
            return [f for f in all_files if f.name.startswith(transaction_type)]
        return all_files
    
    def read_transaction_file(self, filepath):
        """Read and parse a transaction file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Failed to read transaction file {filepath}: {e}")
            return None
    
    def archive_file(self, filepath, sync_success=True):
        """
        REFACTORED: Move file to archived folder (your requirement)
        """
        try:
            # Create dated subfolder in archived
            date_folder = datetime.now().strftime("%Y-%m-%d")
            archived_dir = self.storage_path / "archived" / date_folder
            archived_dir.mkdir(parents=True, exist_ok=True)
            
            # Move file to archived folder
            destination = archived_dir / filepath.name
            shutil.move(str(filepath), str(destination))
            
            status = "synced" if sync_success else "failed"
            logger.info(f"📦 Archived file: {filepath.name} as {status}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to archive file {filepath}: {e}")
            return False
    
    def update_file_metadata(self, filepath, updates):
        """Update metadata in a transaction file"""
        try:
            transaction_data = self.read_transaction_file(filepath)
            if not transaction_data:
                return False
            
            # Update metadata
            transaction_data["_metadata"].update(updates)
            
            # Write back to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(transaction_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update file metadata {filepath}: {e}")
            return False
    
    async def sync_pending_files(self):
        """
        REFACTORED: Sync all pending files (batch processing)
        """
        if not self.is_online:
            logger.warning("🌐 Offline - cannot sync files")
            return {"success": False, "synced_count": 0, "reason": "offline"}
        
        pending_files = self.get_pending_files()
        if not pending_files:
            return {"success": True, "synced_count": 0, "message": "No files to sync"}
        
        synced_count = 0
        failed_files = []
        
        for filepath in pending_files:
            try:
                # Read transaction data
                transaction_data = self.read_transaction_file(filepath)
                if not transaction_data:
                    failed_files.append(filepath.name)
                    continue
                
                # Try to sync (simulate API call for now)
                success = await self.sync_to_cloud(transaction_data)
                
                if success:
                    # Archive successful sync
                    self.archive_file(filepath, sync_success=True)
                    synced_count += 1
                    logger.info(f"✅ Synced: {filepath.name}")
                else:
                    # Update retry count for failed sync
                    self.update_file_metadata(filepath, {
                        "sync_attempts": transaction_data["_metadata"]["sync_attempts"] + 1,
                        "last_attempt": datetime.now().isoformat()
                    })
                    failed_files.append(filepath.name)
                    logger.warning(f"🔄 Sync failed, will retry: {filepath.name}")
                    
            except Exception as e:
                logger.error(f"❌ Error syncing file {filepath}: {e}")
                failed_files.append(filepath.name)
                continue
        
        # Send notification (your requirement)
        if synced_count > 0:
            self.send_sync_notification(synced_count, failed_files)
        
        return {
            "success": synced_count > 0 or not pending_files,
            "synced_count": synced_count,
            "failed_count": len(failed_files),
            "failed_files": failed_files
        }
    
    async def sync_to_cloud(self, transaction_data):
        """
        REFACTORED: Simulate cloud sync (will integrate with your actual endpoints)
        """
        try:
            # TODO: Replace with actual API calls to your endpoints
            transaction_type = transaction_data["_metadata"]["type"]
            data = transaction_data["data"]
            
            # Simulate API call delay
            await asyncio.sleep(0.1)
            
            # Simulate successful sync 90% of the time for testing
            import random
            return random.random() < 0.9
            
        except Exception as e:
            logger.error(f"❌ Cloud sync simulation failed: {e}")
            return False
    
    def send_sync_notification(self, synced_count, failed_files):
        """
        REFACTORED: Use your existing notification template
        """
        # TODO: Integrate with your existing notification function
        notification_data = {
            "type": "sync_completed",
            "timestamp": datetime.now().isoformat(),
            "synced_count": synced_count,
            "failed_count": len(failed_files),
            "failed_files": failed_files
        }
        
        # Log notification (replace with your actual notification function)
        log_path = self.storage_path / "logs" / f"notifications_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().isoformat()} - SYNC: {synced_count} successful, {len(failed_files)} failed\n")
        
        logger.info(f"📢 Sync notification: {synced_count} files synced, {len(failed_files)} failed")
    
    def get_sync_status(self):
        """Get overall sync status"""
        pending_files = self.get_pending_files()
        return {
            "is_online": self.is_online,
            "pending_files_count": len(pending_files),
            "pending_files": [f.name for f in pending_files],
            "storage_path": str(self.storage_path),
            "storage_exists": self.storage_path.exists()
        }

# Global instance (same as before for compatibility)
sync_manager = FileBasedSyncManager()