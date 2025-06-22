"""
Database backup and restore functionality
Handles automated backups and data recovery
"""

import os
import json
import shutil
import tarfile
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
import threading
import schedule

from ..connection import DB_PATH, get_db_session, engine
from .crud import ActivityCRUD, TodoCRUD, PatternCRUD, ReportCRUD, SessionSummaryCRUD
from .models import Activity, Todo, Pattern, Report, SessionSummary

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages database backups and restoration"""
    
    def __init__(self, backup_dir: Optional[str] = None):
        self.backup_dir = Path(backup_dir or os.path.expanduser('~/.pulse/backups'))
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.max_backups = int(os.getenv('PULSE_MAX_BACKUPS', '7'))
        self._scheduler_thread = None
        self._scheduler_running = False
    
    def create_backup(self, backup_name: Optional[str] = None) -> Optional[Path]:
        """Create a full database backup"""
        try:
            # Generate backup filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = backup_name or f"pulse_backup_{timestamp}"
            backup_path = self.backup_dir / f"{backup_name}.tar.gz"
            
            # Create temporary directory for backup files
            temp_dir = self.backup_dir / f"temp_{timestamp}"
            temp_dir.mkdir(exist_ok=True)
            
            try:
                # Copy database file
                db_backup = temp_dir / 'database.db'
                shutil.copy2(DB_PATH, db_backup)
                
                # Export data as JSON for portability
                self._export_data_json(temp_dir)
                
                # Create metadata file
                metadata = {
                    'backup_timestamp': datetime.now().isoformat(),
                    'backup_version': '1.0',
                    'database_stats': self._get_database_stats(),
                    'application_version': '0.1.0'  # TODO: Get from package
                }
                
                with open(temp_dir / 'metadata.json', 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                # Create compressed archive
                with tarfile.open(backup_path, 'w:gz') as tar:
                    for item in temp_dir.iterdir():
                        tar.add(item, arcname=item.name)
                
                logger.info(f"Backup created successfully: {backup_path}")
                
                # Cleanup old backups
                self._cleanup_old_backups()
                
                return backup_path
                
            finally:
                # Cleanup temporary directory
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def restore_backup(self, backup_path: Path) -> bool:
        """Restore database from backup"""
        try:
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Create temporary extraction directory
            temp_dir = self.backup_dir / f"restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            temp_dir.mkdir(exist_ok=True)
            
            try:
                # Extract backup
                with tarfile.open(backup_path, 'r:gz') as tar:
                    tar.extractall(temp_dir)
                
                # Read metadata
                metadata_path = temp_dir / 'metadata.json'
                if metadata_path.exists():
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    logger.info(f"Restoring backup from {metadata['backup_timestamp']}")
                
                # Backup current database before restore
                current_backup = self.backup_dir / f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2(DB_PATH, current_backup)
                
                # Restore database file
                db_backup = temp_dir / 'database.db'
                if db_backup.exists():
                    shutil.copy2(db_backup, DB_PATH)
                    logger.info("Database file restored")
                else:
                    # Restore from JSON if database file missing
                    logger.warning("Database file not found in backup, restoring from JSON")
                    return self._restore_from_json(temp_dir)
                
                return True
                
            finally:
                # Cleanup temporary directory
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """List available backups"""
        backups = []
        
        for backup_file in self.backup_dir.glob('pulse_backup_*.tar.gz'):
            try:
                # Extract metadata without full extraction
                with tarfile.open(backup_file, 'r:gz') as tar:
                    try:
                        metadata_info = tar.getmember('metadata.json')
                        metadata_file = tar.extractfile(metadata_info)
                        metadata = json.load(metadata_file)
                    except:
                        metadata = {}
                
                backups.append({
                    'filename': backup_file.name,
                    'path': str(backup_file),
                    'size_mb': round(backup_file.stat().st_size / 1024 / 1024, 2),
                    'created': backup_file.stat().st_mtime,
                    'metadata': metadata
                })
            except:
                continue
        
        # Sort by creation time, newest first
        backups.sort(key=lambda x: x['created'], reverse=True)
        return backups
    
    def start_scheduled_backups(self, schedule_time: str = "02:00"):
        """Start scheduled daily backups"""
        if self._scheduler_running:
            logger.warning("Backup scheduler already running")
            return
        
        # Schedule daily backup
        schedule.every().day.at(schedule_time).do(self.create_backup)
        
        def run_scheduler():
            self._scheduler_running = True
            logger.info(f"Backup scheduler started (daily at {schedule_time})")
            
            while self._scheduler_running:
                schedule.run_pending()
                threading.Event().wait(60)  # Check every minute
        
        self._scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self._scheduler_thread.start()
    
    def stop_scheduled_backups(self):
        """Stop scheduled backups"""
        self._scheduler_running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        logger.info("Backup scheduler stopped")
    
    def _export_data_json(self, export_dir: Path):
        """Export all data as JSON files"""
        try:
            with get_db_session() as db:
                # Export activities
                activities = db.query(Activity).all()
                with open(export_dir / 'activities.json', 'w') as f:
                    json.dump(
                        [a.to_dict() for a in activities],
                        f, indent=2, default=str
                    )
                
                # Export todos
                todos = db.query(Todo).all()
                with open(export_dir / 'todos.json', 'w') as f:
                    json.dump(
                        [t.to_dict() for t in todos],
                        f, indent=2, default=str
                    )
                
                # Export patterns
                patterns = db.query(Pattern).all()
                with open(export_dir / 'patterns.json', 'w') as f:
                    json.dump(
                        [p.to_dict() for p in patterns],
                        f, indent=2, default=str
                    )
                
                # Export reports
                reports = db.query(Report).all()
                with open(export_dir / 'reports.json', 'w') as f:
                    json.dump(
                        [r.to_dict() for r in reports],
                        f, indent=2, default=str
                    )
                
                # Export session summaries
                summaries = db.query(SessionSummary).all()
                with open(export_dir / 'session_summaries.json', 'w') as f:
                    json.dump(
                        [s.to_dict() for s in summaries],
                        f, indent=2, default=str
                    )
                
        except Exception as e:
            logger.error(f"Failed to export data as JSON: {e}")
    
    def _restore_from_json(self, restore_dir: Path) -> bool:
        """Restore data from JSON files"""
        try:
            # TODO: Implement JSON restoration
            # This would read JSON files and recreate database records
            logger.error("JSON restoration not yet implemented")
            return False
        except Exception as e:
            logger.error(f"Failed to restore from JSON: {e}")
            return False
    
    def _get_database_stats(self) -> Dict:
        """Get database statistics for metadata"""
        try:
            with get_db_session() as db:
                return {
                    'activities_count': db.query(Activity).count(),
                    'todos_count': db.query(Todo).count(),
                    'patterns_count': db.query(Pattern).count(),
                    'reports_count': db.query(Report).count(),
                    'sessions_count': db.query(SessionSummary).count(),
                    'database_size_mb': round(DB_PATH.stat().st_size / 1024 / 1024, 2)
                }
        except:
            return {}
    
    def _cleanup_old_backups(self):
        """Remove old backups beyond retention limit"""
        try:
            backups = list(self.backup_dir.glob('pulse_backup_*.tar.gz'))
            backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Keep only max_backups most recent
            for old_backup in backups[self.max_backups:]:
                old_backup.unlink()
                logger.info(f"Removed old backup: {old_backup.name}")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")


# Global backup manager instance
backup_manager = BackupManager()


def create_backup(name: Optional[str] = None) -> Optional[Path]:
    """Create a database backup"""
    return backup_manager.create_backup(name)


def restore_backup(backup_path: str) -> bool:
    """Restore from backup"""
    return backup_manager.restore_backup(Path(backup_path))


def list_backups() -> List[Dict]:
    """List available backups"""
    return backup_manager.list_backups()


def start_auto_backup(schedule_time: str = "02:00"):
    """Start automated daily backups"""
    backup_manager.start_scheduled_backups(schedule_time)


def stop_auto_backup():
    """Stop automated backups"""
    backup_manager.stop_scheduled_backups()