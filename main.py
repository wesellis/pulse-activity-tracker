"""
Pulse Activity Tracker
Intelligent work-life balance automation system

Usage: python main.py
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Optional

# Add the pulse package to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from pulse.core.activity_monitor import ActivityMonitor
from pulse.core.todo_generator import TodoGenerator
from pulse.database.models import DatabaseManager
from pulse.utils.config import Config
from pulse.utils.helpers import setup_logging

class PulseTracker:
    def __init__(self):
        """Initialize Pulse with default settings"""
        self.config = Config()
        self.db_manager = DatabaseManager(self.config.database_url)
        self.activity_monitor = ActivityMonitor(self.config)
        self.todo_generator = TodoGenerator(self.config)
        
        # Setup logging
        self.logger = setup_logging()
        
        print("🔄 Pulse Activity Tracker - Intelligent Productivity Automation")
        print("=" * 60)
        print("Tracks your work patterns and generates smart todo suggestions")
    
    async def start_monitoring(self):
        """Start the main monitoring loop"""
        try:
            print("\n🚀 Starting activity monitoring...")
            print("💡 This will track your computer usage to learn work patterns")
            print("🔒 All data stays local unless you choose to share reports")
            
            # Initialize database
            await self.db_manager.initialize()
            print("✓ Database initialized")
            
            # Start activity monitoring
            await self.activity_monitor.start()
            print("✓ Activity monitoring started")
            
            # Main monitoring loop
            while True:
                # Collect activity data
                activity_data = await self.activity_monitor.get_current_activity()
                
                # Store in database
                await self.db_manager.store_activity(activity_data)
                
                # Generate todo suggestions periodically
                if self.should_update_todos():
                    todos = await self.todo_generator.generate_suggestions(activity_data)
                    await self.db_manager.store_todos(todos)
                    self.show_todo_updates(todos)
                
                # Wait before next collection
                await asyncio.sleep(self.config.monitoring_interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping Pulse...")
            await self.cleanup()
        except Exception as e:
            self.logger.error(f"Error in monitoring loop: {e}")
            print(f"❌ Error: {e}")
    
    def should_update_todos(self) -> bool:
        """Check if it's time to update todo suggestions"""
        # For now, update every hour during work hours
        import datetime
        now = datetime.datetime.now()
        return now.minute == 0 and 9 <= now.hour <= 17
    
    def show_todo_updates(self, todos: List[Dict]):
        """Display new todo suggestions to user"""
        if not todos:
            return
        
        print("\n📝 New todo suggestions based on your activity:")
        for i, todo in enumerate(todos[:3], 1):  # Show top 3
            print(f"   {i}. {todo.get('title', 'Untitled task')}")
        
        if len(todos) > 3:
            print(f"   ... and {len(todos) - 3} more suggestions")
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            await self.activity_monitor.stop()
            await self.db_manager.close()
            print("✓ Cleanup completed")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
    
    async def show_dashboard(self):
        """Show current productivity dashboard"""
        print("\n📊 Pulse Dashboard")
        print("-" * 30)
        
        # Get today's activity summary
        activity_summary = await self.db_manager.get_daily_summary()
        print(f"⏱️  Productive hours today: {activity_summary.get('productive_hours', 0):.1f}")
        print(f"💻 Most used app: {activity_summary.get('top_app', 'None')}")
        print(f"📋 Todos completed: {activity_summary.get('completed_todos', 0)}")
        
        # Show pending todos
        pending_todos = await self.db_manager.get_pending_todos()
        if pending_todos:
            print(f"\n📝 Pending todos ({len(pending_todos)}):")
            for todo in pending_todos[:5]:  # Show top 5
                print(f"   • {todo.get('title', 'Untitled')}")
    
    def run_interactive_mode(self):
        """Run in interactive mode for testing and setup"""
        print("\n🎮 Interactive Mode")
        print("1. Start monitoring")
        print("2. Show dashboard")
        print("3. Generate todos manually")
        print("4. Exit")
        
        while True:
            try:
                choice = input("\nChoose option (1-4): ").strip()
                
                if choice == "1":
                    asyncio.run(self.start_monitoring())
                elif choice == "2":
                    asyncio.run(self.show_dashboard())
                elif choice == "3":
                    asyncio.run(self.manual_todo_generation())
                elif choice == "4":
                    break
                else:
                    print("Invalid choice. Please enter 1-4.")
                    
            except KeyboardInterrupt:
                break
        
        print("👋 Thanks for using Pulse!")
    
    async def manual_todo_generation(self):
        """Manually trigger todo generation for testing"""
        print("\n🧠 Generating todo suggestions based on recent activity...")
        activity_data = await self.activity_monitor.get_recent_activity()
        todos = await self.todo_generator.generate_suggestions(activity_data)
        
        if todos:
            print("✓ Generated suggestions:")
            for i, todo in enumerate(todos, 1):
                print(f"   {i}. {todo.get('title', 'Untitled task')}")
        else:
            print("No suggestions generated. Need more activity data to learn patterns.")

def main():
    """Main entry point"""
    pulse = PulseTracker()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--monitor":
            asyncio.run(pulse.start_monitoring())
        elif sys.argv[1] == "--dashboard":
            asyncio.run(pulse.show_dashboard())
        else:
            print("Usage: python main.py [--monitor|--dashboard]")
    else:
        # Run in interactive mode
        pulse.run_interactive_mode()

if __name__ == "__main__":
    main()
