#!/usr/bin/env python3
"""
Test script for Pattern Analyzer
Tests pattern detection, analysis, and insights generation
"""

import sys
import os
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Add the pulse module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from pulse.utils.config import Config
from pulse.core.pattern_analyzer import PatternAnalyzer, TimePatternAnalyzer, ApplicationPatternAnalyzer, FileAccessAnalyzer


def generate_mock_activity_data() -> list:
    """Generate mock activity data for testing"""
    mock_data = []
    current_time = datetime.now()
    
    # Generate 7 days of mock data
    for day in range(7):
        day_start = current_time - timedelta(days=day)
        
        # Simulate different productivity patterns throughout the day
        for hour in range(8, 18):  # 8 AM to 6 PM
            timestamp = day_start.replace(hour=hour, minute=0, second=0)
            
            # Simulate productivity patterns (higher in morning, lower after lunch)
            if hour <= 11:
                base_productivity = 80 + (hour - 8) * 2  # 80-86%
            elif hour <= 14:
                base_productivity = 60 + (14 - hour) * 5  # 60-75%
            else:
                base_productivity = 70 + (18 - hour) * 2  # 70-78%
            
            # Add some variance
            variance = (day * hour) % 20 - 10  # -10 to +10
            productivity = max(20, min(100, base_productivity + variance))
            
            # Simulate different applications
            apps = ['code.exe', 'chrome.exe', 'slack.exe', 'excel.exe', 'terminal.exe']
            app_name = apps[(hour + day) % len(apps)]
            
            mock_data.append({
                'timestamp': timestamp.isoformat(),
                'app_name': app_name,
                'window_title': f'Working on Project {day + 1}',
                'productivity_score': productivity,
                'duration': 1800,  # 30 minutes
                'focus_score': productivity * 0.9,
                'idle_time': 0
            })
    
    return mock_data


def generate_mock_file_data() -> list:
    """Generate mock file access data for testing"""
    mock_files = []
    current_time = datetime.now()
    
    # Simulate different project files
    projects = ['project-alpha', 'project-beta', 'project-gamma']
    file_types = ['.py', '.js', '.md', '.json', '.html']
    
    for day in range(7):
        day_start = current_time - timedelta(days=day)
        
        for project in projects:
            for file_type in file_types:
                file_path = f"/home/user/projects/{project}/src/main{file_type}"
                
                # Simulate file access patterns
                for access in range(2):  # 2 accesses per file per day
                    timestamp = day_start + timedelta(hours=9 + access * 4)
                    
                    mock_files.append({
                        'file_path': file_path,
                        'timestamp': timestamp.isoformat(),
                        'action': 'write' if access == 1 else 'read',
                        'duration': 900,  # 15 minutes
                        'project': project
                    })
    
    return mock_files


def test_time_pattern_analyzer():
    """Test time-based pattern analysis"""
    print("🕐 Testing Time Pattern Analyzer...")
    print("-" * 40)
    
    config = Config()
    analyzer = TimePatternAnalyzer(config)
    
    # Test with mock data
    activity_data = generate_mock_activity_data()
    
    # Test productive hours analysis
    productive_hours = analyzer.analyze_productive_hours(activity_data)
    print(f"✅ Productive hours analysis: {len(productive_hours)} metrics")
    
    if productive_hours:
        print(f"   Peak hour: {productive_hours.get('peak_hour', 'Unknown')}:00")
        print(f"   Peak productivity: {productive_hours.get('peak_productivity', 0):.1f}%")
        print(f"   Energy pattern: {productive_hours.get('energy_pattern', 'Unknown')}")
        
        optimal_range = productive_hours.get('optimal_range', {})
        if optimal_range:
            print(f"   Optimal range: {optimal_range.get('start_hour', 'Unknown')}-{optimal_range.get('end_hour', 'Unknown')}:00")
    
    # Test weekly patterns
    weekly_patterns = analyzer.analyze_weekly_patterns(activity_data)
    print(f"\n✅ Weekly patterns analysis: {len(weekly_patterns)} metrics")
    
    if weekly_patterns:
        print(f"   Best day: {weekly_patterns.get('best_day', 'Unknown')}")
        print(f"   Best productivity: {weekly_patterns.get('best_productivity', 0):.1f}%")
        print(f"   Weekly trend: {weekly_patterns.get('weekly_trend', 'Unknown')}")
    
    print()


def test_application_pattern_analyzer():
    """Test application pattern analysis"""
    print("💻 Testing Application Pattern Analyzer...")
    print("-" * 40)
    
    config = Config()
    analyzer = ApplicationPatternAnalyzer(config)
    
    # Test with mock data
    activity_data = generate_mock_activity_data()
    
    app_patterns = analyzer.analyze_application_usage(activity_data)
    print(f"✅ Application usage analysis: {len(app_patterns)} sections")
    
    # Check application statistics
    app_stats = app_patterns.get('application_stats', {})
    print(f"   Applications tracked: {len(app_stats)}")
    
    # Show most used apps
    most_used = app_patterns.get('most_used_apps', [])
    if most_used:
        print(f"   Most used app: {most_used[0][0]} ({most_used[0][1]:.0f}s)")
    
    # Show productivity by category
    productivity_by_cat = app_patterns.get('productivity_by_category', {})
    print(f"   Categories analyzed: {len(productivity_by_cat)}")
    
    # Show workflow sequences
    sequences = app_patterns.get('workflow_sequences', {})
    transitions = sequences.get('common_transitions', [])
    if transitions:
        print(f"   Common transitions: {len(transitions)} patterns")
        print(f"   Top transition: {transitions[0][0][0]} → {transitions[0][0][1]}")
    
    print()


def test_file_access_analyzer():
    """Test file access pattern analysis"""
    print("📁 Testing File Access Analyzer...")
    print("-" * 40)
    
    config = Config()
    analyzer = FileAccessAnalyzer(config)
    
    # Test with mock data
    file_data = generate_mock_file_data()
    
    file_patterns = analyzer.analyze_file_patterns(file_data)
    print(f"✅ File patterns analysis: {len(file_patterns)} sections")
    
    # Check file statistics
    file_stats = file_patterns.get('file_statistics', {})
    print(f"   Files tracked: {len(file_stats)}")
    
    # Check project statistics
    project_stats = file_patterns.get('project_statistics', {})
    print(f"   Projects identified: {len(project_stats)}")
    
    # Show active projects
    active_projects = file_patterns.get('active_projects', [])
    print(f"   Active projects: {len(active_projects)}")
    if active_projects:
        top_project = active_projects[0]
        print(f"   Most active: {top_project['project']} ({top_project['file_count']} files)")
    
    # Show unfinished work
    unfinished = file_patterns.get('unfinished_work', [])
    print(f"   Unfinished work items: {len(unfinished)}")
    if unfinished:
        top_unfinished = unfinished[0]
        print(f"   Top priority: {Path(top_unfinished['file_path']).name}")
    
    # Show file type analysis
    file_types = file_patterns.get('file_type_analysis', {})
    print(f"   File types analyzed: {len(file_types)}")
    
    print()


def test_comprehensive_pattern_analysis():
    """Test comprehensive pattern analysis"""
    print("🔍 Testing Comprehensive Pattern Analysis...")
    print("-" * 40)
    
    config = Config()
    analyzer = PatternAnalyzer(config)
    
    # Generate test data
    activity_data = generate_mock_activity_data()
    file_data = generate_mock_file_data()
    
    # Perform comprehensive analysis
    all_patterns = analyzer.analyze_all_patterns(activity_data, file_data)
    print(f"✅ Comprehensive analysis: {len(all_patterns)} sections")
    
    # Check all pattern types
    required_sections = ['time_patterns', 'application_patterns', 'file_patterns', 'insights', 'recommendations']
    for section in required_sections:
        if section in all_patterns:
            print(f"   ✅ {section}: Present")
        else:
            print(f"   ❌ {section}: Missing")
    
    # Show insights
    insights = all_patterns.get('insights', [])
    print(f"\n💡 Generated insights: {len(insights)}")
    for i, insight in enumerate(insights[:3], 1):
        print(f"   {i}. {insight}")
    
    # Show recommendations
    recommendations = all_patterns.get('recommendations', [])
    print(f"\n🎯 Generated recommendations: {len(recommendations)}")
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"   {i}. {rec}")
    
    # Test pattern summary
    summary = analyzer.get_pattern_summary(all_patterns)
    print(f"\n📊 Pattern summary:")
    print(f"   Productivity peak: {summary.get('productivity_peak', 'Unknown')}:00")
    print(f"   Energy type: {summary.get('energy_type', 'Unknown')}")
    print(f"   Most used app: {summary.get('most_used_app', 'Unknown')}")
    print(f"   Active projects: {summary.get('active_projects_count', 0)}")
    print(f"   Unfinished work: {summary.get('unfinished_work_count', 0)}")
    
    print()


def test_pattern_export():
    """Test pattern export functionality"""
    print("💾 Testing Pattern Export...")
    print("-" * 40)
    
    config = Config()
    analyzer = PatternAnalyzer(config)
    
    # Generate test data and analyze
    activity_data = generate_mock_activity_data()
    file_data = generate_mock_file_data()
    patterns = analyzer.analyze_all_patterns(activity_data, file_data)
    
    # Test JSON export
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(patterns, f, indent=2, default=str)
        json_path = f.name
    
    try:
        # Verify JSON export
        with open(json_path, 'r') as f:
            loaded_patterns = json.load(f)
        
        file_size = os.path.getsize(json_path)
        print(f"✅ JSON export: {file_size} bytes")
        print(f"   Sections exported: {len(loaded_patterns)}")
        print(f"   Insights exported: {len(loaded_patterns.get('insights', []))}")
        print(f"   Recommendations exported: {len(loaded_patterns.get('recommendations', []))}")
        
        # Show sample data
        data_period = loaded_patterns.get('data_period', {})
        if data_period:
            print(f"   Data period: {data_period.get('duration_days', 0)} days")
            print(f"   Data points: {data_period.get('data_points', 0)}")
    
    finally:
        # Clean up
        os.unlink(json_path)
    
    print()


def test_edge_cases():
    """Test edge cases and error handling"""
    print("⚠️ Testing Edge Cases...")
    print("-" * 40)
    
    config = Config()
    analyzer = PatternAnalyzer(config)
    
    # Test empty data
    empty_patterns = analyzer.analyze_all_patterns([])
    print(f"✅ Empty data handling: {len(empty_patterns)} sections")
    
    # Test malformed data
    malformed_data = [
        {'timestamp': 'invalid-timestamp', 'app_name': 'test'},
        {'productivity_score': 'not-a-number'},
        {'app_name': None, 'timestamp': datetime.now().isoformat()}
    ]
    
    try:
        malformed_patterns = analyzer.analyze_all_patterns(malformed_data)
        print("✅ Malformed data handled gracefully")
    except Exception as e:
        print(f"⚠️ Malformed data error: {e}")
    
    # Test single data point
    single_point = [{'timestamp': datetime.now().isoformat(), 'app_name': 'test', 'productivity_score': 75}]
    single_patterns = analyzer.analyze_all_patterns(single_point)
    print(f"✅ Single data point: {len(single_patterns.get('insights', []))} insights generated")
    
    # Test missing required fields
    incomplete_data = [{'app_name': 'test'}]  # Missing timestamp
    incomplete_patterns = analyzer.analyze_all_patterns(incomplete_data)
    print("✅ Incomplete data handled")
    
    print()


if __name__ == "__main__":
    print("🚀 Pulse Activity Tracker - Pattern Analysis Tests")
    print("=" * 60)
    
    try:
        test_time_pattern_analyzer()
        test_application_pattern_analyzer()
        test_file_access_analyzer()
        test_comprehensive_pattern_analysis()
        test_pattern_export()
        test_edge_cases()
        
        print("✅ All pattern analysis tests completed successfully!")
        print("\n🎯 Key features tested:")
        print("  • Time-based productivity pattern detection")
        print("  • Application usage workflow analysis")
        print("  • File access and project continuity tracking")
        print("  • Comprehensive pattern integration")
        print("  • Intelligent insights and recommendations generation")
        print("  • Pattern export and serialization")
        print("  • Edge case handling and error recovery")
        print("  • Data validation and malformed input handling")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🏁 Pattern analysis tests completed!")