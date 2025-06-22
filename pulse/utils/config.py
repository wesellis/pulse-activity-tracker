"""
Configuration management for Pulse Activity Tracker
Handles environment variables, settings, and configuration validation
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logging.warning("python-dotenv not available - using environment variables only")

class Config:
    """Configuration manager for Pulse application"""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration with default values"""
        
        # Load from environment file if specified
        if config_file and Path(config_file).exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(config_file)
            except ImportError:
                pass
        
        # Database configuration
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:///pulse_data.db')
        
        # Monitoring settings
        self.monitoring_interval = int(os.getenv('MONITORING_INTERVAL', '30'))
        self.work_hours_start = int(os.getenv('WORK_HOURS_START', '9'))
        self.work_hours_end = int(os.getenv('WORK_HOURS_END', '17'))
        
        # Privacy settings
        self.track_browser_history = os.getenv('TRACK_BROWSER_HISTORY', 'true').lower() == 'true'
        self.track_file_access = os.getenv('TRACK_FILE_ACCESS', 'true').lower() == 'true'
        self.track_keystrokes = os.getenv('TRACK_KEYSTROKES', 'false').lower() == 'true'
        self.track_websites = os.getenv('TRACK_WEBSITES', 'true').lower() == 'true'
        
        # AI integration
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY', '')
        self.use_ai_suggestions = os.getenv('USE_AI_SUGGESTIONS', 'false').lower() == 'true'
        
        # Reporting settings
        self.auto_generate_reports = os.getenv('AUTO_GENERATE_REPORTS', 'true').lower() == 'true'
        self.report_email = os.getenv('REPORT_EMAIL', '')
        self.send_daily_reports = os.getenv('SEND_DAILY_REPORTS', 'false').lower() == 'true'
        
        # Web dashboard
        self.web_port = int(os.getenv('WEB_PORT', '8000'))
        self.web_host = os.getenv('WEB_HOST', 'localhost')
        self.debug_mode = os.getenv('DEBUG_MODE', 'true').lower() == 'true'
        
        # Logging
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.log_file = os.getenv('LOG_FILE', 'pulse.log')
        
        # Application paths
        self.app_dir = Path(__file__).parent.parent.parent
        self.data_dir = self.app_dir / 'data'
        self.logs_dir = self.app_dir / 'logs'
        self.exports_dir = self.app_dir / 'exports'
        
        # Ensure directories exist
        self._create_directories()
        
        # Validate configuration
        self._validate_config()
    
    def _create_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [self.data_dir, self.logs_dir, self.exports_dir]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logging.warning(f"Could not create directory {directory}: {e}")
    
    def _validate_config(self):
        """Validate configuration values"""
        # Validate monitoring interval
        if self.monitoring_interval < 5:
            logging.warning("Monitoring interval too low, setting to 5 seconds")
            self.monitoring_interval = 5
        elif self.monitoring_interval > 300:
            logging.warning("Monitoring interval too high, setting to 300 seconds")
            self.monitoring_interval = 300
        
        # Validate work hours
        if not (0 <= self.work_hours_start <= 23) or not (0 <= self.work_hours_end <= 23):
            logging.warning("Invalid work hours, using defaults (9-17)")
            self.work_hours_start = 9
            self.work_hours_end = 17
        
        if self.work_hours_start >= self.work_hours_end:
            logging.warning("Work start time after end time, using defaults")
            self.work_hours_start = 9
            self.work_hours_end = 17
        
        # Validate web port
        if not (1024 <= self.web_port <= 65535):
            logging.warning("Invalid web port, using default 8000")
            self.web_port = 8000
        
        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level not in valid_log_levels:
            logging.warning(f"Invalid log level '{self.log_level}', using INFO")
            self.log_level = 'INFO'
    
    def get_database_path(self) -> str:
        """Get the full path to the database file"""
        if self.database_url.startswith('sqlite:///'):
            db_file = self.database_url.replace('sqlite:///', '')
            if not os.path.isabs(db_file):
                return str(self.data_dir / db_file)
            return db_file
        return self.database_url
    
    def get_log_path(self) -> str:
        """Get the full path to the log file"""
        if not os.path.isabs(self.log_file):
            return str(self.logs_dir / self.log_file)
        return self.log_file
    
    def is_work_hours(self) -> bool:
        """Check if current time is within configured work hours"""
        import datetime
        current_hour = datetime.datetime.now().hour
        return self.work_hours_start <= current_hour < self.work_hours_end
    
    def get_privacy_settings(self) -> Dict[str, bool]:
        """Get current privacy settings"""
        return {
            'track_browser_history': self.track_browser_history,
            'track_file_access': self.track_file_access,
            'track_keystrokes': self.track_keystrokes,
            'track_websites': self.track_websites
        }
    
    def get_ai_settings(self) -> Dict[str, Any]:
        """Get AI integration settings"""
        return {
            'use_ai_suggestions': self.use_ai_suggestions,
            'openai_available': bool(self.openai_api_key),
            'anthropic_available': bool(self.anthropic_api_key)
        }
    
    def get_reporting_settings(self) -> Dict[str, Any]:
        """Get reporting configuration"""
        return {
            'auto_generate_reports': self.auto_generate_reports,
            'send_daily_reports': self.send_daily_reports,
            'report_email_configured': bool(self.report_email)
        }
    
    def update_setting(self, key: str, value: Any) -> bool:
        """Update a configuration setting"""
        try:
            if hasattr(self, key):
                setattr(self, key, value)
                logging.info(f"Updated setting {key} to {value}")
                return True
            else:
                logging.warning(f"Unknown setting: {key}")
                return False
        except Exception as e:
            logging.error(f"Error updating setting {key}: {e}")
            return False
    
    def export_config(self) -> Dict[str, Any]:
        """Export current configuration (excluding sensitive data)"""
        config_dict = {}
        
        # Include non-sensitive settings
        safe_attributes = [
            'monitoring_interval', 'work_hours_start', 'work_hours_end',
            'track_browser_history', 'track_file_access', 'track_websites',
            'auto_generate_reports', 'web_port', 'web_host', 'debug_mode',
            'log_level'
        ]
        
        for attr in safe_attributes:
            if hasattr(self, attr):
                config_dict[attr] = getattr(self, attr)
        
        # Include derived settings
        config_dict.update({
            'privacy_settings': self.get_privacy_settings(),
            'ai_settings': self.get_ai_settings(),
            'reporting_settings': self.get_reporting_settings(),
            'database_type': 'sqlite' if 'sqlite' in self.database_url else 'postgresql'
        })
        
        return config_dict
    
    def __str__(self) -> str:
        """String representation of configuration"""
        config = self.export_config()
        return f"PulseConfig({', '.join(f'{k}={v}' for k, v in config.items())})"
    
    def __repr__(self) -> str:
        return self.__str__()

# Global configuration instance
config = Config()
