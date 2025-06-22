"""
Health and wellness todo generator
Generates health-related reminders and suggestions
"""

from datetime import datetime
from typing import Dict, List, Any
from .base_generator import BaseTodoGenerator


class HealthTodoGenerator(BaseTodoGenerator):
    """Generates health and wellness related todos"""
    
    def __init__(self, config):
        super().__init__(config)
        self.health_checks = {
            'hydration': {'interval_hours': 2, 'priority': 'low'},
            'eye_rest': {'threshold_minutes': 120, 'priority': 'medium'},
            'posture': {'check_hours': [10, 14, 16], 'priority': 'low'},
            'lunch': {'time_range': (12, 13), 'priority': 'high'},
            'stretch': {'interval_minutes': 90, 'priority': 'medium'}
        }
    
    async def generate(self, activity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate health-related todos"""
        suggestions = []
        current_time = datetime.now()
        hour = current_time.hour
        
        # Hydration reminder
        if self._should_remind_hydration(hour):
            suggestions.append(self.create_todo(
                title='Stay hydrated 💧',
                description='Drink a glass of water to maintain hydration and focus.',
                priority='low',
                category='health',
                confidence=0.6,
                source='health_reminder',
                estimated_minutes=2,
                health_type='hydration'
            ))
        
        # Eye rest reminder
        suggestions.extend(self._generate_eye_rest_reminders(activity_data))
        
        # Posture check
        if hour in self.health_checks['posture']['check_hours']:
            suggestions.append(self.create_todo(
                title='Check your posture',
                description='Adjust your sitting position, straighten your back, and relax your shoulders.',
                priority='low',
                category='health',
                confidence=0.5,
                source='health_reminder',
                estimated_minutes=1,
                health_type='posture'
            ))
        
        # Meal reminders
        suggestions.extend(self._generate_meal_reminders(current_time))
        
        # Exercise reminders
        suggestions.extend(self._generate_exercise_reminders(activity_data))
        
        return suggestions
    
    def _should_remind_hydration(self, hour: int) -> bool:
        """Check if it's time for hydration reminder"""
        return hour % self.health_checks['hydration']['interval_hours'] == 0
    
    def _generate_eye_rest_reminders(self, activity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate eye rest reminders based on screen time"""
        suggestions = []
        
        productivity_indicators = activity_data.get('productivity_indicators', {})
        screen_time = productivity_indicators.get('active_time_minutes', 0)
        
        if screen_time > self.health_checks['eye_rest']['threshold_minutes']:
            suggestions.append(self.create_todo(
                title='Rest your eyes (20-20-20 rule)',
                description='Look at something 20 feet away for 20 seconds to reduce eye strain.',
                priority='medium',
                category='health',
                confidence=0.8,
                source='health_reminder',
                estimated_minutes=1,
                health_type='eye_rest'
            ))
        
        return suggestions
    
    def _generate_meal_reminders(self, current_time: datetime) -> List[Dict[str, Any]]:
        """Generate meal reminders based on time"""
        suggestions = []
        hour = current_time.hour
        minute = current_time.minute
        
        # Lunch reminder
        lunch_start, lunch_end = self.health_checks['lunch']['time_range']
        if lunch_start <= hour <= lunch_end and minute < 30:
            suggestions.append(self.create_todo(
                title='Take a lunch break',
                description='Step away from work and have a proper meal.',
                priority='high',
                category='health',
                confidence=0.9,
                source='health_reminder',
                estimated_minutes=30,
                health_type='meal'
            ))
        
        # Healthy snack reminder (mid-morning and mid-afternoon)
        if hour in [10, 15]:
            suggestions.append(self.create_todo(
                title='Healthy snack time',
                description='Have a nutritious snack to maintain energy levels.',
                priority='low',
                category='health',
                confidence=0.5,
                source='health_reminder',
                estimated_minutes=5,
                health_type='snack'
            ))
        
        return suggestions
    
    def _generate_exercise_reminders(self, activity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate exercise and movement reminders"""
        suggestions = []
        
        # Check for prolonged sitting
        session_data = activity_data.get('session_data', {})
        session_start = session_data.get('start_time')
        
        if session_start:
            try:
                if isinstance(session_start, str):
                    session_start = datetime.fromisoformat(session_start.replace('Z', '+00:00'))
                
                sitting_duration = (datetime.now() - session_start).total_seconds() / 60
                
                if sitting_duration > self.health_checks['stretch']['interval_minutes']:
                    suggestions.append(self.create_todo(
                        title='Time to stretch and move',
                        description='Stand up, do some stretches, or take a short walk around.',
                        priority='medium',
                        category='health',
                        confidence=0.75,
                        source='health_reminder',
                        estimated_minutes=5,
                        health_type='exercise'
                    ))
            except:
                pass
        
        return suggestions