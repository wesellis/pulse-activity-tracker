"""
Context-aware todo generator
Generates todos based on current context and activity state
"""

from typing import Dict, List, Any
from .base_generator import BaseTodoGenerator


class ContextAwareGenerator(BaseTodoGenerator):
    """Generates todos based on current context and activity"""
    
    async def generate(self, activity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate context-aware todos"""
        suggestions = []
        
        # Analyze productivity metrics
        productivity_indicators = activity_data.get('productivity_indicators', {})
        productivity_score = productivity_indicators.get('productivity_score', 0)
        
        if productivity_score < 50:
            suggestions.append(self.create_todo(
                title='Take a productive break',
                description='Step away from computer, stretch, or go for a short walk',
                priority='medium',
                category='wellness',
                confidence=0.8,
                source='productivity_analysis',
                estimated_minutes=10
            ))
        
        # Check for multitasking
        session_data = activity_data.get('session_data', {})
        app_count = len(session_data.get('applications', {}))
        
        if app_count > 10:
            suggestions.append(self.create_todo(
                title='Minimize distractions',
                description='Close unnecessary applications and focus on current task',
                priority='medium',
                category='focus',
                confidence=0.7,
                source='distraction_detection',
                estimated_minutes=5
            ))
        
        # Communication pattern detection
        communication_apps = ['slack', 'teams', 'discord', 'zoom']
        applications = session_data.get('applications', {})
        
        if any(any(comm_app in app.lower() for comm_app in communication_apps) 
               for app in applications):
            suggestions.append(self.create_todo(
                title='Follow up on communications',
                description='Review and respond to important messages or action items',
                priority='medium',
                category='communication',
                confidence=0.6,
                source='communication_pattern',
                estimated_minutes=15
            ))
        
        return suggestions