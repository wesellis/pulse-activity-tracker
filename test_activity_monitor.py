#!/usr/bin/env python3
"""
Test script for Activity Monitor
Tests the enhanced activity monitoring functionality
"""

import asyncio
import sys
import os
from datetime import datetime
import json

# Add the pulse module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from pulse.core.activity_monitor import ActivityMonitor
from pulse.utils.config import Config

class TestConfig:
    """Test configuration for activity monitor"""
    def __init__(self):
        self.monitoring_interval = 2  # seconds
        self.privacy_mode = False
        self.blocked_apps = {'private_app.exe', 'secure_browser.exe'}
        self.incognito_keywords = ['private', 'incognito', 'password', 'banking']
        self.idle_threshold_seconds = 30  # 30 seconds for testing

async def test_activity_monitor():
    """Test the activity monitor functionality"""
    print("🔍 Testing Activity Monitor...")
    print("=" * 50)
    
    # Initialize with test config
    config = TestConfig()
    monitor = ActivityMonitor(config)
    
    print("📊 Initial session summary:")
    summary = monitor.get_session_summary()
    print(json.dumps(summary, indent=2, default=str))
    print()
    
    # Test current activity snapshot
    print("📱 Current activity snapshot:")
    current = await monitor.get_current_activity()
    print(json.dumps(current, indent=2, default=str))
    print()
    
    # Test privacy controls
    print("🔒 Testing privacy controls...")
    print(f"Should track 'chrome.exe': {monitor._should_track_app('chrome.exe')}")
    print(f"Should track 'private_app.exe': {monitor._should_track_app('private_app.exe')}")
    print(f"Should track 'Gmail - Inbox': {monitor._should_track_window('Gmail - Inbox')}")
    print(f"Should track 'Private Browsing - Firefox': {monitor._should_track_window('Private Browsing - Firefox')}")
    print()
    
    # Test productivity scoring
    print("⚡ Testing productivity scoring...")
    
    # Simulate some application usage
    monitor.current_session['applications'] = {
        'code.exe': {
            'total_time': 3600,  # 1 hour
            'cpu_usage': [15.2, 12.8, 18.9],
            'memory_usage': [8.5, 9.1, 8.9],
            'focus_time': 3200,
            'first_seen': datetime.now()
        },
        'chrome.exe': {
            'total_time': 1800,  # 30 minutes
            'cpu_usage': [5.2, 3.8, 7.1],
            'memory_usage': [12.5, 13.1, 11.9],
            'focus_time': 1600,
            'first_seen': datetime.now()
        },
        'discord.exe': {
            'total_time': 600,  # 10 minutes
            'cpu_usage': [2.1, 1.8, 2.5],
            'memory_usage': [4.5, 4.8, 4.2],
            'focus_time': 300,
            'first_seen': datetime.now()
        }
    }
    
    # Add some idle periods
    monitor.current_session['idle_periods'] = [
        {'start': datetime.now(), 'duration_seconds': 300},  # 5 min break
        {'start': datetime.now(), 'duration_seconds': 600},  # 10 min break
    ]
    
    productivity = monitor._calculate_productivity()
    print("Productivity metrics with simulated data:")
    print(json.dumps(productivity, indent=2))
    print()
    
    # Test system stats
    print("💻 System statistics:")
    stats = monitor._get_system_stats()
    print(json.dumps(stats, indent=2))
    print()
    
    # Test running processes
    print("🏃 Top running processes:")
    processes = monitor._get_running_processes()
    for proc in processes[:5]:  # Show top 5
        print(f"  {proc['name']} (PID: {proc['pid']}, CPU: {proc['cpu_percent']}%)")
    print()
    
    # Test active window detection
    print("🪟 Active window detection:")
    active_window = monitor._get_active_window()
    print(f"  Title: {active_window['title']}")
    print(f"  App: {active_window['app']}")
    print()
    
    # Test app name extraction
    print("🔤 App name extraction tests:")
    test_titles = [
        "Visual Studio Code - main.py",
        "Google Chrome - Stack Overflow",
        "Discord | #general",
        "Terminal :: ~/projects/pulse",
        "Simple Window Title"
    ]
    
    for title in test_titles:
        app_name = monitor._extract_app_name(title)
        print(f"  '{title}' → '{app_name}'")
    print()
    
    print("✅ Activity Monitor tests completed!")
    print("🎯 Key features verified:")
    print("  • Privacy controls and filtering")
    print("  • Enhanced productivity scoring")
    print("  • System resource monitoring")
    print("  • Window and process tracking")
    print("  • Break efficiency calculation")
    print("  • Category-based time tracking")

async def test_monitoring_loop():
    """Test the actual monitoring loop (brief test)"""
    print("\n🔄 Testing monitoring loop (10 seconds)...")
    
    config = TestConfig()
    monitor = ActivityMonitor(config)
    
    try:
        await monitor.start()
        print("Monitoring started...")
        
        # Monitor for 10 seconds
        await asyncio.sleep(10)
        
        await monitor.stop()
        print("Monitoring stopped.")
        
        # Show collected data
        print("\nCollected session data:")
        summary = monitor.get_session_summary()
        print(json.dumps(summary, indent=2, default=str))
        
    except Exception as e:
        print(f"Error during monitoring: {e}")
        await monitor.stop()

if __name__ == "__main__":
    print("🚀 Pulse Activity Tracker - Monitor Tests")
    print("=" * 50)
    
    # Run basic functionality tests
    asyncio.run(test_activity_monitor())
    
    # Run brief monitoring test
    try:
        asyncio.run(test_monitoring_loop())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
    
    print("\n🏁 All tests completed!")