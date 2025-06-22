"""
Continuation todo generator
Generates todos for continuing interrupted or unfinished work
"""

from typing import Dict, List, Any
from .base_generator import BaseTodoGenerator


class ContinuationTodoGenerator(BaseTodoGenerator):
    """Generates todos for continuing interrupted or unfinished work"""
    
    def __init__(self, config):
        super().__init__(config)
        self.work_patterns = {
            'development': ['code', 'visual studio', 'pycharm', 'intellij'],
            'documentation': ['word', 'docs', 'notion', 'obsidian'],
            'design': ['figma', 'photoshop', 'illustrator', 'sketch'],
            'research': ['chrome', 'firefox', 'safari', 'edge'],
            'communication': ['slack', 'teams', 'zoom', 'outlook']
        }
    
    async def generate(self, activity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate continuation todos"""
        suggestions = []
        
        session_data = activity_data.get('session_data', {})
        applications = session_data.get('applications', {})
        
        for category, app_keywords in self.work_patterns.items():
            if self._detect_work_type(applications, app_keywords):
                todo = self._create_continuation_todo(category)
                if todo:
                    suggestions.append(todo)
        
        return suggestions
    
    def _detect_work_type(self, applications: Dict, keywords: List[str]) -> bool:
        """Detect if specific type of work is happening"""
        app_names = [app.lower() for app in applications.keys()]
        return any(keyword in app_name for keyword in keywords for app_name in app_names)
    
    def _create_continuation_todo(self, work_type: str) -> Dict[str, Any]:
        """Create continuation todo for specific work type"""
        continuation_templates = {
            'development': {
                'title': 'Continue coding session',
                'description': 'Resume work on current development project',
                'priority': 'medium',
                'confidence': 0.8,
                'estimated_minutes': 60
            },
            'documentation': {
                'title': 'Finish document editing',
                'description': 'Complete current document or report',
                'priority': 'medium', 
                'confidence': 0.7,
                'estimated_minutes': 30
            },
            'design': {
                'title': 'Continue design work',
                'description': 'Finish current design project or mockups',
                'priority': 'medium',
                'confidence': 0.75,
                'estimated_minutes': 45
            },
            'research': {
                'title': 'Compile research findings',
                'description': 'Organize and document research findings',
                'priority': 'low',
                'confidence': 0.6,
                'estimated_minutes': 20
            },
            'communication': {
                'title': 'Follow up on conversations',
                'description': 'Send follow-up messages and action items',
                'priority': 'medium',
                'confidence': 0.65,
                'estimated_minutes': 15
            }
        }
        
        template = continuation_templates.get(work_type)
        if not template:
            return None
        
        return self.create_todo(
            title=template['title'],
            description=template['description'],
            priority=template['priority'],
            category=work_type,
            confidence=template['confidence'],
            source='continuation_pattern',
            estimated_minutes=template['estimated_minutes'],
            work_type=work_type
        )