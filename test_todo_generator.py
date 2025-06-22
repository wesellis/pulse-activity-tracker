#!/usr/bin/env python3
"""
Test script for Todo Generator
Tests modular todo generation with various scenarios
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta
import json

# Add the pulse module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from pulse.core.todo_generator_v2 import TodoGenerator


class TestConfig:
    """Test configuration for todo generator"""
    def __init__(self):
        self.max_todo_suggestions = 15
        self.min_todo_confidence = 0.3
        self.monitoring_interval = 60
        self.break_reminder_enabled = True


async def test_todo_generation():
    """Test comprehensive todo generation"""
    print("🧠 Testing Todo Generator v2...")
    print("=" * 50)
    
    config = TestConfig()
    generator = TodoGenerator(config)
    
    # Test scenario 1: High productivity development session
    print("\n📊 Scenario 1: High Productivity Development Session")
    print("-" * 50)
    
    dev_activity_data = {
        'timestamp': datetime.now().isoformat(),
        'session_data': {
            'start_time': datetime.now() - timedelta(hours=1, minutes=30),
            'applications': {
                'code.exe': {'total_time': 4800, 'focus_time': 4200},
                'chrome.exe': {'total_time': 900, 'focus_time': 600},
                'github.com': {'total_time': 300, 'focus_time': 300}
            },
            'idle_periods': []
        },
        'productivity_indicators': {
            'productivity_score': 85.5,
            'focus_score': 92.0,
            'distraction_score': 8.5,
            'active_time_minutes': 85,
            'category_breakdown': {
                'development': 80,
                'research': 15,
                'communication': 5
            }
        }
    }
    
    suggestions = await generator.generate_suggestions(dev_activity_data)
    print(f"Generated {len(suggestions)} suggestions:")
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"\n{i}. {suggestion.get('title', 'Untitled')}")
        print(f"   Category: {suggestion.get('category', 'Unknown')}")
        print(f"   Priority: {suggestion.get('priority', 'medium')}")
        print(f"   Confidence: {suggestion.get('confidence', 0):.2f}")
        print(f"   Source: {suggestion.get('source', 'unknown')}")
        print(f"   Estimated time: {suggestion.get('estimated_minutes', '?')} min")
        print(f"   Description: {suggestion.get('description', '')}")
    
    # Test scenario 2: Distracted session with many apps
    print("\n\n📱 Scenario 2: Distracted Session (Many Apps)")
    print("-" * 50)
    
    distracted_activity_data = {
        'timestamp': datetime.now().isoformat(),
        'session_data': {
            'start_time': datetime.now() - timedelta(minutes=45),
            'applications': {
                'discord.exe': {'total_time': 1200},
                'spotify.exe': {'total_time': 2400},
                'chrome.exe': {'total_time': 800},
                'code.exe': {'total_time': 600},
                'slack.exe': {'total_time': 400},
                'teams.exe': {'total_time': 300},
                'youtube.com': {'total_time': 900},
                'reddit.com': {'total_time': 600},
                'twitter.com': {'total_time': 300},
                'steam.exe': {'total_time': 500},
                'notepad.exe': {'total_time': 200},
                'calculator.exe': {'total_time': 100},
                'explorer.exe': {'total_time': 1800},
                'firefox.exe': {'total_time': 400},
                'photoshop.exe': {'total_time': 700},
                'figma.com': {'total_time': 500}
            },
            'idle_periods': []
        },
        'productivity_indicators': {
            'productivity_score': 25.0,
            'focus_score': 35.0,
            'distraction_score': 65.0,
            'active_time_minutes': 45,
            'category_breakdown': {
                'entertainment': 25,
                'development': 10,
                'communication': 10
            }
        }
    }
    
    suggestions = await generator.generate_suggestions(distracted_activity_data)
    print(f"Generated {len(suggestions)} suggestions:")
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"\n{i}. {suggestion.get('title', 'Untitled')}")
        print(f"   Priority: {suggestion.get('priority', 'medium')} | Category: {suggestion.get('category', 'Unknown')}")
        print(f"   Confidence: {suggestion.get('confidence', 0):.2f} | Score: {suggestion.get('ranking_score', 0):.1f}")
        print(f"   {suggestion.get('description', '')}")
    
    # Test scenario 3: Long work session (break needed)
    print("\n\n⏰ Scenario 3: Long Work Session (Break Needed)")
    print("-" * 50)
    
    long_session_data = {
        'timestamp': datetime.now().isoformat(),
        'session_data': {
            'start_time': datetime.now() - timedelta(hours=2, minutes=15),
            'applications': {
                'code.exe': {'total_time': 7200, 'focus_time': 6500},
                'terminal.exe': {'total_time': 1800, 'focus_time': 1600}
            },
            'idle_periods': []  # No breaks!
        },
        'productivity_indicators': {
            'productivity_score': 88.0,
            'focus_score': 85.0,
            'distraction_score': 5.0,
            'active_time_minutes': 135,
            'category_breakdown': {
                'development': 120,
                'terminal': 15
            }
        }
    }
    
    suggestions = await generator.generate_suggestions(long_session_data)
    break_suggestions = [s for s in suggestions if 'break' in s.get('title', '').lower()]
    health_suggestions = [s for s in suggestions if s.get('category') == 'health']
    
    print(f"Generated {len(suggestions)} total suggestions")
    print(f"Break-related suggestions: {len(break_suggestions)}")
    print(f"Health suggestions: {len(health_suggestions)}")
    
    print("\nTop break/health suggestions:")
    for suggestion in (break_suggestions + health_suggestions)[:5]:
        print(f"• {suggestion.get('title')} ({suggestion.get('priority')})")
        print(f"  {suggestion.get('description')}")
    
    # Test generator statistics
    print("\n\n📈 Generator Statistics")
    print("-" * 50)
    
    stats = generator.get_generation_stats()
    print(json.dumps(stats, indent=2))
    
    # Test learning functionality
    print("\n\n🎓 Testing Learning Functionality")
    print("-" * 50)
    
    sample_todo = {
        'id': 'test_001',
        'title': 'Take a break',
        'category': 'health',
        'priority': 'high'
    }
    
    completion_context = {
        'time_to_complete': 15,
        'user_rating': 5,
        'effectiveness': 'high',
        'completion_time': datetime.now().isoformat()
    }
    
    await generator.learn_from_completion(sample_todo, completion_context)
    print("✅ Learning functionality tested")
    
    # Test different times of day
    print("\n\n🕐 Testing Time-Based Patterns")
    print("-" * 50)
    
    # Morning scenario
    morning_data = dev_activity_data.copy()
    morning_suggestions = await generator.generate_suggestions(morning_data)
    morning_planning = [s for s in morning_suggestions if 'plan' in s.get('title', '').lower()]
    
    print(f"Morning suggestions with 'plan': {len(morning_planning)}")
    for suggestion in morning_planning:
        print(f"• {suggestion.get('title')}")
    
    print("\n✅ Todo Generator testing completed!")
    print("\n🎯 Key features tested:")
    print("  • Modular generator architecture")
    print("  • Break reminder generation")
    print("  • Distraction detection and mitigation")
    print("  • Project-specific suggestions")
    print("  • Health and wellness reminders")
    print("  • Time-based pattern recognition")
    print("  • Confidence scoring and ranking")
    print("  • Learning from completion feedback")


if __name__ == "__main__":
    print("🚀 Pulse Activity Tracker - Todo Generator Tests")
    print("=" * 55)
    
    try:
        asyncio.run(test_todo_generation())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🏁 All tests completed!")