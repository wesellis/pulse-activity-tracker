#!/usr/bin/env python3
"""
Test script for Compensation Engine
Tests time debt calculation, energy analysis, and smart scheduling
"""

import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add the pulse module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from pulse.utils.config import Config
from pulse.core.compensation_engine import (
    CompensationEngine, EnergyProfileAnalyzer, TimeDebtCalculator, SmartScheduler,
    TaskPriority, EnergyLevel, SchedulePreference, CompensationTask, TimeSlot
)


def generate_mock_activity_data() -> list:
    """Generate mock activity data with varying productivity patterns"""
    mock_data = []
    current_time = datetime.now()
    
    # Generate 14 days of data with some inconsistency
    for day in range(14):
        day_start = current_time - timedelta(days=day)
        
        # Simulate inconsistent work patterns
        if day % 7 in [0, 6]:  # Weekend - less work
            work_hours = 2
            start_hour = 10
        elif day % 5 == 0:  # Every 5th day - low productivity
            work_hours = 4
            start_hour = 10
        else:  # Regular work days
            work_hours = 6
            start_hour = 9
        
        for hour_offset in range(work_hours):
            hour = start_hour + hour_offset
            timestamp = day_start.replace(hour=hour, minute=0, second=0)
            
            # Simulate productivity patterns
            if hour <= 11:
                base_productivity = 85
            elif hour <= 14:
                base_productivity = 65
            else:
                base_productivity = 75
            
            # Add some variance and day-specific factors
            variance = (day * hour) % 30 - 15
            productivity = max(30, min(100, base_productivity + variance))
            
            mock_data.append({
                'timestamp': timestamp.isoformat(),
                'app_name': 'code.exe',
                'productivity_score': productivity,
                'focus_score': productivity * 0.9,
                'duration': 3600,  # 1 hour
                'idle_time': 0
            })
    
    return mock_data


def test_energy_profile_analyzer():
    """Test energy pattern analysis"""
    print("⚡ Testing Energy Profile Analyzer...")
    print("-" * 40)
    
    config = Config()
    analyzer = EnergyProfileAnalyzer(config)
    
    # Test with mock data
    activity_data = generate_mock_activity_data()
    energy_profile = analyzer.analyze_energy_patterns(activity_data)
    
    print(f"✅ Energy profile analysis: {len(energy_profile)} sections")
    
    # Check hourly energy levels
    hourly_energy = energy_profile.get('hourly_energy_levels', {})
    print(f"   Hourly patterns: {len(hourly_energy)} hours tracked")
    
    # Show peak hours
    peak_hours = energy_profile.get('peak_hours', [])
    if peak_hours:
        print(f"   Peak energy hours: {min(peak_hours)}-{max(peak_hours)}:00")
    
    # Show energy type
    energy_type = energy_profile.get('energy_type', 'unknown')
    print(f"   Energy type: {energy_type}")
    
    # Show weekly rhythm
    weekly_rhythm = energy_profile.get('weekly_rhythm', 'unknown')
    print(f"   Weekly rhythm: {weekly_rhythm}")
    
    # Test default pattern for new users
    default_profile = analyzer.analyze_energy_patterns([])
    print(f"✅ Default profile for new users: {len(default_profile)} sections")
    
    print()


def test_time_debt_calculator():
    """Test time debt calculation"""
    print("📊 Testing Time Debt Calculator...")
    print("-" * 40)
    
    config = Config()
    calculator = TimeDebtCalculator(config)
    
    # Test with mock data
    activity_data = generate_mock_activity_data()
    time_debt = calculator.calculate_current_debt(activity_data, period_days=14)
    
    print(f"✅ Time debt calculation completed")
    print(f"   Weekly target: {time_debt.weekly_target} hours")
    print(f"   Daily target: {time_debt.daily_target:.1f} hours")
    print(f"   Deficit hours: {time_debt.deficit_hours:.1f}")
    print(f"   Surplus hours: {time_debt.surplus_hours:.1f}")
    print(f"   Net balance: {time_debt.net_balance:.1f}")
    
    # Test future projections
    projections = calculator.project_future_debt(time_debt, 30)
    print(f"\n📈 Future projections: {len(projections)} periods")
    for period, debt in projections.items():
        print(f"   {period}: {debt:.1f} hours deficit")
    
    # Test makeup schedules
    for preference in [SchedulePreference.IMMEDIATE, SchedulePreference.DISTRIBUTED, SchedulePreference.DELAYED]:
        makeup_schedule = calculator.calculate_makeup_schedule(time_debt, preference)
        print(f"\n📅 {preference.value} schedule: {len(makeup_schedule)} sessions")
        if makeup_schedule:
            total_hours = sum(session['hours'] for session in makeup_schedule)
            print(f"   Total makeup hours: {total_hours:.1f}")
    
    # Test empty data
    empty_debt = calculator.calculate_current_debt([])
    print(f"\n✅ Empty data handling: {empty_debt.net_balance} balance")
    
    print()


def test_smart_scheduler():
    """Test smart scheduling functionality"""
    print("🗓️ Testing Smart Scheduler...")
    print("-" * 40)
    
    config = Config()
    scheduler = SmartScheduler(config)
    
    # Create test tasks
    test_tasks = [
        CompensationTask(
            id="task_1",
            title="Code Review",
            estimated_duration=2.0,
            priority=TaskPriority.HIGH,
            required_energy=EnergyLevel.HIGH,
            deadline=datetime.now() + timedelta(days=2),
            context="work",
            flexibility=0.3,
            compensation_for="time_debt"
        ),
        CompensationTask(
            id="task_2",
            title="Documentation",
            estimated_duration=1.5,
            priority=TaskPriority.MEDIUM,
            required_energy=EnergyLevel.MEDIUM,
            deadline=datetime.now() + timedelta(days=5),
            context="work",
            flexibility=0.7,
            compensation_for=None
        ),
        CompensationTask(
            id="task_3",
            title="Planning Meeting",
            estimated_duration=1.0,
            priority=TaskPriority.URGENT,
            required_energy=EnergyLevel.HIGH,
            deadline=datetime.now() + timedelta(days=1),
            context="work",
            flexibility=0.1,
            compensation_for=None
        )
    ]
    
    # Create test time slots
    test_slots = [
        TimeSlot(
            start_time=datetime.now() + timedelta(hours=2),
            end_time=datetime.now() + timedelta(hours=6),
            available_energy=EnergyLevel.HIGH,
            context_type="work",
            duration_hours=4.0,
            quality_score=0.9
        ),
        TimeSlot(
            start_time=datetime.now() + timedelta(days=1, hours=2),
            end_time=datetime.now() + timedelta(days=1, hours=5),
            available_energy=EnergyLevel.MEDIUM,
            context_type="work",
            duration_hours=3.0,
            quality_score=0.8
        ),
        TimeSlot(
            start_time=datetime.now() + timedelta(days=1, hours=19),
            end_time=datetime.now() + timedelta(days=1, hours=21),
            available_energy=EnergyLevel.LOW,
            context_type="personal",
            duration_hours=2.0,
            quality_score=0.6
        )
    ]
    
    # Test scheduling
    energy_profile = {'energy_type': 'morning', 'peak_hours': [9, 10, 11]}
    user_preferences = {'work_hours_start': 9, 'work_hours_end': 17}
    
    schedule = scheduler.generate_optimal_schedule(
        test_tasks, test_slots, energy_profile, user_preferences
    )
    
    print(f"✅ Schedule generation completed")
    print(f"   Scheduled tasks: {len(schedule['scheduled_tasks'])}")
    print(f"   Unscheduled tasks: {len(schedule['unscheduled_tasks'])}")
    print(f"   Total scheduled hours: {schedule['total_scheduled_hours']:.1f}")
    print(f"   Schedule efficiency: {schedule['schedule_efficiency']:.1%}")
    
    # Show scheduled tasks
    for task_id, task_info in schedule['scheduled_tasks'].items():
        task = task_info['task']
        start_time = task_info['start_time']
        print(f"   📝 {task.title}: {start_time.strftime('%Y-%m-%d %H:%M')} ({task.estimated_duration}h)")
    
    # Show recommendations
    recommendations = schedule.get('recommendations', [])
    print(f"\n💡 Scheduling recommendations: {len(recommendations)}")
    for rec in recommendations:
        print(f"   • {rec}")
    
    print()


def test_compensation_engine():
    """Test comprehensive compensation engine"""
    print("🎯 Testing Compensation Engine...")
    print("-" * 40)
    
    config = Config()
    engine = CompensationEngine(config)
    
    # Generate test data
    activity_data = generate_mock_activity_data()
    
    # Create user tasks
    user_tasks = [
        CompensationTask(
            id="user_task_1",
            title="Project Review",
            estimated_duration=2.0,
            priority=TaskPriority.HIGH,
            required_energy=EnergyLevel.HIGH,
            deadline=datetime.now() + timedelta(days=3),
            context="work",
            flexibility=0.5,
            compensation_for=None
        )
    ]
    
    user_preferences = {
        'work_hours_start': 9,
        'work_hours_end': 17,
        'max_daily_makeup': 2.0,
        'preferred_schedule': 'distributed'
    }
    
    # Perform comprehensive analysis
    result = engine.analyze_and_compensate(activity_data, user_tasks, user_preferences)
    
    print(f"✅ Comprehensive analysis completed")
    print(f"   Analysis sections: {len(result)}")
    
    # Show energy profile summary
    energy_profile = result.get('energy_profile', {})
    print(f"   Energy type: {energy_profile.get('energy_type', 'unknown')}")
    
    # Show time debt
    time_debt = result.get('time_debt', {})
    print(f"   Time deficit: {time_debt.get('deficit_hours', 0):.1f} hours")
    print(f"   Time surplus: {time_debt.get('surplus_hours', 0):.1f} hours")
    
    # Show compensation tasks
    compensation_tasks = result.get('compensation_tasks', [])
    print(f"   Compensation tasks created: {len(compensation_tasks)}")
    
    # Show schedule
    schedule = result.get('schedule', {})
    scheduled_count = len(schedule.get('scheduled_tasks', {}))
    unscheduled_count = len(schedule.get('unscheduled_tasks', []))
    print(f"   Tasks scheduled: {scheduled_count}")
    print(f"   Tasks unscheduled: {unscheduled_count}")
    
    # Show insights
    insights = result.get('insights', [])
    print(f"\n💡 Generated insights: {len(insights)}")
    for insight in insights[:3]:
        print(f"   • {insight}")
    
    # Show recommendations
    recommendations = result.get('recommendations', [])
    print(f"\n🎯 Generated recommendations: {len(recommendations)}")
    for rec in recommendations[:3]:
        print(f"   • {rec}")
    
    # Show next actions
    next_actions = result.get('next_actions', [])
    print(f"\n⏭️ Next actions: {len(next_actions)}")
    for action in next_actions:
        print(f"   • {action}")
    
    print()


def test_edge_cases():
    """Test edge cases and error handling"""
    print("⚠️ Testing Edge Cases...")
    print("-" * 40)
    
    config = Config()
    engine = CompensationEngine(config)
    
    # Test empty activity data
    empty_result = engine.analyze_and_compensate([], [], {})
    print(f"✅ Empty data handling: {len(empty_result)} sections")
    
    # Test minimal data
    minimal_data = [{'timestamp': datetime.now().isoformat(), 'productivity_score': 50, 'duration': 3600}]
    minimal_result = engine.analyze_and_compensate(minimal_data, [], {})
    print(f"✅ Minimal data handling: {len(minimal_result.get('insights', []))} insights")
    
    # Test malformed timestamps
    malformed_data = [
        {'timestamp': 'invalid-timestamp', 'productivity_score': 75, 'duration': 3600},
        {'productivity_score': 80, 'duration': 3600}  # Missing timestamp
    ]
    
    try:
        malformed_result = engine.analyze_and_compensate(malformed_data, [], {})
        print("✅ Malformed data handled gracefully")
    except Exception as e:
        print(f"⚠️ Malformed data error: {e}")
    
    # Test extreme time debt
    # Create data showing very low productivity
    low_productivity_data = []
    for day in range(7):
        timestamp = (datetime.now() - timedelta(days=day)).isoformat()
        low_productivity_data.append({
            'timestamp': timestamp,
            'productivity_score': 20,  # Very low
            'duration': 1800,  # Only 30 minutes per day
            'focus_score': 20
        })
    
    extreme_result = engine.analyze_and_compensate(low_productivity_data, [], {'max_daily_makeup': 3.0})
    extreme_debt = extreme_result.get('time_debt', {})
    print(f"✅ Extreme time debt: {extreme_debt.get('deficit_hours', 0):.1f} hours deficit")
    
    # Test scheduling conflicts
    conflicting_tasks = [
        CompensationTask(
            id="conflict_1",
            title="Task 1",
            estimated_duration=4.0,  # Too long for available slots
            priority=TaskPriority.URGENT,
            required_energy=EnergyLevel.PEAK,
            deadline=datetime.now() + timedelta(hours=2),  # Very soon
            context="work",
            flexibility=0.0,
            compensation_for=None
        )
    ]
    
    conflict_result = engine.analyze_and_compensate([], conflicting_tasks, {})
    conflict_schedule = conflict_result.get('schedule', {})
    unscheduled = len(conflict_schedule.get('unscheduled_tasks', []))
    print(f"✅ Scheduling conflicts: {unscheduled} tasks couldn't be scheduled")
    
    print()


def test_export_functionality():
    """Test exporting compensation analysis"""
    print("💾 Testing Export Functionality...")
    print("-" * 40)
    
    config = Config()
    engine = CompensationEngine(config)
    
    # Generate comprehensive analysis
    activity_data = generate_mock_activity_data()
    user_tasks = []
    user_preferences = {'work_hours_start': 9, 'work_hours_end': 17}
    
    result = engine.analyze_and_compensate(activity_data, user_tasks, user_preferences)
    
    # Test JSON export
    try:
        json_str = json.dumps(result, indent=2, default=str)
        json_size = len(json_str.encode('utf-8'))
        print(f"✅ JSON export: {json_size} bytes")
        
        # Verify JSON is valid
        parsed_result = json.loads(json_str)
        print(f"   Sections exported: {len(parsed_result)}")
        
        # Check specific sections
        required_sections = ['energy_profile', 'time_debt', 'schedule', 'insights', 'recommendations']
        missing_sections = [section for section in required_sections if section not in parsed_result]
        
        if missing_sections:
            print(f"   ❌ Missing sections: {missing_sections}")
        else:
            print("   ✅ All required sections present")
        
    except Exception as e:
        print(f"   ❌ JSON export error: {e}")
    
    print()


if __name__ == "__main__":
    print("🚀 Pulse Activity Tracker - Compensation Engine Tests")
    print("=" * 65)
    
    try:
        test_energy_profile_analyzer()
        test_time_debt_calculator()
        test_smart_scheduler()
        test_compensation_engine()
        test_edge_cases()
        test_export_functionality()
        
        print("✅ All compensation engine tests completed successfully!")
        print("\n🎯 Key features tested:")
        print("  • Energy pattern analysis and classification")
        print("  • Time debt calculation and projection")
        print("  • Smart task scheduling with energy matching")
        print("  • Comprehensive compensation planning")
        print("  • Multiple scheduling preferences (immediate/distributed/delayed)")
        print("  • Task prioritization and deadline management")
        print("  • Intelligent insights and recommendations")
        print("  • Edge case handling and error recovery")
        print("  • JSON export functionality")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🏁 Compensation engine tests completed!")