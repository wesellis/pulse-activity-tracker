"""
Break reminder generator
Generates todos for taking breaks based on work patterns
"""

from datetime import datetime
from typing import Dict, List, Any
from .base_generator import BaseTodoGenerator


class BreakReminderGenerator(BaseTodoGenerator):
    """Generates break reminders based on continuous work time"""
    
    def __init__(self, config):
        super().__init__(config)
        self.break_intervals = {
            'pomodoro': 25,
            'short': 60,
            'long': 90
        }
    
    async def generate(self, activity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate break reminder todos"""
        suggestions = []
        
        # Check session duration
        session_data = activity_data.get('session_data', {})
        session_start = session_data.get('start_time')
        
        if not session_start:
            return suggestions
        
        # Parse session start time
        if isinstance(session_start, str):
            try:
                session_start = datetime.fromisoformat(session_start.replace('Z', '+00:00'))
            except:
                return suggestions
        elif not hasattr(session_start, 'timestamp'):
            return suggestions
        
        # Calculate work duration
        work_duration = (datetime.now() - session_start).total_seconds() / 60
        
        # Check for recent breaks
        idle_periods = session_data.get('idle_periods', [])
        recent_break = self._has_recent_break(idle_periods)
        
        if not recent_break:
            suggestions.extend(self._generate_break_suggestions(work_duration))
        
        return suggestions
    
    def _has_recent_break(self, idle_periods: List[Dict]) -> bool:
        """Check if there was a recent break"""
        if not idle_periods:
            return False
        
        for period in idle_periods:
            period_start = period.get('start')
            if not period_start:
                continue
            
            if isinstance(period_start, str):
                try:
                    period_start = datetime.fromisoformat(period_start)
                except:
                    continue
            
            # Check if break was within last 30 minutes
            if (datetime.now() - period_start).total_seconds() < 1800:
                return True
        
        return False
    
    def _generate_break_suggestions(self, work_duration: float) -> List[Dict[str, Any]]:
        """Generate break suggestions based on work duration"""
        suggestions = []
        
        if work_duration > self.break_intervals['long']:
            # Mandatory break after 90 minutes
            suggestions.append(self.create_todo(
                title='🚨 Take a mandatory break',
                description='You\'ve been working for over 90 minutes. Stand up, stretch, and rest your eyes for 10-15 minutes.',
                priority='urgent',
                category='health',
                confidence=0.95,
                source='break_reminder',
                estimated_minutes=15,
                break_type='mandatory'
            ))
        
        elif work_duration > self.break_intervals['short']:
            # Recommended break after 60 minutes
            suggestions.append(self.create_todo(
                title='Time for a short break',
                description='You\'ve been focused for an hour. Take a 5-10 minute break to maintain productivity.',
                priority='high',
                category='health',
                confidence=0.85,
                source='break_reminder',
                estimated_minutes=10,
                break_type='recommended'
            ))
        
        elif work_duration > self.break_intervals['pomodoro']:
            # Pomodoro break after 25 minutes
            suggestions.append(self.create_todo(
                title='Pomodoro break time',
                description='Complete your 25-minute focus session with a 5-minute break.',
                priority='medium',
                category='health',
                confidence=0.7,
                source='break_reminder',
                estimated_minutes=5,
                break_type='pomodoro'
            ))
        
        return suggestions