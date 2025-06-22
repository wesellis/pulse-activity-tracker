"""
Base class for all todo generators
Provides common functionality and interface
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any
import logging


class BaseTodoGenerator(ABC):
    """Abstract base class for todo generators"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def generate(self, activity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate todo suggestions based on activity data"""
        pass
    
    def create_todo(
        self,
        title: str,
        description: str,
        priority: str = 'medium',
        category: str = 'general',
        confidence: float = 0.5,
        source: str = 'unknown',
        estimated_minutes: int = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a standardized todo dictionary"""
        todo = {
            'title': title,
            'description': description,
            'priority': priority,
            'category': category,
            'confidence': confidence,
            'source': source,
            'generated_at': datetime.now().isoformat(),
            'is_ai_generated': True
        }
        
        if estimated_minutes:
            todo['estimated_minutes'] = estimated_minutes
        
        # Add any additional fields
        todo.update(kwargs)
        
        return todo
    
    def validate_priority(self, priority: str) -> str:
        """Validate and normalize priority levels"""
        valid_priorities = ['low', 'medium', 'high', 'urgent']
        priority = priority.lower()
        
        if priority not in valid_priorities:
            self.logger.warning(f"Invalid priority '{priority}', defaulting to 'medium'")
            return 'medium'
        
        return priority
    
    def calculate_confidence(self, base_confidence: float, *modifiers: float) -> float:
        """Calculate final confidence score with modifiers"""
        confidence = base_confidence
        
        for modifier in modifiers:
            confidence *= modifier
        
        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, confidence))