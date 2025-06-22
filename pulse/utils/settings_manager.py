"""
Settings Manager - Runtime configuration management
Handles user preferences, settings persistence, and validation
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .config import Config


class SettingsManager:
    """Manages runtime settings and user preferences"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.settings_file = Path(config.data_dir) / 'user_settings.json'
        self.user_settings = {}
        
        # Load existing settings
        self.load_settings()
    
    def load_settings(self) -> bool:
        """Load user settings from file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    self.user_settings = json.load(f)
                self.logger.info(f"Loaded settings from {self.settings_file}")
                return True
            else:
                self.user_settings = self._get_default_settings()
                self.save_settings()
                return True
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
            self.user_settings = self._get_default_settings()
            return False
    
    def save_settings(self) -> bool:
        """Save current settings to file"""
        try:
            # Ensure directory exists
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Add metadata
            settings_with_meta = {
                'metadata': {
                    'last_updated': datetime.now().isoformat(),
                    'version': '1.0'
                },
                'settings': self.user_settings
            }
            
            with open(self.settings_file, 'w') as f:
                json.dump(settings_with_meta, f, indent=2)
            
            self.logger.info(f"Saved settings to {self.settings_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            return False
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default user settings"""
        return {
            'privacy': {
                'privacy_mode': False,
                'blocked_apps': [],
                'incognito_keywords': ['private', 'incognito', 'password', 'banking'],
                'track_browser_history': True,
                'track_file_access': True,
                'track_websites': True
            },
            'productivity': {
                'work_hours_start': 9,
                'work_hours_end': 17,
                'break_reminder_interval': 3600,
                'productivity_threshold_low': 30,
                'productivity_threshold_high': 80,
                'idle_threshold_seconds': 300
            },
            'notifications': {
                'enable_notifications': True,
                'break_notifications': True,
                'productivity_alerts': True,
                'desktop_notifications': True,
                'sound_enabled': False
            },
            'focus_modes': {
                'pomodoro_enabled': True,
                'pomodoro_work_minutes': 25,
                'pomodoro_break_minutes': 5,
                'deep_work_minutes': 90,
                'focus_mode_blocks_distractions': True
            },
            'health': {
                'hydration_reminders': True,
                'hydration_interval_hours': 2,
                'eye_rest_reminders': True,
                'eye_rest_interval_hours': 1,
                'posture_reminders': True,
                'posture_interval_hours': 2,
                'movement_reminders': True
            },
            'reports': {
                'auto_generate_daily': True,
                'auto_generate_weekly': True,
                'include_productivity_score': True,
                'include_category_breakdown': True,
                'include_health_metrics': True,
                'export_format': 'json'
            },
            'ui': {
                'theme': 'light',
                'compact_mode': False,
                'show_notifications_in_tray': True,
                'minimize_to_tray': True,
                'start_minimized': False
            },
            'advanced': {
                'monitoring_interval': 30,
                'data_retention_days': 90,
                'auto_backup': True,
                'backup_interval_hours': 24,
                'debug_mode': False
            }
        }
    
    def get_setting(self, category: str, key: str, default: Any = None) -> Any:
        """Get a specific setting value"""
        return self.user_settings.get(category, {}).get(key, default)
    
    def set_setting(self, category: str, key: str, value: Any) -> bool:
        """Set a specific setting value"""
        try:
            if category not in self.user_settings:
                self.user_settings[category] = {}
            
            old_value = self.user_settings[category].get(key)
            self.user_settings[category][key] = value
            
            # Validate the new setting
            if not self._validate_setting(category, key, value):
                # Revert if validation fails
                if old_value is not None:
                    self.user_settings[category][key] = old_value
                else:
                    del self.user_settings[category][key]
                return False
            
            self.save_settings()
            self.logger.info(f"Updated setting {category}.{key} = {value}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting {category}.{key}: {e}")
            return False
    
    def get_category(self, category: str) -> Dict[str, Any]:
        """Get all settings in a category"""
        return self.user_settings.get(category, {})
    
    def update_category(self, category: str, settings: Dict[str, Any]) -> bool:
        """Update multiple settings in a category"""
        try:
            if category not in self.user_settings:
                self.user_settings[category] = {}
            
            # Validate all settings first
            for key, value in settings.items():
                if not self._validate_setting(category, key, value):
                    self.logger.error(f"Invalid setting {category}.{key} = {value}")
                    return False
            
            # Apply all settings
            self.user_settings[category].update(settings)
            self.save_settings()
            self.logger.info(f"Updated {len(settings)} settings in {category}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating category {category}: {e}")
            return False
    
    def _validate_setting(self, category: str, key: str, value: Any) -> bool:
        """Validate a setting value"""
        validation_rules = {
            'productivity': {
                'work_hours_start': lambda x: 0 <= x <= 23,
                'work_hours_end': lambda x: 0 <= x <= 23,
                'break_reminder_interval': lambda x: 300 <= x <= 14400,  # 5 min to 4 hours
                'productivity_threshold_low': lambda x: 0 <= x <= 100,
                'productivity_threshold_high': lambda x: 0 <= x <= 100,
                'idle_threshold_seconds': lambda x: 60 <= x <= 3600  # 1 min to 1 hour
            },
            'focus_modes': {
                'pomodoro_work_minutes': lambda x: 5 <= x <= 120,
                'pomodoro_break_minutes': lambda x: 1 <= x <= 30,
                'deep_work_minutes': lambda x: 30 <= x <= 240
            },
            'health': {
                'hydration_interval_hours': lambda x: 0.5 <= x <= 8,
                'eye_rest_interval_hours': lambda x: 0.25 <= x <= 4,
                'posture_interval_hours': lambda x: 0.5 <= x <= 6
            },
            'advanced': {
                'monitoring_interval': lambda x: 5 <= x <= 300,
                'data_retention_days': lambda x: 1 <= x <= 365,
                'backup_interval_hours': lambda x: 1 <= x <= 168  # 1 hour to 1 week
            }
        }
        
        category_rules = validation_rules.get(category, {})
        if key in category_rules:
            try:
                return category_rules[key](value)
            except:
                return False
        
        # For boolean and string values, basic type checking
        if isinstance(value, (bool, str, int, float, list, dict)):
            return True
        
        return False
    
    def reset_category(self, category: str) -> bool:
        """Reset a category to default values"""
        try:
            defaults = self._get_default_settings()
            if category in defaults:
                self.user_settings[category] = defaults[category].copy()
                self.save_settings()
                self.logger.info(f"Reset category {category} to defaults")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error resetting category {category}: {e}")
            return False
    
    def reset_all_settings(self) -> bool:
        """Reset all settings to defaults"""
        try:
            self.user_settings = self._get_default_settings()
            self.save_settings()
            self.logger.info("Reset all settings to defaults")
            return True
        except Exception as e:
            self.logger.error(f"Error resetting all settings: {e}")
            return False
    
    def export_settings(self, file_path: Optional[str] = None) -> str:
        """Export settings to a file"""
        try:
            if file_path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_path = str(self.config.exports_dir / f'settings_backup_{timestamp}.json')
            
            export_data = {
                'export_info': {
                    'timestamp': datetime.now().isoformat(),
                    'version': '1.0',
                    'app_version': '0.1.0'
                },
                'settings': self.user_settings
            }
            
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.logger.info(f"Exported settings to {file_path}")
            return file_path
        except Exception as e:
            self.logger.error(f"Error exporting settings: {e}")
            return ""
    
    def import_settings(self, file_path: str) -> bool:
        """Import settings from a file"""
        try:
            with open(file_path, 'r') as f:
                import_data = json.load(f)
            
            # Validate structure
            if 'settings' not in import_data:
                self.logger.error("Invalid settings file format")
                return False
            
            imported_settings = import_data['settings']
            
            # Validate and apply settings
            for category, settings in imported_settings.items():
                if isinstance(settings, dict):
                    for key, value in settings.items():
                        if not self._validate_setting(category, key, value):
                            self.logger.warning(f"Skipping invalid setting {category}.{key}")
                            continue
            
            self.user_settings = imported_settings
            self.save_settings()
            self.logger.info(f"Imported settings from {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error importing settings: {e}")
            return False
    
    def get_settings_summary(self) -> Dict[str, Any]:
        """Get a summary of current settings"""
        return {
            'categories': list(self.user_settings.keys()),
            'total_settings': sum(len(cat) for cat in self.user_settings.values()),
            'privacy_mode': self.get_setting('privacy', 'privacy_mode', False),
            'notifications_enabled': self.get_setting('notifications', 'enable_notifications', True),
            'work_hours': f"{self.get_setting('productivity', 'work_hours_start', 9)}:00-{self.get_setting('productivity', 'work_hours_end', 17)}:00",
            'last_updated': datetime.now().isoformat()
        }