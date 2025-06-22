#!/usr/bin/env python3
"""
Test script for Configuration System
Tests environment variables, settings management, and validation
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# Add the pulse module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from pulse.utils.config import Config
from pulse.utils.settings_manager import SettingsManager


def test_basic_config():
    """Test basic configuration loading"""
    print("🔧 Testing Basic Configuration...")
    print("-" * 40)
    
    # Test default configuration
    config = Config()
    
    print(f"✅ Database URL: {config.database_url}")
    print(f"✅ Monitoring interval: {config.monitoring_interval} seconds")
    print(f"✅ Work hours: {config.work_hours_start}:00 - {config.work_hours_end}:00")
    print(f"✅ Privacy mode: {config.privacy_mode}")
    print(f"✅ Web port: {config.web_port}")
    print(f"✅ Log level: {config.log_level}")
    
    # Test privacy settings
    privacy = config.get_privacy_settings()
    print(f"\nPrivacy settings: {json.dumps(privacy, indent=2)}")
    
    # Test AI settings
    ai_settings = config.get_ai_settings()
    print(f"\nAI settings: {json.dumps(ai_settings, indent=2)}")
    
    # Test productivity settings
    productivity = config.get_productivity_settings()
    print(f"\nProductivity settings: {json.dumps(productivity, indent=2)}")
    
    print()


def test_environment_variables():
    """Test configuration with environment variables"""
    print("🌍 Testing Environment Variables...")
    print("-" * 40)
    
    # Set some test environment variables
    test_env = {
        'MONITORING_INTERVAL': '45',
        'WORK_HOURS_START': '8',
        'WORK_HOURS_END': '18',
        'PRIVACY_MODE': 'true',
        'POMODORO_WORK_MINUTES': '30',
        'BREAK_REMINDER_INTERVAL': '2700'
    }
    
    # Temporarily set environment variables
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    try:
        # Create config with environment variables
        config = Config()
        
        print(f"✅ Monitoring interval: {config.monitoring_interval} (should be 45)")
        print(f"✅ Work hours: {config.work_hours_start}-{config.work_hours_end} (should be 8-18)")
        print(f"✅ Privacy mode: {config.privacy_mode} (should be True)")
        print(f"✅ Pomodoro work: {config.pomodoro_work_minutes} min (should be 30)")
        print(f"✅ Break reminder: {config.break_reminder_interval} sec (should be 2700)")
        
        # Test validation
        assert config.monitoring_interval == 45
        assert config.work_hours_start == 8
        assert config.work_hours_end == 18
        assert config.privacy_mode == True
        assert config.pomodoro_work_minutes == 30
        
        print("✅ All environment variable tests passed!")
        
    finally:
        # Restore original environment
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    
    print()


def test_settings_manager():
    """Test the settings manager functionality"""
    print("⚙️ Testing Settings Manager...")
    print("-" * 40)
    
    # Create temporary directory for settings
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create config with temp data directory
        config = Config()
        config.data_dir = Path(temp_dir)
        
        # Initialize settings manager
        settings_manager = SettingsManager(config)
        
        # Test default settings
        summary = settings_manager.get_settings_summary()
        print(f"✅ Default settings loaded: {summary['total_settings']} settings in {len(summary['categories'])} categories")
        
        # Test individual setting access
        privacy_mode = settings_manager.get_setting('privacy', 'privacy_mode', False)
        print(f"✅ Privacy mode (default): {privacy_mode}")
        
        # Test setting update
        success = settings_manager.set_setting('privacy', 'privacy_mode', True)
        assert success, "Failed to update privacy mode"
        
        updated_privacy = settings_manager.get_setting('privacy', 'privacy_mode', False)
        print(f"✅ Privacy mode (updated): {updated_privacy}")
        assert updated_privacy == True
        
        # Test category update
        productivity_settings = {
            'work_hours_start': 8,
            'work_hours_end': 19,
            'break_reminder_interval': 2700
        }
        
        success = settings_manager.update_category('productivity', productivity_settings)
        assert success, "Failed to update productivity category"
        
        # Verify updates
        work_start = settings_manager.get_setting('productivity', 'work_hours_start')
        print(f"✅ Work hours start (updated): {work_start} (should be 8)")
        assert work_start == 8
        
        # Test validation (should fail)
        invalid_update = settings_manager.set_setting('productivity', 'work_hours_start', 25)  # Invalid hour
        print(f"✅ Invalid setting rejected: {not invalid_update}")
        assert not invalid_update
        
        # Test settings export
        export_path = settings_manager.export_settings()
        print(f"✅ Settings exported to: {export_path}")
        assert os.path.exists(export_path)
        
        # Test settings import
        # Create a new settings manager and import
        settings_manager2 = SettingsManager(config)
        settings_manager2.reset_all_settings()  # Reset to defaults
        
        import_success = settings_manager2.import_settings(export_path)
        assert import_success, "Failed to import settings"
        
        # Verify import worked
        imported_privacy = settings_manager2.get_setting('privacy', 'privacy_mode', False)
        print(f"✅ Imported privacy mode: {imported_privacy} (should match updated value)")
        assert imported_privacy == True
        
        print("✅ Settings manager tests passed!")
    
    print()


def test_configuration_integration():
    """Test integration between config and settings manager"""
    print("🔗 Testing Configuration Integration...")
    print("-" * 40)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config = Config()
        config.data_dir = Path(temp_dir)
        
        settings_manager = SettingsManager(config)
        
        # Test work hours detection
        print(f"✅ Current time is work hours: {config.is_work_hours()}")
        
        # Test notification checking
        should_notify_break = config.should_notify('break')
        should_notify_productivity = config.should_notify('productivity')
        
        print(f"✅ Should notify breaks: {should_notify_break}")
        print(f"✅ Should notify productivity: {should_notify_productivity}")
        
        # Test all category getters
        categories = [
            ('Privacy', config.get_privacy_settings()),
            ('AI', config.get_ai_settings()),
            ('Reporting', config.get_reporting_settings()),
            ('Productivity', config.get_productivity_settings()),
            ('Notifications', config.get_notification_settings()),
            ('Health', config.get_health_settings()),
            ('Backup', config.get_backup_settings())
        ]
        
        for category_name, category_data in categories:
            print(f"✅ {category_name} settings: {len(category_data)} items")
        
        # Test configuration export
        config_export = config.export_config()
        print(f"✅ Configuration exported: {len(config_export)} items")
        
        print("✅ Configuration integration tests passed!")
    
    print()


def test_edge_cases():
    """Test edge cases and error handling"""
    print("🔍 Testing Edge Cases...")
    print("-" * 40)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config = Config()
        config.data_dir = Path(temp_dir)
        
        settings_manager = SettingsManager(config)
        
        # Test invalid settings
        test_cases = [
            ('productivity', 'work_hours_start', 25),  # Invalid hour
            ('productivity', 'break_reminder_interval', 60),  # Too short
            ('focus_modes', 'pomodoro_work_minutes', 300),  # Too long
            ('health', 'hydration_interval_hours', 0.1),  # Too short
        ]
        
        for category, key, invalid_value in test_cases:
            success = settings_manager.set_setting(category, key, invalid_value)
            print(f"✅ Rejected invalid {category}.{key}={invalid_value}: {not success}")
            assert not success
        
        # Test non-existent category/key
        unknown_setting = settings_manager.get_setting('unknown_category', 'unknown_key', 'default')
        print(f"✅ Unknown setting returns default: {unknown_setting == 'default'}")
        assert unknown_setting == 'default'
        
        # Test reset functionality
        original_privacy = settings_manager.get_setting('privacy', 'privacy_mode')
        settings_manager.set_setting('privacy', 'privacy_mode', not original_privacy)
        
        reset_success = settings_manager.reset_category('privacy')
        assert reset_success
        
        reset_privacy = settings_manager.get_setting('privacy', 'privacy_mode')
        print(f"✅ Category reset worked: {reset_privacy == original_privacy}")
        
        print("✅ Edge case tests passed!")
    
    print()


if __name__ == "__main__":
    print("🚀 Pulse Activity Tracker - Configuration Tests")
    print("=" * 55)
    
    try:
        test_basic_config()
        test_environment_variables()
        test_settings_manager()
        test_configuration_integration()
        test_edge_cases()
        
        print("✅ All configuration tests completed successfully!")
        print("\n🎯 Key features tested:")
        print("  • Environment variable loading and validation")
        print("  • Comprehensive settings management")
        print("  • Privacy, productivity, and health configurations")
        print("  • Settings persistence and import/export")
        print("  • Input validation and error handling")
        print("  • Integration between config and settings")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🏁 Configuration tests completed!")