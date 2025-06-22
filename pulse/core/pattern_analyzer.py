"""
Advanced Pattern Analysis Engine for Pulse Activity Tracker
Detects and analyzes user patterns to generate intelligent insights and recommendations
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import logging
from pathlib import Path
import sqlite3
import hashlib

from ..utils.config import Config


class TimePatternAnalyzer:
    """Analyzes time-based patterns in user activity"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def analyze_productive_hours(self, activity_data: List[Dict]) -> Dict[str, Any]:
        """Analyze most productive hours of the day"""
        if not activity_data:
            return {}
        
        hourly_productivity = defaultdict(list)
        
        for activity in activity_data:
            timestamp = activity.get('timestamp')
            productivity = activity.get('productivity_score', 0)
            
            if timestamp and productivity:
                try:
                    if isinstance(timestamp, str):
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        dt = timestamp
                    
                    hour = dt.hour
                    hourly_productivity[hour].append(productivity)
                except Exception as e:
                    self.logger.warning(f"Failed to parse timestamp {timestamp}: {e}")
                    continue
        
        # Calculate average productivity per hour
        hourly_averages = {}
        for hour, scores in hourly_productivity.items():
            hourly_averages[hour] = sum(scores) / len(scores) if scores else 0
        
        # Find peak productivity hours
        if hourly_averages:
            peak_hour = max(hourly_averages.keys(), key=lambda h: hourly_averages[h])
            low_hour = min(hourly_averages.keys(), key=lambda h: hourly_averages[h])
            
            return {
                'hourly_productivity': hourly_averages,
                'peak_hour': peak_hour,
                'peak_productivity': hourly_averages[peak_hour],
                'low_hour': low_hour,
                'low_productivity': hourly_averages[low_hour],
                'optimal_range': self._find_optimal_range(hourly_averages),
                'energy_pattern': self._classify_energy_pattern(hourly_averages)
            }
        
        return {}
    
    def _find_optimal_range(self, hourly_averages: Dict[int, float]) -> Dict[str, Any]:
        """Find the optimal productive hour range"""
        if not hourly_averages:
            return {}
        
        # Sort hours by productivity
        sorted_hours = sorted(hourly_averages.items(), key=lambda x: x[1], reverse=True)
        
        # Take top 4 hours as optimal range
        top_hours = sorted([hour for hour, _ in sorted_hours[:4]])
        
        if top_hours:
            return {
                'start_hour': min(top_hours),
                'end_hour': max(top_hours),
                'duration': max(top_hours) - min(top_hours) + 1,
                'avg_productivity': sum(hourly_averages[h] for h in top_hours) / len(top_hours)
            }
        
        return {}
    
    def _classify_energy_pattern(self, hourly_averages: Dict[int, float]) -> str:
        """Classify user's energy pattern (morning/afternoon/evening person)"""
        if not hourly_averages:
            return 'unknown'
        
        morning_avg = sum(hourly_averages.get(h, 0) for h in range(6, 12)) / 6
        afternoon_avg = sum(hourly_averages.get(h, 0) for h in range(12, 18)) / 6
        evening_avg = sum(hourly_averages.get(h, 0) for h in range(18, 24)) / 6
        
        patterns = {'morning': morning_avg, 'afternoon': afternoon_avg, 'evening': evening_avg}
        return max(patterns.keys(), key=lambda k: patterns[k])
    
    def analyze_weekly_patterns(self, activity_data: List[Dict]) -> Dict[str, Any]:
        """Analyze weekly productivity patterns"""
        if not activity_data:
            return {}
        
        daily_productivity = defaultdict(list)
        
        for activity in activity_data:
            timestamp = activity.get('timestamp')
            productivity = activity.get('productivity_score', 0)
            
            if timestamp and productivity:
                try:
                    if isinstance(timestamp, str):
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        dt = timestamp
                    
                    weekday = dt.strftime('%A')
                    daily_productivity[weekday].append(productivity)
                except Exception as e:
                    self.logger.warning(f"Failed to parse timestamp {timestamp}: {e}")
                    continue
        
        # Calculate daily averages
        daily_averages = {}
        for day, scores in daily_productivity.items():
            daily_averages[day] = sum(scores) / len(scores) if scores else 0
        
        if daily_averages:
            best_day = max(daily_averages.keys(), key=lambda d: daily_averages[d])
            worst_day = min(daily_averages.keys(), key=lambda d: daily_averages[d])
            
            return {
                'daily_productivity': daily_averages,
                'best_day': best_day,
                'best_productivity': daily_averages[best_day],
                'worst_day': worst_day,
                'worst_productivity': daily_averages[worst_day],
                'weekly_trend': self._analyze_weekly_trend(daily_averages)
            }
        
        return {}
    
    def _analyze_weekly_trend(self, daily_averages: Dict[str, float]) -> str:
        """Analyze weekly productivity trend"""
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Calculate trend from Monday to Friday
        weekday_scores = [daily_averages.get(day, 0) for day in days_order[:5]]
        
        if len(weekday_scores) >= 2:
            if weekday_scores[-1] > weekday_scores[0]:
                return 'improving'
            elif weekday_scores[-1] < weekday_scores[0]:
                return 'declining'
            else:
                return 'stable'
        
        return 'insufficient_data'


class ApplicationPatternAnalyzer:
    """Analyzes application usage patterns"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def analyze_application_usage(self, activity_data: List[Dict]) -> Dict[str, Any]:
        """Analyze application usage patterns"""
        if not activity_data:
            return {}
        
        app_usage = defaultdict(lambda: {'total_time': 0, 'sessions': 0, 'productivity_scores': []})
        app_sequences = []
        
        for activity in activity_data:
            app_name = activity.get('app_name', 'Unknown')
            duration = activity.get('duration', 0)
            productivity = activity.get('productivity_score', 0)
            
            if app_name and app_name != 'Unknown':
                app_usage[app_name]['total_time'] += duration
                app_usage[app_name]['sessions'] += 1
                app_usage[app_name]['productivity_scores'].append(productivity)
                app_sequences.append(app_name)
        
        # Calculate app statistics
        app_stats = {}
        for app, data in app_usage.items():
            avg_productivity = sum(data['productivity_scores']) / len(data['productivity_scores']) if data['productivity_scores'] else 0
            app_stats[app] = {
                'total_time': data['total_time'],
                'sessions': data['sessions'],
                'avg_session_length': data['total_time'] / data['sessions'] if data['sessions'] > 0 else 0,
                'avg_productivity': avg_productivity,
                'category': self._categorize_application(app)
            }
        
        # Analyze workflow sequences
        sequences = self._analyze_sequences(app_sequences)
        
        return {
            'application_stats': app_stats,
            'most_used_apps': self._get_top_apps(app_stats, 'total_time'),
            'most_productive_apps': self._get_top_apps(app_stats, 'avg_productivity'),
            'workflow_sequences': sequences,
            'productivity_by_category': self._analyze_by_category(app_stats)
        }
    
    def _categorize_application(self, app_name: str) -> str:
        """Categorize application by type"""
        app_name_lower = app_name.lower()
        
        categories = {
            'development': ['code', 'pycharm', 'intellij', 'eclipse', 'atom', 'sublime', 'vim', 'emacs', 'git'],
            'communication': ['slack', 'teams', 'zoom', 'discord', 'telegram', 'whatsapp', 'skype'],
            'browser': ['chrome', 'firefox', 'safari', 'edge', 'brave'],
            'office': ['word', 'excel', 'powerpoint', 'outlook', 'notion', 'obsidian'],
            'design': ['photoshop', 'illustrator', 'figma', 'sketch', 'canva'],
            'entertainment': ['spotify', 'youtube', 'netflix', 'games', 'steam'],
            'system': ['explorer', 'finder', 'terminal', 'cmd', 'powershell']
        }
        
        for category, keywords in categories.items():
            if any(keyword in app_name_lower for keyword in keywords):
                return category
        
        return 'other'
    
    def _get_top_apps(self, app_stats: Dict[str, Dict], metric: str, limit: int = 5) -> List[Tuple[str, float]]:
        """Get top applications by specified metric"""
        return sorted(
            [(app, data[metric]) for app, data in app_stats.items()],
            key=lambda x: x[1],
            reverse=True
        )[:limit]
    
    def _analyze_sequences(self, app_sequences: List[str]) -> Dict[str, Any]:
        """Analyze application usage sequences"""
        if len(app_sequences) < 2:
            return {}
        
        # Find common transitions
        transitions = Counter()
        for i in range(len(app_sequences) - 1):
            transition = (app_sequences[i], app_sequences[i + 1])
            transitions[transition] += 1
        
        # Find common patterns (3-app sequences)
        patterns = Counter()
        for i in range(len(app_sequences) - 2):
            pattern = tuple(app_sequences[i:i+3])
            patterns[pattern] += 1
        
        return {
            'common_transitions': transitions.most_common(10),
            'common_patterns': patterns.most_common(5),
            'total_transitions': len(app_sequences) - 1
        }
    
    def _analyze_by_category(self, app_stats: Dict[str, Dict]) -> Dict[str, Dict]:
        """Analyze productivity by application category"""
        category_stats = defaultdict(lambda: {'total_time': 0, 'productivity_scores': []})
        
        for app, data in app_stats.items():
            category = data['category']
            category_stats[category]['total_time'] += data['total_time']
            category_stats[category]['productivity_scores'].append(data['avg_productivity'])
        
        # Calculate category averages
        result = {}
        for category, data in category_stats.items():
            avg_productivity = sum(data['productivity_scores']) / len(data['productivity_scores']) if data['productivity_scores'] else 0
            result[category] = {
                'total_time': data['total_time'],
                'avg_productivity': avg_productivity,
                'app_count': len(data['productivity_scores'])
            }
        
        return result


class FileAccessAnalyzer:
    """Analyzes file access patterns for project continuity"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.tracked_extensions = {
            '.py', '.js', '.ts', '.html', '.css', '.java', '.cpp', '.c',
            '.md', '.txt', '.doc', '.docx', '.pdf', '.json', '.xml', '.yml', '.yaml'
        }
    
    def analyze_file_patterns(self, file_access_data: List[Dict]) -> Dict[str, Any]:
        """Analyze file access patterns"""
        if not file_access_data:
            return {}
        
        file_stats = defaultdict(lambda: {
            'access_count': 0, 'last_accessed': None, 'total_time': 0,
            'modification_count': 0, 'project': None
        })
        
        project_stats = defaultdict(lambda: {
            'files': set(), 'total_time': 0, 'last_activity': None
        })
        
        for access in file_access_data:
            file_path = access.get('file_path', '')
            timestamp = access.get('timestamp')
            duration = access.get('duration', 0)
            action = access.get('action', 'read')  # read, write, create, delete
            
            if file_path and self._should_track_file(file_path):
                file_stats[file_path]['access_count'] += 1
                file_stats[file_path]['total_time'] += duration
                file_stats[file_path]['last_accessed'] = timestamp
                
                if action in ['write', 'create']:
                    file_stats[file_path]['modification_count'] += 1
                
                # Determine project
                project = self._extract_project_name(file_path)
                file_stats[file_path]['project'] = project
                
                if project:
                    project_stats[project]['files'].add(file_path)
                    project_stats[project]['total_time'] += duration
                    project_stats[project]['last_activity'] = timestamp
        
        # Convert sets to lists for JSON serialization
        for project in project_stats:
            project_stats[project]['files'] = list(project_stats[project]['files'])
            project_stats[project]['file_count'] = len(project_stats[project]['files'])
        
        return {
            'file_statistics': dict(file_stats),
            'project_statistics': dict(project_stats),
            'unfinished_work': self._detect_unfinished_work(file_stats),
            'active_projects': self._identify_active_projects(project_stats),
            'file_type_analysis': self._analyze_by_file_type(file_stats)
        }
    
    def _should_track_file(self, file_path: str) -> bool:
        """Check if file should be tracked based on extension"""
        path_obj = Path(file_path)
        return path_obj.suffix.lower() in self.tracked_extensions
    
    def _extract_project_name(self, file_path: str) -> Optional[str]:
        """Extract project name from file path"""
        path_obj = Path(file_path)
        
        # Look for common project indicators
        parts = path_obj.parts
        
        # Check for git repositories
        for i, part in enumerate(parts):
            if part == '.git' and i > 0:
                return parts[i-1]
        
        # Check for common project directories
        project_indicators = ['src', 'lib', 'app', 'components', 'modules']
        for i, part in enumerate(parts):
            if part.lower() in project_indicators and i > 0:
                return parts[i-1]
        
        # Fallback to parent directory of file
        if len(parts) >= 2:
            return parts[-2]
        
        return None
    
    def _detect_unfinished_work(self, file_stats: Dict[str, Dict]) -> List[Dict]:
        """Detect potentially unfinished work based on access patterns"""
        unfinished = []
        current_time = datetime.now()
        
        for file_path, stats in file_stats.items():
            last_accessed = stats.get('last_accessed')
            modification_count = stats.get('modification_count', 0)
            
            if last_accessed and modification_count > 0:
                try:
                    if isinstance(last_accessed, str):
                        last_dt = datetime.fromisoformat(last_accessed.replace('Z', '+00:00'))
                    else:
                        last_dt = last_accessed
                    
                    # If modified recently but not accessed in last 24 hours
                    hours_since_access = (current_time - last_dt).total_seconds() / 3600
                    
                    if 24 <= hours_since_access <= 168:  # 1-7 days
                        unfinished.append({
                            'file_path': file_path,
                            'project': stats.get('project'),
                            'last_accessed': last_accessed,
                            'hours_since_access': hours_since_access,
                            'modification_count': modification_count,
                            'priority': self._calculate_priority(stats)
                        })
                except Exception as e:
                    self.logger.warning(f"Failed to parse timestamp {last_accessed}: {e}")
                    continue
        
        return sorted(unfinished, key=lambda x: x['priority'], reverse=True)
    
    def _identify_active_projects(self, project_stats: Dict[str, Dict]) -> List[Dict]:
        """Identify currently active projects"""
        active_projects = []
        current_time = datetime.now()
        
        for project, stats in project_stats.items():
            last_activity = stats.get('last_activity')
            
            if last_activity:
                try:
                    if isinstance(last_activity, str):
                        last_dt = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                    else:
                        last_dt = last_activity
                    
                    hours_since_activity = (current_time - last_dt).total_seconds() / 3600
                    
                    if hours_since_activity <= 72:  # Active in last 3 days
                        active_projects.append({
                            'project': project,
                            'file_count': stats.get('file_count', 0),
                            'total_time': stats.get('total_time', 0),
                            'last_activity': last_activity,
                            'hours_since_activity': hours_since_activity,
                            'activity_level': self._classify_activity_level(hours_since_activity, stats.get('total_time', 0))
                        })
                except Exception as e:
                    self.logger.warning(f"Failed to parse timestamp {last_activity}: {e}")
                    continue
        
        return sorted(active_projects, key=lambda x: x['total_time'], reverse=True)
    
    def _calculate_priority(self, file_stats: Dict) -> float:
        """Calculate priority score for unfinished work"""
        base_score = file_stats.get('modification_count', 0) * 10
        time_bonus = min(file_stats.get('total_time', 0) / 60, 50)  # Max 50 points for time
        return base_score + time_bonus
    
    def _classify_activity_level(self, hours_since: float, total_time: float) -> str:
        """Classify project activity level"""
        if hours_since <= 8:
            return 'very_active'
        elif hours_since <= 24:
            return 'active'
        elif hours_since <= 48:
            return 'moderate'
        else:
            return 'low'
    
    def _analyze_by_file_type(self, file_stats: Dict[str, Dict]) -> Dict[str, Dict]:
        """Analyze patterns by file type"""
        type_stats = defaultdict(lambda: {
            'file_count': 0, 'total_time': 0, 'total_modifications': 0
        })
        
        for file_path, stats in file_stats.items():
            extension = Path(file_path).suffix.lower()
            if extension:
                type_stats[extension]['file_count'] += 1
                type_stats[extension]['total_time'] += stats.get('total_time', 0)
                type_stats[extension]['total_modifications'] += stats.get('modification_count', 0)
        
        return dict(type_stats)


class PatternAnalyzer:
    """Main pattern analyzer that coordinates all pattern analysis"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize sub-analyzers
        self.time_analyzer = TimePatternAnalyzer(config)
        self.app_analyzer = ApplicationPatternAnalyzer(config)
        self.file_analyzer = FileAccessAnalyzer(config)
    
    def analyze_all_patterns(
        self,
        activity_data: List[Dict],
        file_access_data: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Perform comprehensive pattern analysis"""
        
        patterns = {
            'analysis_timestamp': datetime.now().isoformat(),
            'data_period': self._calculate_data_period(activity_data),
            'time_patterns': {},
            'application_patterns': {},
            'file_patterns': {},
            'insights': [],
            'recommendations': []
        }
        
        try:
            # Analyze time patterns
            patterns['time_patterns'] = self.time_analyzer.analyze_productive_hours(activity_data)
            weekly_patterns = self.time_analyzer.analyze_weekly_patterns(activity_data)
            patterns['time_patterns'].update(weekly_patterns)
            
            # Analyze application patterns
            patterns['application_patterns'] = self.app_analyzer.analyze_application_usage(activity_data)
            
            # Analyze file patterns if data is available
            if file_access_data:
                patterns['file_patterns'] = self.file_analyzer.analyze_file_patterns(file_access_data)
            
            # Generate insights and recommendations
            patterns['insights'] = self._generate_pattern_insights(patterns)
            patterns['recommendations'] = self._generate_pattern_recommendations(patterns)
            
        except Exception as e:
            self.logger.error(f"Error during pattern analysis: {e}")
            patterns['error'] = str(e)
        
        return patterns
    
    def _calculate_data_period(self, activity_data: List[Dict]) -> Dict[str, Any]:
        """Calculate the time period covered by the data"""
        if not activity_data:
            return {}
        
        timestamps = []
        for activity in activity_data:
            timestamp = activity.get('timestamp')
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        dt = timestamp
                    timestamps.append(dt)
                except Exception:
                    continue
        
        if timestamps:
            return {
                'start_date': min(timestamps).isoformat(),
                'end_date': max(timestamps).isoformat(),
                'duration_days': (max(timestamps) - min(timestamps)).days + 1,
                'data_points': len(activity_data)
            }
        
        return {}
    
    def _generate_pattern_insights(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate insights based on detected patterns"""
        insights = []
        
        # Time pattern insights
        time_patterns = patterns.get('time_patterns', {})
        if time_patterns.get('energy_pattern'):
            energy_type = time_patterns['energy_pattern']
            insights.append(f"🕐 You're a {energy_type} person - your productivity peaks during {energy_type} hours")
        
        if time_patterns.get('peak_hour') is not None:
            peak_hour = time_patterns['peak_hour']
            insights.append(f"⏰ Your most productive hour is {peak_hour}:00 - schedule important tasks then")
        
        # Application pattern insights
        app_patterns = patterns.get('application_patterns', {})
        most_used = app_patterns.get('most_used_apps', [])
        if most_used:
            top_app = most_used[0][0]
            insights.append(f"💻 {top_app} is your most-used application - consider optimizing your workflow there")
        
        productivity_by_cat = app_patterns.get('productivity_by_category', {})
        if productivity_by_cat:
            best_category = max(productivity_by_cat.keys(), key=lambda k: productivity_by_cat[k]['avg_productivity'])
            insights.append(f"🎯 You're most productive when using {best_category} applications")
        
        # File pattern insights
        file_patterns = patterns.get('file_patterns', {})
        unfinished_work = file_patterns.get('unfinished_work', [])
        if unfinished_work:
            insights.append(f"📁 You have {len(unfinished_work)} files with unfinished work - consider prioritizing them")
        
        active_projects = file_patterns.get('active_projects', [])
        if len(active_projects) > 3:
            insights.append(f"🔄 You're juggling {len(active_projects)} projects - consider focusing on fewer at a time")
        
        return insights
    
    def _generate_pattern_recommendations(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on patterns"""
        recommendations = []
        
        # Time-based recommendations
        time_patterns = patterns.get('time_patterns', {})
        optimal_range = time_patterns.get('optimal_range', {})
        if optimal_range:
            start_hour = optimal_range.get('start_hour', 9)
            end_hour = optimal_range.get('end_hour', 17)
            recommendations.append(f"🎯 Schedule your most important work between {start_hour}:00-{end_hour}:00")
        
        energy_pattern = time_patterns.get('energy_pattern')
        if energy_pattern == 'morning':
            recommendations.append("🌅 Front-load your day with challenging tasks - you're a morning person")
        elif energy_pattern == 'evening':
            recommendations.append("🌙 Save complex work for later in the day - you're an evening person")
        
        # Application recommendations
        app_patterns = patterns.get('application_patterns', {})
        sequences = app_patterns.get('workflow_sequences', {})
        common_transitions = sequences.get('common_transitions', [])
        if common_transitions:
            top_transition = common_transitions[0][0]
            recommendations.append(f"⚡ Create shortcuts for your common workflow: {top_transition[0]} → {top_transition[1]}")
        
        # File management recommendations
        file_patterns = patterns.get('file_patterns', {})
        unfinished_work = file_patterns.get('unfinished_work', [])
        if unfinished_work:
            top_unfinished = unfinished_work[0]
            recommendations.append(f"📝 Resume work on {Path(top_unfinished['file_path']).name} - it's been {int(top_unfinished['hours_since_access'])}h since last access")
        
        active_projects = file_patterns.get('active_projects', [])
        if len(active_projects) > 2:
            recommendations.append("🎯 Consider time-blocking for different projects to reduce context switching")
        
        return recommendations
    
    def get_pattern_summary(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a concise summary of all patterns"""
        # Handle most_used_app extraction safely
        most_used_app = None
        most_used_apps = patterns.get('application_patterns', {}).get('most_used_apps', [])
        if most_used_apps and isinstance(most_used_apps[0], tuple) and len(most_used_apps[0]) >= 1:
            most_used_app = most_used_apps[0][0]
        
        return {
            'productivity_peak': patterns.get('time_patterns', {}).get('peak_hour'),
            'energy_type': patterns.get('time_patterns', {}).get('energy_pattern'),
            'most_used_app': most_used_app,
            'active_projects_count': len(patterns.get('file_patterns', {}).get('active_projects', [])),
            'unfinished_work_count': len(patterns.get('file_patterns', {}).get('unfinished_work', [])),
            'insights_count': len(patterns.get('insights', [])),
            'recommendations_count': len(patterns.get('recommendations', []))
        }