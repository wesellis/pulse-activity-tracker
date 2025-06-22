"""
Todo Generator v2 - Modular intelligent task generation
Uses modular generators for maintainable and focused todo generation
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import re

from .generators import (
    BreakReminderGenerator,
    HealthTodoGenerator,
    ProjectTodoGenerator,
    DistractionTodoGenerator,
    PatternBasedGenerator,
    ContextAwareGenerator,
    ScheduleBasedGenerator,
    ContinuationTodoGenerator
)

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available - using basic todo generation")


class TodoGenerator:
    """Modular intelligent todo suggestions generator"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize modular generators
        self.generators = self._initialize_generators()
        
        # Pattern learning components
        self.activity_patterns = {}
        self.todo_history = []
        self.completion_patterns = {}
        
        # Ranking settings
        self.max_suggestions = getattr(config, 'max_todo_suggestions', 10)
        self.min_confidence = getattr(config, 'min_todo_confidence', 0.3)
    
    def _initialize_generators(self) -> List:
        """Initialize all todo generators"""
        generators = [
            BreakReminderGenerator(self.config),
            HealthTodoGenerator(self.config),
            ProjectTodoGenerator(self.config),
            DistractionTodoGenerator(self.config),
            PatternBasedGenerator(self.config),
            ContextAwareGenerator(self.config),
            ScheduleBasedGenerator(self.config),
            ContinuationTodoGenerator(self.config)
        ]
        
        self.logger.info(f"Initialized {len(generators)} todo generators")
        return generators
    
    async def generate_suggestions(self, activity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate todo suggestions using all available generators"""
        suggestions = []
        
        try:
            # Run all generators
            for generator in self.generators:
                try:
                    new_suggestions = await generator.generate(activity_data)
                    suggestions.extend(new_suggestions)
                    self.logger.debug(f"{generator.__class__.__name__} generated {len(new_suggestions)} suggestions")
                except Exception as e:
                    self.logger.error(f"Error in {generator.__class__.__name__}: {e}")
            
            # Use ML for advanced suggestions if available
            if SKLEARN_AVAILABLE:
                ml_suggestions = await self._generate_ml_suggestions(activity_data)
                suggestions.extend(ml_suggestions)
            
            # Filter by minimum confidence
            filtered_suggestions = [
                s for s in suggestions 
                if s.get('confidence', 0) >= self.min_confidence
            ]
            
            # Rank and filter suggestions
            ranked_suggestions = self._rank_suggestions(filtered_suggestions, activity_data)
            
            # Return top suggestions
            final_suggestions = ranked_suggestions[:self.max_suggestions]
            
            self.logger.info(f"Generated {len(final_suggestions)} final suggestions from {len(suggestions)} total")
            return final_suggestions
            
        except Exception as e:
            self.logger.error(f"Error generating suggestions: {e}")
            return []
    
    async def _generate_ml_suggestions(self, activity_data: Dict[str, Any]) -> List[Dict]:
        """Generate suggestions using machine learning (if available)"""
        if not SKLEARN_AVAILABLE:
            return []
        
        suggestions = []
        
        try:
            # Placeholder for ML-based suggestions
            # In a full implementation, this would:
            # 1. Analyze historical activity patterns
            # 2. Use clustering to identify similar situations
            # 3. Generate suggestions based on successful past actions
            
            # For now, return a simple ML-based suggestion
            productivity_score = activity_data.get('productivity_indicators', {}).get('productivity_score', 50)
            
            if productivity_score > 70:
                suggestions.append({
                    'title': 'AI Suggestion: Optimize current workflow',
                    'description': 'Based on your high productivity, consider documenting your current workflow for future reference.',
                    'priority': 'low',
                    'category': 'optimization',
                    'confidence': 0.6,
                    'source': 'machine_learning',
                    'estimated_minutes': 15,
                    'ml_model': 'productivity_optimizer'
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
        
        # Base confidence score (0-100)
        confidence = suggestion.get('confidence', 0.5)
        score += confidence * 100
        
        # Priority weighting
        priority_weights = {'urgent': 40, 'high': 30, 'medium': 20, 'low': 10}
        priority = suggestion.get('priority', 'medium')
        score += priority_weights.get(priority, 20)
        
        # Time relevance
        current_hour = datetime.now().hour
        if 'break' in suggestion.get('category', '').lower() and 9 <= current_hour <= 17:
            score += 25  # Boost break suggestions during work hours
        
        # Category relevance based on current activity
        session_data = activity_data.get('session_data', {})
        applications = session_data.get('applications', {})
        
        category = suggestion.get('category', '').lower()
        app_names = [app.lower() for app in applications.keys()]
        
        # Boost relevant suggestions
        if category == 'development' and any('code' in app for app in app_names):
            score += 25
        elif category == 'health' and len(app_names) > 10:  # Many apps = likely tired
            score += 20
        elif category == 'focus' and suggestion.get('distraction_score', 0) > 30:
            score += 30
        
        # Source reliability weighting
        source_weights = {
            'break_reminder': 1.2,
            'health_reminder': 1.1,
            'distraction_analysis': 1.3,
            'productivity_pattern': 1.15,
            'project_pattern': 1.1,
            'machine_learning': 0.9
        }
        source = suggestion.get('source', 'unknown')
        score *= source_weights.get(source, 1.0)
        
        return round(score, 2)
    
    def _remove_similar_suggestions(self, suggestions: List[Dict]) -> List[Dict]:
        """Remove suggestions with similar titles or descriptions"""
        unique_suggestions = []
        seen_titles = set()
        
        for suggestion in suggestions:
            title = suggestion.get('title', '').lower()
            
            # Simple similarity check
            is_similar = False
            for seen_title in seen_titles:
                if self._calculate_similarity(title, seen_title) > 0.7:
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
                'time_to_complete': completion_context.get('time_to_complete', 0),
                'user_rating': completion_context.get('user_rating'),
                'effectiveness': completion_context.get('effectiveness')
            }
            
            todo_id = todo.get('id', str(len(self.completion_patterns)))
            self.completion_patterns[todo_id] = pattern
            
            self.logger.info(f"Learned from completed todo: {todo.get('title', 'Unknown')}")
            
        except Exception as e:
            self.logger.error(f"Error learning from completion: {e}")
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get statistics about todo generation performance"""
        return {
            'total_generators': len(self.generators),
            'generator_types': [g.__class__.__name__ for g in self.generators],
            'completion_patterns': len(self.completion_patterns),
            'ml_available': SKLEARN_AVAILABLE,
            'max_suggestions': self.max_suggestions,
            'min_confidence': self.min_confidence,
            'last_generation': datetime.now().isoformat()
        }
    
    def configure_generator(self, generator_name: str, enabled: bool):
        """Enable or disable specific generators"""
        # This could be used to turn generators on/off based on user preferences
        for generator in self.generators:
            if generator.__class__.__name__ == generator_name:
                generator.enabled = enabled
                self.logger.info(f"{'Enabled' if enabled else 'Disabled'} {generator_name}")
                return True
        
        self.logger.warning(f"Generator {generator_name} not found")
        return False