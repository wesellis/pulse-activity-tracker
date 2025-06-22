"""
Todo Generator - Intelligent task generation based on activity patterns
Uses machine learning and pattern recognition to suggest relevant todos
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import re

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available - using basic todo generation")

class TodoGenerator:
    """Generates intelligent todo suggestions based on user activity patterns"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Pattern learning components
        self.activity_patterns = {}
        self.todo_history = []
        self.completion_patterns = {}
        
        # Simple rule-based generators
        self.rule_generators = [
            self._generate_continuation_todos,
            self._generate_pattern_based_todos,
            self._generate_context_aware_todos,
            self._generate_schedule_based_todos,
            self._generate_break_reminders,
            self._generate_health_todos,
            self._generate_project_todos,
            self._generate_distraction_todos
        ]
        
        # Break tracking
        self.last_break_time = datetime.now()
        self.continuous_work_time = 0
        
        # Productivity thresholds
        self.productivity_thresholds = {
            'high': 80,
            'medium': 50,
            'low': 30
        }
    
    async def generate_suggestions(self, activity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate todo suggestions based on current activity"""
        suggestions = []
        
        try:
            # Run all generators
            for generator in self.rule_generators:
                new_suggestions = await generator(activity_data)
                suggestions.extend(new_suggestions)
            
            # Use ML for advanced suggestions if available
            if SKLEARN_AVAILABLE:
                ml_suggestions = await self._generate_ml_suggestions(activity_data)
                suggestions.extend(ml_suggestions)
            
            # Rank and filter suggestions
            ranked_suggestions = self._rank_suggestions(suggestions, activity_data)
            
            # Return top suggestions
            return ranked_suggestions[:10]
            
        except Exception as e:
            self.logger.error(f"Error generating suggestions: {e}")
            return []
    
    async def _generate_continuation_todos(self, activity_data: Dict[str, Any]) -> List[Dict]:
        """Generate todos for continuing interrupted or unfinished work"""
        suggestions = []
        
        # Check for recently accessed files that might need continuation
        session_data = activity_data.get('session_data', {})
        applications = session_data.get('applications', {})
        
        # Look for development work
        if any('code' in app.lower() or 'visual studio' in app.lower() for app in applications):
            suggestions.append({
                'title': 'Continue coding session',
                'description': 'Resume work on current development project',
                'priority': 'medium',
                'category': 'development',
                'confidence': 0.8,
                'source': 'continuation_pattern'
            })
        
        # Look for document editing
        if any('word' in app.lower() or 'docs' in app.lower() for app in applications):
            suggestions.append({
                'title': 'Finish document editing',
                'description': 'Complete current document or report',
                'priority': 'medium',
                'category': 'documentation',
                'confidence': 0.7,
                'source': 'continuation_pattern'
            })
        
        # Look for design work
        if any('figma' in app.lower() or 'photoshop' in app.lower() for app in applications):
            suggestions.append({
                'title': 'Continue design work',
                'description': 'Finish current design project or mockups',
                'priority': 'medium',
                'category': 'design',
                'confidence': 0.75,
                'source': 'continuation_pattern'
            })
        
        return suggestions
    
    async def _generate_pattern_based_todos(self, activity_data: Dict[str, Any]) -> List[Dict]:
        """Generate todos based on learned activity patterns"""
        suggestions = []
        current_time = datetime.now()
        
        # Day-of-week patterns
        weekday = current_time.weekday()
        
        if weekday == 0:  # Monday
            suggestions.append({
                'title': 'Weekly planning session',
                'description': 'Review goals and plan the week ahead',
                'priority': 'high',
                'category': 'planning',
                'confidence': 0.9,
                'source': 'weekly_pattern'
            })
        
        if weekday == 4:  # Friday
            suggestions.append({
                'title': 'Week wrap-up and review',
                'description': 'Summarize accomplishments and prepare weekly report',
                'priority': 'medium',
                'category': 'reporting',
                'confidence': 0.8,
                'source': 'weekly_pattern'
            })
        
        # Time-based patterns
        hour = current_time.hour
        
        if 9 <= hour <= 11:  # Morning productivity window
            suggestions.append({
                'title': 'Tackle high-focus task',
                'description': 'Work on most challenging or important task during peak hours',
                'priority': 'high',
                'category': 'productivity',
                'confidence': 0.7,
                'source': 'time_pattern'
            })
        
        if 13 <= hour <= 15:  # Post-lunch period
            suggestions.append({
                'title': 'Handle administrative tasks',
                'description': 'Process emails, update documentation, or handle routine tasks',
                'priority': 'low',
                'category': 'administrative',
                'confidence': 0.6,
                'source': 'time_pattern'
            })
        
        return suggestions
    
    async def _generate_context_aware_todos(self, activity_data: Dict[str, Any]) -> List[Dict]:
        """Generate todos based on current context and activity"""
        suggestions = []
        
        # Analyze productivity metrics
        productivity_indicators = activity_data.get('productivity_indicators', {})
        productivity_score = productivity_indicators.get('productivity_score', 0)
        
        if productivity_score < 50:  # Low productivity detected
            suggestions.append({
                'title': 'Take a productive break',
                'description': 'Step away from computer, stretch, or go for a short walk',
                'priority': 'medium',
                'category': 'wellness',
                'confidence': 0.8,
                'source': 'productivity_analysis'
            })
        
        # Check for multitasking (many apps open)
        session_data = activity_data.get('session_data', {})
        app_count = len(session_data.get('applications', {}))
        
        if app_count > 10:
            suggestions.append({
                'title': 'Minimize distractions',
                'description': 'Close unnecessary applications and focus on current task',
                'priority': 'medium',
                'category': 'focus',
                'confidence': 0.7,
                'source': 'distraction_detection'
            })
        
        # Look for communication app usage
        communication_apps = ['slack', 'teams', 'discord', 'zoom']
        if any(any(comm_app in app.lower() for comm_app in communication_apps) 
               for app in session_data.get('applications', {})):
            suggestions.append({
                'title': 'Follow up on communications',
                'description': 'Review and respond to important messages or action items',
                'priority': 'medium',
                'category': 'communication',
                'confidence': 0.6,
                'source': 'communication_pattern'
            })
        
        return suggestions
    
    async def _generate_schedule_based_todos(self, activity_data: Dict[str, Any]) -> List[Dict]:
        """Generate todos based on schedule and upcoming events"""
        suggestions = []
        current_time = datetime.now()
        
        # End of day suggestions
        if current_time.hour >= 16:
            suggestions.append({
                'title': 'Prepare for tomorrow',
                'description': 'Review tomorrow\'s calendar and prepare necessary materials',
                'priority': 'medium',
                'category': 'planning',
                'confidence': 0.7,
                'source': 'schedule_pattern'
            })
            
            suggestions.append({
                'title': 'Update daily progress',
                'description': 'Document today\'s accomplishments and update project status',
                'priority': 'low',
                'category': 'tracking',
                'confidence': 0.6,
                'source': 'schedule_pattern'
            })
        
        # Start of day suggestions
        if current_time.hour <= 10:
            suggestions.append({
                'title': 'Review daily priorities',
                'description': 'Check calendar, emails, and set focus for the day',
                'priority': 'high',
                'category': 'planning',
                'confidence': 0.9,
                'source': 'schedule_pattern'
            })
        
        return suggestions
    
    async def _generate_break_reminders(self, activity_data: Dict[str, Any]) -> List[Dict]:
        """Generate break reminders based on continuous work time"""
        suggestions = []
        
        # Check session duration
        session_data = activity_data.get('session_data', {})
        session_start = session_data.get('start_time')
        
        if session_start:
            # Calculate continuous work time
            if isinstance(session_start, str):
                session_start = datetime.fromisoformat(session_start.replace('Z', '+00:00'))
            elif hasattr(session_start, 'isoformat'):
                pass  # Already datetime
            else:
                return suggestions
            
            work_duration = (datetime.now() - session_start).total_seconds() / 60
            
            # Check idle periods
            idle_periods = session_data.get('idle_periods', [])
            recent_break = False
            for period in idle_periods:
                if (datetime.now() - period.get('start', datetime.min)).total_seconds() < 1800:  # 30 min
                    recent_break = True
                    break
            
            if not recent_break:
                if work_duration > 90:  # 90 minutes continuous work
                    suggestions.append({
                        'title': '🚨 Take a mandatory break',
                        'description': 'You\'ve been working for over 90 minutes. Stand up, stretch, and rest your eyes for 10-15 minutes.',
                        'priority': 'urgent',
                        'category': 'health',
                        'confidence': 0.95,
                        'source': 'break_reminder',
                        'estimated_minutes': 15
                    })
                elif work_duration > 60:  # 60 minutes
                    suggestions.append({
                        'title': 'Time for a short break',
                        'description': 'You\'ve been focused for an hour. Take a 5-10 minute break to maintain productivity.',
                        'priority': 'high',
                        'category': 'health',
                        'confidence': 0.85,
                        'source': 'break_reminder',
                        'estimated_minutes': 10
                    })
                elif work_duration > 25:  # Pomodoro interval
                    suggestions.append({
                        'title': 'Pomodoro break time',
                        'description': 'Complete your 25-minute focus session with a 5-minute break.',
                        'priority': 'medium',
                        'category': 'health',
                        'confidence': 0.7,
                        'source': 'break_reminder',
                        'estimated_minutes': 5
                    })
        
        return suggestions
    
    async def _generate_health_todos(self, activity_data: Dict[str, Any]) -> List[Dict]:
        """Generate health and wellness related todos"""
        suggestions = []
        current_time = datetime.now()
        hour = current_time.hour
        
        # Hydration reminder
        if hour % 2 == 0:  # Every 2 hours
            suggestions.append({
                'title': 'Stay hydrated 💧',
                'description': 'Drink a glass of water to maintain hydration and focus.',
                'priority': 'low',
                'category': 'health',
                'confidence': 0.6,
                'source': 'health_reminder',
                'estimated_minutes': 2
            })
        
        # Eye rest reminder
        productivity_indicators = activity_data.get('productivity_indicators', {})
        screen_time = productivity_indicators.get('active_time_minutes', 0)
        
        if screen_time > 120:  # 2 hours of screen time
            suggestions.append({
                'title': 'Rest your eyes (20-20-20 rule)',
                'description': 'Look at something 20 feet away for 20 seconds to reduce eye strain.',
                'priority': 'medium',
                'category': 'health',
                'confidence': 0.8,
                'source': 'health_reminder',
                'estimated_minutes': 1
            })
        
        # Posture check
        if hour in [10, 14, 16]:  # Specific times for posture checks
            suggestions.append({
                'title': 'Check your posture',
                'description': 'Adjust your sitting position, straighten your back, and relax your shoulders.',
                'priority': 'low',
                'category': 'health',
                'confidence': 0.5,
                'source': 'health_reminder',
                'estimated_minutes': 1
            })
        
        # Lunch reminder
        if 12 <= hour <= 13 and current_time.minute < 30:
            suggestions.append({
                'title': 'Take a lunch break',
                'description': 'Step away from work and have a proper meal.',
                'priority': 'high',
                'category': 'health',
                'confidence': 0.9,
                'source': 'health_reminder',
                'estimated_minutes': 30
            })
        
        return suggestions
    
    async def _generate_project_todos(self, activity_data: Dict[str, Any]) -> List[Dict]:
        """Generate project-specific todos based on recent activity"""
        suggestions = []
        
        # Analyze recent applications and files
        session_data = activity_data.get('session_data', {})
        applications = session_data.get('applications', {})
        
        # Git-related todos
        if any('git' in app.lower() or 'sourcetree' in app.lower() for app in applications):
            suggestions.append({
                'title': 'Commit your changes',
                'description': 'Review and commit pending changes to version control.',
                'priority': 'high',
                'category': 'development',
                'confidence': 0.8,
                'source': 'project_pattern',
                'estimated_minutes': 10
            })
        
        # Testing todos
        if any('test' in app.lower() or 'pytest' in app.lower() for app in applications):
            suggestions.append({
                'title': 'Run test suite',
                'description': 'Execute tests to ensure code quality before pushing.',
                'priority': 'high',
                'category': 'development',
                'confidence': 0.75,
                'source': 'project_pattern',
                'estimated_minutes': 15
            })
        
        # Documentation todos
        productivity_indicators = activity_data.get('productivity_indicators', {})
        category_breakdown = productivity_indicators.get('category_breakdown', {})
        
        if category_breakdown.get('development', 0) > 60:  # Over 60 min of development
            suggestions.append({
                'title': 'Update documentation',
                'description': 'Document recent code changes and update README if needed.',
                'priority': 'medium',
                'category': 'documentation',
                'confidence': 0.7,
                'source': 'project_pattern',
                'estimated_minutes': 20
            })
        
        # Code review
        if 'github' in ' '.join(applications).lower() or 'gitlab' in ' '.join(applications).lower():
            suggestions.append({
                'title': 'Review pull requests',
                'description': 'Check and review pending pull requests from team members.',
                'priority': 'medium',
                'category': 'collaboration',
                'confidence': 0.65,
                'source': 'project_pattern',
                'estimated_minutes': 30
            })
        
        return suggestions
    
    async def _generate_distraction_todos(self, activity_data: Dict[str, Any]) -> List[Dict]:
        """Generate todos to handle distractions and improve focus"""
        suggestions = []
        
        productivity_indicators = activity_data.get('productivity_indicators', {})
        distraction_score = productivity_indicators.get('distraction_score', 0)
        focus_score = productivity_indicators.get('focus_score', 100)
        
        # High distraction detected
        if distraction_score > 30:
            suggestions.append({
                'title': 'Minimize distractions',
                'description': 'Close social media tabs, silence notifications, and focus on one task.',
                'priority': 'high',
                'category': 'focus',
                'confidence': 0.85,
                'source': 'distraction_analysis',
                'estimated_minutes': 5
            })
            
            suggestions.append({
                'title': 'Use website blocker',
                'description': 'Enable website blocker for distracting sites for the next 2 hours.',
                'priority': 'medium',
                'category': 'focus',
                'confidence': 0.7,
                'source': 'distraction_analysis',
                'estimated_minutes': 2
            })
        
        # Low focus score
        if focus_score < 50:
            suggestions.append({
                'title': 'Try the Pomodoro Technique',
                'description': 'Work in focused 25-minute intervals with short breaks.',
                'priority': 'medium',
                'category': 'productivity',
                'confidence': 0.75,
                'source': 'focus_improvement',
                'estimated_minutes': 25
            })
            
            suggestions.append({
                'title': 'Create a focused work session',
                'description': 'Set a specific goal for the next hour and work without interruptions.',
                'priority': 'high',
                'category': 'productivity',
                'confidence': 0.8,
                'source': 'focus_improvement',
                'estimated_minutes': 60
            })
        
        # App switching detection
        session_data = activity_data.get('session_data', {})
        app_count = len(session_data.get('applications', {}))
        
        if app_count > 15:
            suggestions.append({
                'title': 'Close unnecessary applications',
                'description': f'You have {app_count} applications open. Close unused ones to improve system performance and focus.',
                'priority': 'medium',
                'category': 'focus',
                'confidence': 0.8,
                'source': 'resource_optimization',
                'estimated_minutes': 5
            })
        
        return suggestions
    
    async def _generate_ml_suggestions(self, activity_data: Dict[str, Any]) -> List[Dict]:
        """Generate suggestions using machine learning (if available)"""
        if not SKLEARN_AVAILABLE:
            return []
        
        suggestions = []
        
        try:
            # This would use historical data to train models
            # For now, return placeholder ML-based suggestions
            suggestions.append({
                'title': 'ML-suggested task',
                'description': 'Task suggested by machine learning analysis of your patterns',
                'priority': 'medium',
                'category': 'ml_generated',
                'confidence': 0.6,
                'source': 'machine_learning'
            })
            
        except Exception as e:
            self.logger.error(f"Error in ML suggestion generation: {e}")
        
        return suggestions
    
    def _rank_suggestions(self, suggestions: List[Dict], activity_data: Dict[str, Any]) -> List[Dict]:
        """Rank suggestions by relevance and confidence"""
        if not suggestions:
            return []
        
        # Calculate ranking score for each suggestion
        for suggestion in suggestions:
            score = self._calculate_suggestion_score(suggestion, activity_data)
            suggestion['ranking_score'] = score
        
        # Sort by ranking score (highest first)
        ranked = sorted(suggestions, key=lambda x: x.get('ranking_score', 0), reverse=True)
        
        # Remove duplicates based on title similarity
        unique_suggestions = self._remove_similar_suggestions(ranked)
        
        return unique_suggestions
    
    def _calculate_suggestion_score(self, suggestion: Dict, activity_data: Dict[str, Any]) -> float:
        """Calculate relevance score for a suggestion"""
        score = 0.0
        
        # Base confidence score
        confidence = suggestion.get('confidence', 0.5)
        score += confidence * 100
        
        # Priority weighting
        priority_weights = {'high': 30, 'medium': 20, 'low': 10}
        priority = suggestion.get('priority', 'medium')
        score += priority_weights.get(priority, 20)
        
        # Time relevance (prefer recent patterns)
        current_hour = datetime.now().hour
        if 'time_pattern' in suggestion.get('source', ''):
            if 9 <= current_hour <= 17:  # Work hours
                score += 20
        
        # Category relevance based on current activity
        session_data = activity_data.get('session_data', {})
        applications = session_data.get('applications', {})
        
        category = suggestion.get('category', '')
        if category == 'development' and any('code' in app.lower() for app in applications):
            score += 25
        elif category == 'communication' and any('slack' in app.lower() or 'teams' in app.lower() for app in applications):
            score += 25
        
        return score
    
    def _remove_similar_suggestions(self, suggestions: List[Dict]) -> List[Dict]:
        """Remove suggestions with similar titles or descriptions"""
        unique_suggestions = []
        seen_titles = set()
        
        for suggestion in suggestions:
            title = suggestion.get('title', '').lower()
            
            # Simple similarity check - could be improved with fuzzy matching
            is_similar = False
            for seen_title in seen_titles:
                if self._calculate_similarity(title, seen_title) > 0.8:
                    is_similar = True
                    break
            
            if not is_similar:
                unique_suggestions.append(suggestion)
                seen_titles.add(title)
        
        return unique_suggestions
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def learn_from_completion(self, todo: Dict[str, Any], completion_context: Dict[str, Any]):
        """Learn from completed todos to improve future suggestions"""
        try:
            # Store completion pattern for future learning
            pattern = {
                'todo': todo,
                'context': completion_context,
                'completed_at': datetime.now().isoformat(),
                'time_to_complete': completion_context.get('time_to_complete', 0)
            }
            
            self.completion_patterns[todo.get('id', '')] = pattern
            self.logger.info(f"Learned from completed todo: {todo.get('title', 'Unknown')}")
            
        except Exception as e:
            self.logger.error(f"Error learning from completion: {e}")
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get statistics about todo generation performance"""
        return {
            'total_patterns': len(self.completion_patterns),
            'generators_active': len(self.rule_generators),
            'ml_available': SKLEARN_AVAILABLE,
            'last_generation': datetime.now().isoformat()
        }
