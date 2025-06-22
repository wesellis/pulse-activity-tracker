"""
CLI Commands for Pulse Activity Tracker
Comprehensive command-line interface with all major functionality
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import argparse
import time

from ..utils.config import Config
from ..utils.settings_manager import SettingsManager
from ..core.activity_monitor import ActivityMonitor
from ..core.todo_generator_v2 import TodoGenerator
from ..database import init_db, get_db_session
from ..database.crud import ActivityCRUD, TodoCRUD, SessionSummaryCRUD
from ..database.backup import create_backup, list_backups


class PulseCLI:
    """Main CLI interface for Pulse Activity Tracker"""
    
    def __init__(self):
        self.config = Config()
        self.settings_manager = SettingsManager(self.config)
        self.activity_monitor = ActivityMonitor(self.config)
        self.todo_generator = TodoGenerator(self.config)
        
        # Initialize database
        init_db()
    
    def run(self, args: List[str]):
        """Main CLI entry point"""
        parser = self._create_parser()
        
        if not args:
            parser.print_help()
            return
        
        parsed_args = parser.parse_args(args)
        
        # Route to appropriate command
        if hasattr(parsed_args, 'func'):
            try:
                if asyncio.iscoroutinefunction(parsed_args.func):
                    asyncio.run(parsed_args.func(parsed_args))
                else:
                    parsed_args.func(parsed_args)
            except KeyboardInterrupt:
                print("\\n⏹️  Interrupted by user")
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            parser.print_help()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser"""
        parser = argparse.ArgumentParser(
            description="Pulse Activity Tracker - Intelligent Work-Life Balance Automation",
            epilog="Visit github.com/pulse-tracker for documentation and examples"
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Monitor command
        monitor_parser = subparsers.add_parser('monitor', help='Start activity monitoring')
        monitor_parser.add_argument('--duration', '-d', type=int, help='Duration in minutes')
        monitor_parser.add_argument('--silent', '-s', action='store_true', help='Run silently without output')
        monitor_parser.set_defaults(func=self.cmd_monitor)
        
        # Dashboard command
        dashboard_parser = subparsers.add_parser('dashboard', help='Show productivity dashboard')
        dashboard_parser.add_argument('--period', '-p', choices=['today', 'week', 'month'], default='today')
        dashboard_parser.add_argument('--detailed', action='store_true', help='Show detailed breakdown')
        dashboard_parser.set_defaults(func=self.cmd_dashboard)
        
        # Todo commands
        todo_parser = subparsers.add_parser('todo', help='Manage todos')
        todo_subparsers = todo_parser.add_subparsers(dest='todo_action')
        
        # Todo list
        list_parser = todo_subparsers.add_parser('list', help='List todos')
        list_parser.add_argument('--status', choices=['pending', 'in_progress', 'completed'], help='Filter by status')
        list_parser.add_argument('--category', help='Filter by category')
        list_parser.set_defaults(func=self.cmd_todo_list)
        
        # Todo add
        add_parser = todo_subparsers.add_parser('add', help='Add a new todo')
        add_parser.add_argument('title', help='Todo title')
        add_parser.add_argument('--description', '-d', help='Todo description')
        add_parser.add_argument('--priority', '-p', choices=['low', 'medium', 'high', 'urgent'], default='medium')
        add_parser.add_argument('--category', '-c', help='Todo category')
        add_parser.set_defaults(func=self.cmd_todo_add)
        
        # Todo complete
        complete_parser = todo_subparsers.add_parser('complete', help='Mark todo as complete')
        complete_parser.add_argument('id', type=int, help='Todo ID')
        complete_parser.set_defaults(func=self.cmd_todo_complete)
        
        # Todo generate
        generate_parser = todo_subparsers.add_parser('generate', help='Generate AI suggestions')
        generate_parser.add_argument('--count', '-n', type=int, default=10, help='Number of suggestions')
        generate_parser.set_defaults(func=self.cmd_todo_generate)
        
        # Report commands
        report_parser = subparsers.add_parser('report', help='Generate reports')
        report_parser.add_argument('type', choices=['daily', 'weekly', 'monthly'], help='Report type')
        report_parser.add_argument('--format', '-f', choices=['json', 'text', 'csv'], default='text')
        report_parser.add_argument('--output', '-o', help='Output file path')
        report_parser.add_argument('--email', action='store_true', help='Email the report')
        report_parser.set_defaults(func=self.cmd_report)
        
        # Settings commands
        settings_parser = subparsers.add_parser('settings', help='Manage settings')
        settings_subparsers = settings_parser.add_subparsers(dest='settings_action')
        
        # Settings show
        show_parser = settings_subparsers.add_parser('show', help='Show current settings')
        show_parser.add_argument('--category', '-c', help='Show specific category')
        show_parser.set_defaults(func=self.cmd_settings_show)
        
        # Settings set
        set_parser = settings_subparsers.add_parser('set', help='Set a setting value')
        set_parser.add_argument('key', help='Setting key (category.setting)')
        set_parser.add_argument('value', help='Setting value')
        set_parser.set_defaults(func=self.cmd_settings_set)
        
        # Settings reset
        reset_parser = settings_subparsers.add_parser('reset', help='Reset settings')
        reset_parser.add_argument('--category', '-c', help='Reset specific category')
        reset_parser.add_argument('--all', action='store_true', help='Reset all settings')
        reset_parser.set_defaults(func=self.cmd_settings_reset)
        
        # Backup commands
        backup_parser = subparsers.add_parser('backup', help='Backup and restore')
        backup_subparsers = backup_parser.add_subparsers(dest='backup_action')
        
        # Backup create
        create_parser = backup_subparsers.add_parser('create', help='Create backup')
        create_parser.add_argument('--name', '-n', help='Backup name')
        create_parser.set_defaults(func=self.cmd_backup_create)
        
        # Backup list
        list_backup_parser = backup_subparsers.add_parser('list', help='List backups')
        list_backup_parser.set_defaults(func=self.cmd_backup_list)
        
        # Status command
        status_parser = subparsers.add_parser('status', help='Show system status')
        status_parser.set_defaults(func=self.cmd_status)
        
        return parser
    
    async def cmd_monitor(self, args):
        """Start activity monitoring"""
        print("🔍 Starting Pulse Activity Monitor...")
        print("=" * 50)
        
        duration = args.duration * 60 if args.duration else None
        start_time = time.time()
        
        try:
            await self.activity_monitor.start()
            
            if not args.silent:
                print("✅ Monitoring started")
                print("📊 Collecting activity data...")
                if duration:
                    print(f"⏱️  Running for {args.duration} minutes")
                print("Press Ctrl+C to stop\\n")
            
            iteration = 0
            while True:
                # Check duration limit
                if duration and (time.time() - start_time) >= duration:
                    break
                
                # Get activity data
                activity_data = await self.activity_monitor.get_current_activity()
                
                # Store in database (simplified for CLI)
                if not args.silent and iteration % 10 == 0:  # Update every 10 iterations
                    productivity = activity_data.get('productivity_indicators', {})
                    print(f"📈 Productivity: {productivity.get('productivity_score', 0):.1f}% | "
                          f"Focus: {productivity.get('focus_score', 0):.1f}% | "
                          f"Apps: {len(activity_data.get('session_data', {}).get('applications', {}))}")
                
                iteration += 1
                await asyncio.sleep(self.config.monitoring_interval)
                
        except KeyboardInterrupt:
            pass
        finally:
            await self.activity_monitor.stop()
            if not args.silent:
                print("\\n✅ Monitoring stopped")
                
                # Show session summary
                session_summary = self.activity_monitor.get_session_summary()
                print("\\n📊 Session Summary:")
                print(f"   Duration: {session_summary.get('session_duration', 'Unknown')}")
                print(f"   Applications: {session_summary.get('total_applications', 0)}")
                print(f"   Productivity: {session_summary.get('productivity_metrics', {}).get('productivity_score', 0):.1f}%")
    
    def cmd_dashboard(self, args):
        """Show productivity dashboard"""
        print("📊 Pulse Dashboard")
        print("=" * 30)
        
        # Calculate date range
        if args.period == 'today':
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = datetime.now()
            period_name = "Today"
        elif args.period == 'week':
            start_date = datetime.now() - timedelta(days=7)
            end_date = datetime.now()
            period_name = "Past 7 days"
        else:  # month
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()
            period_name = "Past 30 days"
        
        print(f"📅 Period: {period_name}\\n")
        
        try:
            with get_db_session() as db:
                # Get productivity stats
                stats = SessionSummaryCRUD.get_productivity_stats(db, start_date, end_date)
                
                print(f"⚡ Average Productivity: {stats['avg_productivity']:.1f}%")
                print(f"🎯 Average Focus: {stats['avg_focus']:.1f}%")
                print(f"⏱️  Total Productive Hours: {stats['total_productive_hours']:.1f}")
                print(f"📈 Total Sessions: {stats['total_sessions']}")
                
                if args.detailed and stats['daily_breakdown']:
                    print("\\n📊 Daily Breakdown:")
                    for date, daily_stats in sorted(stats['daily_breakdown'].items())[-7:]:
                        print(f"   {date}: {daily_stats['avg_productivity']:.1f}% productivity, "
                              f"{daily_stats['productive_hours']:.1f}h productive")
                
                # Get recent todos
                todos = TodoCRUD.get_active(db)
                if todos:
                    print(f"\\n📝 Active Todos ({len(todos)}):")
                    for todo in todos[:5]:
                        print(f"   • {todo.title} ({todo.priority})")
                    if len(todos) > 5:
                        print(f"   ... and {len(todos) - 5} more")
                else:
                    print("\\n📝 No active todos")
                
        except Exception as e:
            print(f"❌ Error accessing database: {e}")
    
    def cmd_todo_list(self, args):
        """List todos"""
        try:
            with get_db_session() as db:
                if args.status:
                    # Filter by status (simplified for CLI)
                    todos = [t for t in TodoCRUD.get_active(db) if t.status == args.status]
                else:
                    todos = TodoCRUD.get_active(db)
                
                if not todos:
                    print("📝 No todos found")
                    return
                
                print(f"📝 Todos ({len(todos)}):")
                print("=" * 40)
                
                for todo in todos:
                    status_icon = "✅" if todo.status == "completed" else "🔄" if todo.status == "in_progress" else "⏸️"
                    priority_icon = "🔴" if todo.priority == "urgent" else "🟡" if todo.priority == "high" else "🟢"
                    
                    print(f"{status_icon} {priority_icon} [{todo.id}] {todo.title}")
                    if todo.description:
                        print(f"    {todo.description}")
                    print(f"    Category: {todo.category or 'None'} | Priority: {todo.priority}")
                    if todo.due_date:
                        print(f"    Due: {todo.due_date.strftime('%Y-%m-%d %H:%M')}")
                    print()
                
        except Exception as e:
            print(f"❌ Error listing todos: {e}")
    
    def cmd_todo_add(self, args):
        """Add a new todo"""
        try:
            with get_db_session() as db:
                todo_data = {
                    'title': args.title,
                    'description': args.description,
                    'priority': args.priority,
                    'category': args.category or 'general',
                    'is_ai_generated': False
                }
                
                todo = TodoCRUD.create(db, todo_data)
                if todo:
                    print(f"✅ Todo created with ID {todo.id}")
                    print(f"   Title: {todo.title}")
                    print(f"   Priority: {todo.priority}")
                    print(f"   Category: {todo.category}")
                else:
                    print("❌ Failed to create todo")
                    
        except Exception as e:
            print(f"❌ Error creating todo: {e}")
    
    def cmd_todo_complete(self, args):
        """Mark todo as complete"""
        try:
            with get_db_session() as db:
                todo = TodoCRUD.update(db, args.id, {
                    'status': 'completed',
                    'completed_at': datetime.now()
                })
                
                if todo:
                    print(f"✅ Todo #{args.id} marked as completed")
                    print(f"   Title: {todo.title}")
                else:
                    print(f"❌ Todo #{args.id} not found")
                    
        except Exception as e:
            print(f"❌ Error completing todo: {e}")
    
    async def cmd_todo_generate(self, args):
        """Generate AI todo suggestions"""
        print("🧠 Generating AI todo suggestions...")
        
        try:
            # Get recent activity data
            activity_data = await self.activity_monitor.get_current_activity()
            
            # Generate suggestions
            suggestions = await self.todo_generator.generate_suggestions(activity_data)
            
            if not suggestions:
                print("💡 No suggestions generated. Try using the system for a while to build activity patterns.")
                return
            
            print(f"\\n📝 Generated {len(suggestions)} suggestions:")
            print("=" * 50)
            
            for i, suggestion in enumerate(suggestions[:args.count], 1):
                priority_icon = "🔴" if suggestion.get('priority') == "urgent" else "🟡" if suggestion.get('priority') == "high" else "🟢"
                
                print(f"{priority_icon} {i}. {suggestion.get('title', 'Untitled')}")
                print(f"    {suggestion.get('description', 'No description')}")
                print(f"    Category: {suggestion.get('category', 'general')} | "
                      f"Confidence: {suggestion.get('confidence', 0):.2f} | "
                      f"Source: {suggestion.get('source', 'unknown')}")
                if suggestion.get('estimated_minutes'):
                    print(f"    Estimated time: {suggestion.get('estimated_minutes')} minutes")
                print()
            
            # Ask if user wants to save any suggestions
            if suggestions:
                try:
                    save_choice = input("💾 Save any suggestions as todos? (y/N): ").strip().lower()
                    if save_choice == 'y':
                        indices = input("Enter suggestion numbers to save (e.g., 1,3,5): ").strip()
                        if indices:
                            selected = [int(i.strip()) - 1 for i in indices.split(',') if i.strip().isdigit()]
                            
                            saved_count = 0
                            with get_db_session() as db:
                                for idx in selected:
                                    if 0 <= idx < len(suggestions):
                                        suggestion = suggestions[idx]
                                        todo_data = {
                                            'title': suggestion.get('title'),
                                            'description': suggestion.get('description'),
                                            'priority': suggestion.get('priority', 'medium'),
                                            'category': suggestion.get('category', 'general'),
                                            'is_ai_generated': True,
                                            'confidence_score': suggestion.get('confidence'),
                                            'generation_reason': f"Generated from {suggestion.get('source')}"
                                        }
                                        
                                        if TodoCRUD.create(db, todo_data):
                                            saved_count += 1
                            
                            print(f"✅ Saved {saved_count} suggestions as todos")
                except (KeyboardInterrupt, EOFError):
                    print("\\n⏹️  Cancelled")
                
        except Exception as e:
            print(f"❌ Error generating suggestions: {e}")
    
    def cmd_report(self, args):
        """Generate reports"""
        print(f"📊 Generating {args.type} report...")
        
        # Calculate date range based on report type
        if args.type == 'daily':
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = datetime.now()
        elif args.type == 'weekly':
            start_date = datetime.now() - timedelta(days=7)
            end_date = datetime.now()
        else:  # monthly
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()
        
        try:
            with get_db_session() as db:
                # Get productivity stats
                stats = SessionSummaryCRUD.get_productivity_stats(db, start_date, end_date)
                
                # Generate report content
                report_data = {
                    'type': args.type,
                    'period': {
                        'start': start_date.isoformat(),
                        'end': end_date.isoformat()
                    },
                    'summary': {
                        'avg_productivity': stats['avg_productivity'],
                        'avg_focus': stats['avg_focus'],
                        'total_productive_hours': stats['total_productive_hours'],
                        'total_sessions': stats['total_sessions']
                    },
                    'daily_breakdown': stats.get('daily_breakdown', {}),
                    'generated_at': datetime.now().isoformat()
                }
                
                # Format output
                if args.format == 'json':
                    output = json.dumps(report_data, indent=2)
                elif args.format == 'csv':
                    # Simple CSV format for daily breakdown
                    output = "Date,Productivity,Focus,Productive Hours,Sessions\\n"
                    for date, data in stats.get('daily_breakdown', {}).items():
                        output += f"{date},{data['avg_productivity']},{data.get('avg_focus', 0)},{data['productive_hours']},{data['sessions']}\\n"
                else:  # text format
                    output = f"""
Pulse Activity Report - {args.type.title()}
{'=' * 40}
Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}

SUMMARY
-------
Average Productivity: {stats['avg_productivity']:.1f}%
Average Focus: {stats['avg_focus']:.1f}%
Total Productive Hours: {stats['total_productive_hours']:.1f}
Total Sessions: {stats['total_sessions']}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
                
                # Output to file or console
                if args.output:
                    with open(args.output, 'w') as f:
                        f.write(output)
                    print(f"✅ Report saved to {args.output}")
                else:
                    print(output)
                
        except Exception as e:
            print(f"❌ Error generating report: {e}")
    
    def cmd_settings_show(self, args):
        """Show current settings"""
        if args.category:
            settings = self.settings_manager.get_category(args.category)
            if settings:
                print(f"⚙️ Settings - {args.category}")
                print("=" * 30)
                for key, value in settings.items():
                    print(f"{key}: {value}")
            else:
                print(f"❌ Category '{args.category}' not found")
        else:
            summary = self.settings_manager.get_settings_summary()
            print("⚙️ Settings Summary")
            print("=" * 25)
            print(f"Categories: {', '.join(summary['categories'])}")
            print(f"Total settings: {summary['total_settings']}")
            print(f"Privacy mode: {summary['privacy_mode']}")
            print(f"Notifications: {summary['notifications_enabled']}")
            print(f"Work hours: {summary['work_hours']}")
    
    def cmd_settings_set(self, args):
        """Set a setting value"""
        try:
            # Parse category.key format
            if '.' not in args.key:
                print("❌ Key must be in format 'category.setting'")
                return
            
            category, key = args.key.split('.', 1)
            
            # Convert value to appropriate type
            value = args.value
            if value.lower() in ['true', 'false']:
                value = value.lower() == 'true'
            elif value.isdigit():
                value = int(value)
            elif value.replace('.', '').isdigit():
                value = float(value)
            
            success = self.settings_manager.set_setting(category, key, value)
            if success:
                print(f"✅ Updated {category}.{key} = {value}")
            else:
                print(f"❌ Failed to update {category}.{key}")
                
        except Exception as e:
            print(f"❌ Error updating setting: {e}")
    
    def cmd_settings_reset(self, args):
        """Reset settings"""
        if args.all:
            success = self.settings_manager.reset_all_settings()
            if success:
                print("✅ All settings reset to defaults")
            else:
                print("❌ Failed to reset settings")
        elif args.category:
            success = self.settings_manager.reset_category(args.category)
            if success:
                print(f"✅ Category '{args.category}' reset to defaults")
            else:
                print(f"❌ Failed to reset category '{args.category}'")
        else:
            print("❌ Must specify --category or --all")
    
    def cmd_backup_create(self, args):
        """Create a backup"""
        try:
            backup_path = create_backup(args.name)
            if backup_path:
                print(f"✅ Backup created: {backup_path.name}")
                print(f"   Size: {backup_path.stat().st_size / 1024:.2f} KB")
            else:
                print("❌ Failed to create backup")
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
    
    def cmd_backup_list(self, args):
        """List available backups"""
        try:
            backups = list_backups()
            if not backups:
                print("📦 No backups found")
                return
            
            print(f"📦 Available Backups ({len(backups)}):")
            print("=" * 40)
            
            for backup in backups:
                created = datetime.fromtimestamp(backup['created'])
                print(f"📄 {backup['filename']}")
                print(f"   Size: {backup['size_mb']} MB")
                print(f"   Created: {created.strftime('%Y-%m-%d %H:%M:%S')}")
                if backup.get('metadata'):
                    print(f"   Stats: {backup['metadata'].get('database_stats', {})}")
                print()
                
        except Exception as e:
            print(f"❌ Error listing backups: {e}")
    
    def cmd_status(self, args):
        """Show system status"""
        print("📊 Pulse System Status")
        print("=" * 25)
        
        # Configuration info
        print(f"⚙️ Config: {len(self.config.export_config())} settings loaded")
        print(f"🗂️ Data directory: {self.config.data_dir}")
        print(f"🔒 Privacy mode: {self.config.is_privacy_mode()}")
        print(f"⏰ Work hours: {self.config.work_hours_start}:00-{self.config.work_hours_end}:00")
        
        # Database info
        try:
            from ..database.connection import get_db_stats
            db_stats = get_db_stats()
            print(f"🗄️ Database: {db_stats.get('database_size_mb', 0)} MB, {db_stats.get('table_count', 0)} tables")
            if db_stats.get('row_counts'):
                print(f"📊 Records: {sum(db_stats['row_counts'].values())} total")
        except Exception as e:
            print(f"🗄️ Database: Error - {e}")
        
        # Todo generator info
        gen_stats = self.todo_generator.get_generation_stats()
        print(f"🧠 Todo generators: {gen_stats['total_generators']} active")
        print(f"🎯 ML available: {gen_stats['ml_available']}")
        
        # Settings info
        settings_summary = self.settings_manager.get_settings_summary()
        print(f"⚙️ User settings: {settings_summary['total_settings']} in {len(settings_summary['categories'])} categories")
        
        print(f"\\n✅ System operational")