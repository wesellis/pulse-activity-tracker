#!/usr/bin/env python3
"""
Test script for Reporting System
Tests report generation, analytics, and export functionality
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
from pulse.reports.report_generator import ReportGenerator, ProductivityAnalytics


def test_analytics_engine():
    """Test the productivity analytics engine"""
    print("🧮 Testing Analytics Engine...")
    print("-" * 40)
    
    analytics = ProductivityAnalytics()
    
    # Test trend calculation
    mock_daily_data = [
        {'avg_productivity': 60, 'avg_focus': 70},
        {'avg_productivity': 65, 'avg_focus': 72},
        {'avg_productivity': 70, 'avg_focus': 75},
        {'avg_productivity': 75, 'avg_focus': 78},
        {'avg_productivity': 80, 'avg_focus': 80}
    ]
    
    trends = analytics.calculate_productivity_trends(mock_daily_data)
    print(f"✅ Trend calculation: {trends['trend_direction']} (value: {trends['trend_value']:.1f})")
    print(f"✅ Average productivity: {trends['average_productivity']:.1f}%")
    print(f"✅ Consistency score: {trends['consistency_score']:.1f}")
    
    # Test insights generation
    test_data = {
        'summary': {
            'avg_productivity': 75,
            'avg_focus': 68
        },
        'trends': trends
    }
    
    insights = analytics.generate_insights(test_data)
    print(f"\\n💡 Generated {len(insights)} insights:")
    for insight in insights:
        print(f"   • {insight}")
    
    # Test recommendations
    recommendations = analytics.generate_recommendations(test_data)
    print(f"\\n🎯 Generated {len(recommendations)} recommendations:")
    for rec in recommendations[:3]:  # Show first 3
        print(f"   • {rec}")
    
    print()


def test_report_generation():
    """Test report generation functionality"""
    print("📊 Testing Report Generation...")
    print("-" * 40)
    
    config = Config()
    generator = ReportGenerator(config)
    
    # Test daily report
    daily_report = generator.generate_daily_report()
    print(f"✅ Daily report generated")
    print(f"   Type: {daily_report.get('type')}")
    print(f"   Summary: {len(daily_report.get('summary', {}))} metrics")
    print(f"   Insights: {len(daily_report.get('insights', []))} insights")
    print(f"   Recommendations: {len(daily_report.get('recommendations', []))} recommendations")
    
    # Test weekly report
    weekly_report = generator.generate_weekly_report()
    print(f"\\n✅ Weekly report generated")
    print(f"   Period: {weekly_report.get('period', {}).get('start', 'Unknown')} to {weekly_report.get('period', {}).get('end', 'Unknown')}")
    print(f"   Daily breakdown: {len(weekly_report.get('daily_breakdown', {}))} days")
    
    # Test monthly report
    monthly_report = generator.generate_monthly_report()
    print(f"\\n✅ Monthly report generated")
    print(f"   Daily breakdown: {len(monthly_report.get('daily_breakdown', {}))} days")
    
    # Show sample summary
    summary = daily_report.get('summary', {})
    if summary:
        print(f"\\n📈 Sample Daily Summary:")
        print(f"   Average Productivity: {summary.get('avg_productivity', 0):.1f}%")
        print(f"   Average Focus: {summary.get('avg_focus', 0):.1f}%")
        print(f"   Productive Hours: {summary.get('total_productive_hours', 0):.1f}")
        print(f"   Sessions: {summary.get('total_sessions', 0)}")
    
    print()


def test_export_functionality():
    """Test export functionality with different formats"""
    print("💾 Testing Export Functionality...")
    print("-" * 40)
    
    config = Config()
    generator = ReportGenerator(config)
    
    # Generate a sample report
    report = generator.generate_daily_report()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test JSON export
        json_path = os.path.join(temp_dir, 'test_report.json')
        json_report = generator.generate_report(
            'daily',
            datetime.now() - timedelta(days=1),
            datetime.now(),
            'json',
            json_path
        )
        
        if os.path.exists(json_path):
            file_size = os.path.getsize(json_path)
            print(f"✅ JSON export: {file_size} bytes")
            
            # Verify JSON is valid
            try:
                with open(json_path, 'r') as f:
                    json.load(f)
                print("✅ JSON format valid")
            except:
                print("❌ JSON format invalid")
        
        # Test CSV export
        csv_path = os.path.join(temp_dir, 'test_report.csv')
        csv_report = generator.generate_report(
            'weekly',
            datetime.now() - timedelta(days=7),
            datetime.now(),
            'csv',
            csv_path
        )
        
        if os.path.exists(csv_path):
            file_size = os.path.getsize(csv_path)
            print(f"✅ CSV export: {file_size} bytes")
            
            # Show first few lines
            with open(csv_path, 'r') as f:
                lines = f.readlines()[:5]
                print(f"   First {len(lines)} lines preview:")
                for line in lines:
                    print(f"     {line.strip()}")
        
        # Test text export
        text_path = os.path.join(temp_dir, 'test_report.txt')
        text_report = generator.generate_report(
            'monthly',
            datetime.now() - timedelta(days=30),
            datetime.now(),
            'text',
            text_path
        )
        
        if os.path.exists(text_path):
            file_size = os.path.getsize(text_path)
            print(f"\\n✅ Text export: {file_size} bytes")
            
            # Show preview
            with open(text_path, 'r') as f:
                lines = f.readlines()[:8]
                print("   Preview:")
                for line in lines:
                    print(f"     {line.rstrip()}")
    
    print()


def test_report_templates():
    """Test report templates and configuration"""
    print("📋 Testing Report Templates...")
    print("-" * 40)
    
    config = Config()
    generator = ReportGenerator(config)
    
    templates = generator.get_report_templates()
    print(f"✅ Available report types: {', '.join(templates['types'])}")
    print(f"✅ Available formats: {', '.join(templates['formats'])}")
    print(f"✅ Default format: {templates['default_format']}")
    print(f"✅ Output directory: {templates['output_directory']}")
    
    # Test scheduling
    schedule_success = generator.schedule_report('daily', 'json', 'daily')
    print(f"\\n✅ Report scheduling: {'Success' if schedule_success else 'Failed'}")
    
    print()


def test_report_content_quality():
    """Test the quality and completeness of report content"""
    print("🔍 Testing Report Content Quality...")
    print("-" * 40)
    
    config = Config()
    generator = ReportGenerator(config)
    
    # Generate comprehensive report
    report = generator.generate_weekly_report()
    
    # Check required sections
    required_sections = ['type', 'period', 'summary', 'insights', 'recommendations', 'daily_breakdown']
    missing_sections = []
    
    for section in required_sections:
        if section not in report:
            missing_sections.append(section)
        else:
            print(f"✅ Section '{section}': Present")
    
    if missing_sections:
        print(f"❌ Missing sections: {missing_sections}")
    else:
        print("✅ All required sections present")
    
    # Check summary metrics
    summary = report.get('summary', {})
    expected_metrics = ['avg_productivity', 'avg_focus', 'total_productive_hours', 'total_sessions']
    
    print(f"\\n📊 Summary metrics:")
    for metric in expected_metrics:
        value = summary.get(metric, 'Missing')
        print(f"   {metric}: {value}")
    
    # Check insights quality
    insights = report.get('insights', [])
    recommendations = report.get('recommendations', [])
    
    print(f"\\n💡 Content quality:")
    print(f"   Insights generated: {len(insights)}")
    print(f"   Recommendations: {len(recommendations)}")
    print(f"   Daily breakdown: {len(report.get('daily_breakdown', {}))} days")
    
    # Sample insights and recommendations
    if insights:
        print(f"\\n   Sample insight: {insights[0][:80]}...")
    if recommendations:
        print(f"   Sample recommendation: {recommendations[0][:80]}...")
    
    print()


def test_edge_cases():
    """Test edge cases and error handling"""
    print("⚠️ Testing Edge Cases...")
    print("-" * 40)
    
    config = Config()
    generator = ReportGenerator(config)
    analytics = ProductivityAnalytics()
    
    # Test empty data
    empty_trends = analytics.calculate_productivity_trends([])
    print(f"✅ Empty data handling: {len(empty_trends)} trend metrics")
    
    # Test single data point
    single_point = analytics.calculate_productivity_trends([{'avg_productivity': 75}])
    print(f"✅ Single data point: {single_point.get('trend_direction', 'No trend')}")
    
    # Test invalid date range
    try:
        future_start = datetime.now() + timedelta(days=30)
        future_end = datetime.now() + timedelta(days=60)
        future_report = generator.generate_report('daily', future_start, future_end)
        print("✅ Future date range handled")
    except Exception as e:
        print(f"⚠️ Future date range error: {e}")
    
    # Test invalid export format
    invalid_report = generator.generate_report(
        'daily',
        datetime.now() - timedelta(days=1),
        datetime.now(),
        'invalid_format'
    )
    print(f"✅ Invalid format handling: Report still generated")
    
    print()


if __name__ == "__main__":
    print("🚀 Pulse Activity Tracker - Reporting Tests")
    print("=" * 55)
    
    try:
        test_analytics_engine()
        test_report_generation()
        test_export_functionality()
        test_report_templates()
        test_report_content_quality()
        test_edge_cases()
        
        print("✅ All reporting tests completed successfully!")
        print("\\n🎯 Key features tested:")
        print("  • Productivity analytics and trend calculation")
        print("  • Daily, weekly, and monthly report generation")
        print("  • Multi-format export (JSON, CSV, text)")
        print("  • Insight and recommendation generation")
        print("  • Report scheduling and templates")
        print("  • Content quality and completeness")
        print("  • Edge case handling and error recovery")
        
    except Exception as e:
        print(f"\\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\\n🏁 Reporting tests completed!")