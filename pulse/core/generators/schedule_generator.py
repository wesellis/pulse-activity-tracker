"""
Schedule-based todo generator
Generates todos based on schedule and upcoming events
"""

from datetime import datetime
from typing import Dict, List, Any
from .base_generator import BaseTodoGenerator


class ScheduleBasedGenerator(BaseTodoGenerator):
    """Generates todos based on schedule and upcoming events"""
    
    async def generate(self, activity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate schedule-based todos"""
        suggestions = []
        current_time = datetime.now()
        
        # End of day suggestions
        if current_time.hour >= 16:
            suggestions.append(self.create_todo(
                title='Prepare for tomorrow',
                description='Review tomorrow\'s calendar and prepare necessary materials',
                priority='medium',
                category='planning',
                confidence=0.7,
                source='schedule_pattern',
                estimated_minutes=15
            ))
            
            suggestions.append(self.create_todo(
                title='Update daily progress',
                description='Document today\'s accomplishments and update project status',
                priority='low',
                category='tracking',
                confidence=0.6,
                source='schedule_pattern',
                estimated_minutes=10
            ))
        
        # Start of day suggestions
        if current_time.hour <= 10:
            suggestions.append(self.create_todo(
                title='Review daily priorities',
                description='Check calendar, emails, and set focus for the day',
                priority='high',
                category='planning',
                confidence=0.9,
                source='schedule_pattern',
                estimated_minutes=15
            ))
        
        return suggestions