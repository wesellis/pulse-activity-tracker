"""
Pattern-based todo generator
Generates todos based on time patterns and recurring behaviors
"""

from datetime import datetime
from typing import Dict, List, Any
from .base_generator import BaseTodoGenerator


class PatternBasedGenerator(BaseTodoGenerator):
    """Generates todos based on learned activity patterns"""
    
    def __init__(self, config):
        super().__init__(config)
        self.weekly_patterns = {
            0: {'name': 'Monday', 'todos': ['weekly_planning', 'inbox_zero']},
            1: {'name': 'Tuesday', 'todos': ['deep_work']},
            2: {'name': 'Wednesday', 'todos': ['team_sync']},
            3: {'name': 'Thursday', 'todos': ['progress_review']},
            4: {'name': 'Friday', 'todos': ['weekly_review', 'planning_next']},
            5: {'name': 'Saturday', 'todos': ['personal_projects']},
            6: {'name': 'Sunday', 'todos': ['week_prep']}
        }
        
        self.time_patterns = {
            'morning': (6, 11),
            'midday': (11, 14),
            'afternoon': (14, 17),
            'evening': (17, 20),
            'night': (20, 23)
        }
    
    async def generate(self, activity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate pattern-based todos"""
        suggestions = []
        current_time = datetime.now()
        
        # Day-of-week patterns
        suggestions.extend(self._generate_weekly_todos(current_time))
        
        # Time-of-day patterns
        suggestions.extend(self._generate_time_based_todos(current_time))
        
        # Productivity patterns
        suggestions.extend(self._generate_productivity_pattern_todos(activity_data))
        
        return suggestions
    
    def _generate_weekly_todos(self, current_time: datetime) -> List[Dict[str, Any]]:
        """Generate todos based on day of week"""
        suggestions = []
        weekday = current_time.weekday()
        day_info = self.weekly_patterns.get(weekday, {})
        
        if 'weekly_planning' in day_info.get('todos', []):
            suggestions.append(self.create_todo(
                title='Weekly planning session',
                description='Review goals and plan the week ahead',
                priority='high',
                category='planning',
                confidence=0.9,
                source='weekly_pattern',
                estimated_minutes=30,
                pattern_type='weekly',
                day_of_week=day_info['name']
            ))
        
        if 'weekly_review' in day_info.get('todos', []):
            suggestions.append(self.create_todo(
                title='Week wrap-up and review',
                description='Summarize accomplishments and prepare weekly report',
                priority='medium',
                category='reporting',
                confidence=0.8,
                source='weekly_pattern',
                estimated_minutes=20,
                pattern_type='weekly',
                day_of_week=day_info['name']
            ))
        
        if 'team_sync' in day_info.get('todos', []):
            suggestions.append(self.create_todo(
                title='Team sync preparation',
                description='Prepare updates and questions for team meeting',
                priority='medium',
                category='communication',
                confidence=0.7,
                source='weekly_pattern',
                estimated_minutes=15,
                pattern_type='weekly'
            ))
        
        return suggestions
    
    def _generate_time_based_todos(self, current_time: datetime) -> List[Dict[str, Any]]:
        """Generate todos based on time of day"""
        suggestions = []
        hour = current_time.hour
        
        # Determine time period
        time_period = None
        for period, (start, end) in self.time_patterns.items():
            if start <= hour < end:
                time_period = period
                break
        
        if time_period == 'morning':
            suggestions.append(self.create_todo(
                title='Tackle high-focus task',
                description='Work on most challenging or important task during peak hours',
                priority='high',
                category='productivity',
                confidence=0.7,
                source='time_pattern',
                estimated_minutes=60,
                pattern_type='circadian',
                time_period=time_period
            ))
        
        elif time_period == 'afternoon':
            suggestions.append(self.create_todo(
                title='Handle administrative tasks',
                description='Process emails, update documentation, or handle routine tasks',
                priority='low',
                category='administrative',
                confidence=0.6,
                source='time_pattern',
                estimated_minutes=30,
                pattern_type='circadian',
                time_period=time_period
            ))
        
        elif time_period == 'evening':
            suggestions.append(self.create_todo(
                title='Plan tomorrow\'s priorities',
                description='Review calendar and set top 3 priorities for tomorrow',
                priority='medium',
                category='planning',
                confidence=0.75,
                source='time_pattern',
                estimated_minutes=10,
                pattern_type='circadian',
                time_period=time_period
            ))
        
        return suggestions
    
    def _generate_productivity_pattern_todos(self, activity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate todos based on productivity patterns"""
        suggestions = []
        
        productivity_indicators = activity_data.get('productivity_indicators', {})
        productivity_score = productivity_indicators.get('productivity_score', 0)
        
        # High productivity momentum
        if productivity_score > 80:
            suggestions.append(self.create_todo(
                title='Leverage high productivity',
                description='You\'re in the zone! Tackle a challenging task while your productivity is high.',
                priority='high',
                category='productivity',
                confidence=0.8,
                source='productivity_pattern',
                estimated_minutes=45,
                pattern_type='momentum',
                productivity_level='high'
            ))
        
        # Productivity slump
        elif productivity_score < 40:
            suggestions.append(self.create_todo(
                title='Switch to low-energy tasks',
                description='Productivity is low. Switch to routine tasks that don\'t require deep focus.',
                priority='medium',
                category='productivity',
                confidence=0.7,
                source='productivity_pattern',
                estimated_minutes=20,
                pattern_type='energy_management',
                productivity_level='low'
            ))
        
        return suggestions