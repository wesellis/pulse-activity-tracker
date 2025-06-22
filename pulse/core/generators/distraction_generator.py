"""
Distraction and focus improvement generator
Generates todos to minimize distractions and improve focus
"""

from typing import Dict, List, Any
from .base_generator import BaseTodoGenerator


class DistractionTodoGenerator(BaseTodoGenerator):
    """Generates todos to handle distractions and improve focus"""
    
    def __init__(self, config):
        super().__init__(config)
        self.distraction_apps = [
            'discord', 'spotify', 'steam', 'netflix', 'youtube',
            'tiktok', 'instagram', 'facebook', 'twitter', 'reddit',
            'twitch', 'whatsapp', 'telegram', 'slack'
        ]
        self.focus_thresholds = {
            'high_distraction': 30,
            'low_focus': 50,
            'app_overload': 15
        }
    
    async def generate(self, activity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate distraction-related todos"""
        suggestions = []
        
        productivity_indicators = activity_data.get('productivity_indicators', {})
        distraction_score = productivity_indicators.get('distraction_score', 0)
        focus_score = productivity_indicators.get('focus_score', 100)
        
        # High distraction detection
        if distraction_score > self.focus_thresholds['high_distraction']:
            suggestions.extend(self._generate_distraction_reduction_todos(distraction_score))
        
        # Low focus detection
        if focus_score < self.focus_thresholds['low_focus']:
            suggestions.extend(self._generate_focus_improvement_todos(focus_score))
        
        # App overload detection
        session_data = activity_data.get('session_data', {})
        app_count = len(session_data.get('applications', {}))
        
        if app_count > self.focus_thresholds['app_overload']:
            suggestions.extend(self._generate_app_management_todos(app_count))
        
        # Social media detection
        suggestions.extend(self._check_social_media_usage(session_data))
        
        return suggestions
    
    def _generate_distraction_reduction_todos(self, distraction_score: float) -> List[Dict[str, Any]]:
        """Generate todos to reduce distractions"""
        suggestions = []
        
        suggestions.append(self.create_todo(
            title='Minimize distractions',
            description='Close social media tabs, silence notifications, and focus on one task.',
            priority='high',
            category='focus',
            confidence=0.85,
            source='distraction_analysis',
            estimated_minutes=5,
            distraction_level='high',
            metric_value=distraction_score
        ))
        
        suggestions.append(self.create_todo(
            title='Use website blocker',
            description='Enable website blocker for distracting sites for the next 2 hours.',
            priority='medium',
            category='focus',
            confidence=0.7,
            source='distraction_analysis',
            estimated_minutes=2,
            distraction_level='high'
        ))
        
        if distraction_score > 50:
            suggestions.append(self.create_todo(
                title='Take a digital detox break',
                description='Step away from all screens for 15 minutes to reset your focus.',
                priority='high',
                category='focus',
                confidence=0.8,
                source='distraction_analysis',
                estimated_minutes=15,
                distraction_level='severe'
            ))
        
        return suggestions
    
    def _generate_focus_improvement_todos(self, focus_score: float) -> List[Dict[str, Any]]:
        """Generate todos to improve focus"""
        suggestions = []
        
        suggestions.append(self.create_todo(
            title='Try the Pomodoro Technique',
            description='Work in focused 25-minute intervals with short breaks.',
            priority='medium',
            category='productivity',
            confidence=0.75,
            source='focus_improvement',
            estimated_minutes=25,
            focus_technique='pomodoro',
            metric_value=focus_score
        ))
        
        suggestions.append(self.create_todo(
            title='Create a focused work session',
            description='Set a specific goal for the next hour and work without interruptions.',
            priority='high',
            category='productivity',
            confidence=0.8,
            source='focus_improvement',
            estimated_minutes=60,
            focus_technique='deep_work'
        ))
        
        if focus_score < 30:
            suggestions.append(self.create_todo(
                title='Review and prioritize tasks',
                description='Your focus is very low. Take 10 minutes to clarify priorities and create a clear action plan.',
                priority='urgent',
                category='planning',
                confidence=0.9,
                source='focus_improvement',
                estimated_minutes=10,
                focus_technique='planning'
            ))
        
        return suggestions
    
    def _generate_app_management_todos(self, app_count: int) -> List[Dict[str, Any]]:
        """Generate todos for managing too many open applications"""
        suggestions = []
        
        suggestions.append(self.create_todo(
            title='Close unnecessary applications',
            description=f'You have {app_count} applications open. Close unused ones to improve system performance and focus.',
            priority='medium',
            category='focus',
            confidence=0.8,
            source='resource_optimization',
            estimated_minutes=5,
            app_count=app_count
        ))
        
        if app_count > 20:
            suggestions.append(self.create_todo(
                title='Restart your work session',
                description='Too many apps are running. Save your work, close everything, and start fresh with only essential apps.',
                priority='high',
                category='focus',
                confidence=0.85,
                source='resource_optimization',
                estimated_minutes=10,
                app_count=app_count
            ))
        
        return suggestions
    
    def _check_social_media_usage(self, session_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for social media usage and generate appropriate todos"""
        suggestions = []
        
        applications = session_data.get('applications', {})
        app_names = [app.lower() for app in applications.keys()]
        
        # Count distraction apps
        distraction_apps_found = [
            app for app in self.distraction_apps 
            if any(app in app_name for app_name in app_names)
        ]
        
        if len(distraction_apps_found) >= 3:
            suggestions.append(self.create_todo(
                title='Limit social media usage',
                description=f'Multiple distracting apps detected ({", ".join(distraction_apps_found[:3])}). Consider scheduling specific times for social media.',
                priority='medium',
                category='focus',
                confidence=0.7,
                source='social_media_detection',
                estimated_minutes=5,
                detected_apps=distraction_apps_found
            ))
        
        return suggestions