"""
Database migration manager
Handles schema versioning and migrations
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from sqlalchemy import text

from ..connection import get_db_session, engine

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database schema migrations"""
    
    def __init__(self):
        self.migrations_dir = Path(__file__).parent
        self.version_table = 'schema_versions'
        self._ensure_version_table()
    
    def _ensure_version_table(self):
        """Create version tracking table if it doesn't exist"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS schema_versions (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP NOT NULL,
            description TEXT,
            checksum TEXT
        )
        """
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
    
    def get_current_version(self) -> int:
        """Get current schema version"""
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("SELECT MAX(version) FROM schema_versions")
                ).scalar()
                return result or 0
        except Exception as e:
            logger.error(f"Failed to get current version: {e}")
            return 0
    
    def get_applied_migrations(self) -> List[Dict]:
        """Get list of applied migrations"""
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("SELECT * FROM schema_versions ORDER BY version")
                ).fetchall()
                
                return [
                    {
                        'version': row[0],
                        'applied_at': row[1],
                        'description': row[2],
                        'checksum': row[3]
                    }
                    for row in result
                ]
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {e}")
            return []
    
    def apply_migration(self, version: int, description: str, sql: str) -> bool:
        """Apply a single migration"""
        try:
            with engine.begin() as conn:
                # Execute migration SQL
                for statement in sql.split(';'):
                    statement = statement.strip()
                    if statement:
                        conn.execute(text(statement))
                
                # Record migration
                conn.execute(
                    text("""
                        INSERT INTO schema_versions (version, applied_at, description, checksum)
                        VALUES (:version, :applied_at, :description, :checksum)
                    """),
                    {
                        'version': version,
                        'applied_at': datetime.utcnow(),
                        'description': description,
                        'checksum': str(hash(sql))
                    }
                )
            
            logger.info(f"Applied migration {version}: {description}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply migration {version}: {e}")
            return False
    
    def run_migrations(self):
        """Run all pending migrations"""
        current_version = self.get_current_version()
        logger.info(f"Current schema version: {current_version}")
        
        # Get all migration files
        migrations = self._get_migration_files()
        
        # Apply pending migrations
        applied_count = 0
        for migration in migrations:
            if migration['version'] > current_version:
                success = self.apply_migration(
                    migration['version'],
                    migration['description'],
                    migration['sql']
                )
                if success:
                    applied_count += 1
                else:
                    logger.error(f"Migration {migration['version']} failed, stopping")
                    break
        
        if applied_count > 0:
            logger.info(f"Applied {applied_count} migrations")
        else:
            logger.info("No new migrations to apply")
        
        return applied_count
    
    def _get_migration_files(self) -> List[Dict]:
        """Get all migration definitions"""
        # For now, return hardcoded migrations
        # In production, these would be read from .sql files
        return [
            {
                'version': 1,
                'description': 'Initial schema',
                'sql': """
                    -- Initial schema is created by SQLAlchemy models
                    -- This migration is just for version tracking
                    SELECT 1;
                """
            },
            {
                'version': 2,
                'description': 'Add indexes for performance',
                'sql': """
                    CREATE INDEX IF NOT EXISTS idx_activities_productivity 
                    ON activities(productivity_score, timestamp);
                    
                    CREATE INDEX IF NOT EXISTS idx_todos_due_date 
                    ON todos(due_date, status);
                    
                    CREATE INDEX IF NOT EXISTS idx_patterns_last_occurrence 
                    ON patterns(last_occurrence, is_active);
                """
            },
            {
                'version': 3,
                'description': 'Add settings table',
                'sql': """
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    INSERT OR IGNORE INTO settings (key, value) VALUES
                    ('privacy_mode', 'false'),
                    ('work_hours_start', '09:00'),
                    ('work_hours_end', '17:00'),
                    ('break_reminder_interval', '3600'),
                    ('monitoring_interval', '60');
                """
            }
        ]


def check_migrations():
    """Check for pending migrations"""
    manager = MigrationManager()
    current = manager.get_current_version()
    migrations = manager._get_migration_files()
    pending = [m for m in migrations if m['version'] > current]
    
    return {
        'current_version': current,
        'latest_version': migrations[-1]['version'] if migrations else 0,
        'pending_count': len(pending),
        'pending_migrations': pending
    }


def run_migrations():
    """Run all pending migrations"""
    manager = MigrationManager()
    return manager.run_migrations()


def get_migration_history():
    """Get migration history"""
    manager = MigrationManager()
    return manager.get_applied_migrations()