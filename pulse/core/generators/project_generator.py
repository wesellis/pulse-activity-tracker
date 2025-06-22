"""
Project-specific todo generator
Generates todos based on development activities and project context
"""

from typing import Dict, List, Any
from .base_generator import BaseTodoGenerator


class ProjectTodoGenerator(BaseTodoGenerator):
    """Generates project-specific todos based on recent activity"""
    
    def __init__(self, config):
        super().__init__(config)
        self.dev_apps = ['code', 'visual studio', 'pycharm', 'intellij', 'eclipse', 'vim', 'emacs']
        self.vcs_apps = ['git', 'sourcetree', 'github', 'gitlab', 'bitbucket']
        self.test_keywords = ['test', 'pytest', 'unittest', 'jest', 'mocha']
    
    async def generate(self, activity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate project-related todos"""
        suggestions = []
        
        # Analyze recent applications
        session_data = activity_data.get('session_data', {})
        applications = session_data.get('applications', {})
        app_names = [app.lower() for app in applications.keys()]
        
        # Version control todos
        suggestions.extend(self._generate_vcs_todos(app_names))
        
        # Testing todos
        suggestions.extend(self._generate_testing_todos(app_names))
        
        # Documentation todos
        suggestions.extend(self._generate_documentation_todos(activity_data))
        
        # Code review todos
        suggestions.extend(self._generate_review_todos(app_names))
        
        # Deployment todos
        suggestions.extend(self._generate_deployment_todos(app_names))
        
        return suggestions
    
    def _generate_vcs_todos(self, app_names: List[str]) -> List[Dict[str, Any]]:
        """Generate version control related todos"""
        suggestions = []
        
        # Check if VCS tools are being used
        if any(vcs in ' '.join(app_names) for vcs in self.vcs_apps):
            suggestions.append(self.create_todo(
                title='Commit your changes',
                description='Review and commit pending changes to version control.',
                priority='high',
                category='development',
                confidence=0.8,
                source='project_pattern',
                estimated_minutes=10,
                project_type='version_control'
            ))
            
            suggestions.append(self.create_todo(
                title='Push to remote repository',
                description='Push your local commits to the remote repository.',
                priority='medium',
                category='development',
                confidence=0.7,
                source='project_pattern',
                estimated_minutes=5,
                project_type='version_control'
            ))
        
        return suggestions
    
    def _generate_testing_todos(self, app_names: List[str]) -> List[Dict[str, Any]]:
        """Generate testing related todos"""
        suggestions = []
        
        # Check if testing tools are being used
        if any(test in ' '.join(app_names) for test in self.test_keywords):
            suggestions.append(self.create_todo(
                title='Run test suite',
                description='Execute tests to ensure code quality before pushing.',
                priority='high',
                category='development',
                confidence=0.75,
                source='project_pattern',
                estimated_minutes=15,
                project_type='testing'
            ))
            
            suggestions.append(self.create_todo(
                title='Write tests for new features',
                description='Add test coverage for recently implemented functionality.',
                priority='medium',
                category='development',
                confidence=0.65,
                source='project_pattern',
                estimated_minutes=30,
                project_type='testing'
            ))
        
        return suggestions
    
    def _generate_documentation_todos(self, activity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate documentation related todos"""
        suggestions = []
        
        productivity_indicators = activity_data.get('productivity_indicators', {})
        category_breakdown = productivity_indicators.get('category_breakdown', {})
        
        # If significant development time
        if category_breakdown.get('development', 0) > 60:
            suggestions.append(self.create_todo(
                title='Update documentation',
                description='Document recent code changes and update README if needed.',
                priority='medium',
                category='documentation',
                confidence=0.7,
                source='project_pattern',
                estimated_minutes=20,
                project_type='documentation'
            ))
            
            suggestions.append(self.create_todo(
                title='Add code comments',
                description='Review recent code and add explanatory comments where needed.',
                priority='low',
                category='documentation',
                confidence=0.6,
                source='project_pattern',
                estimated_minutes=15,
                project_type='documentation'
            ))
        
        return suggestions
    
    def _generate_review_todos(self, app_names: List[str]) -> List[Dict[str, Any]]:
        """Generate code review related todos"""
        suggestions = []
        
        # Check if collaboration tools are being used
        if any(platform in ' '.join(app_names) for platform in ['github', 'gitlab', 'bitbucket']):
            suggestions.append(self.create_todo(
                title='Review pull requests',
                description='Check and review pending pull requests from team members.',
                priority='medium',
                category='collaboration',
                confidence=0.65,
                source='project_pattern',
                estimated_minutes=30,
                project_type='code_review'
            ))
        
        return suggestions
    
    def _generate_deployment_todos(self, app_names: List[str]) -> List[Dict[str, Any]]:
        """Generate deployment related todos"""
        suggestions = []
        
        # Check for CI/CD or deployment tools
        deploy_keywords = ['jenkins', 'travis', 'circle', 'docker', 'kubernetes']
        if any(deploy in ' '.join(app_names) for deploy in deploy_keywords):
            suggestions.append(self.create_todo(
                title='Check deployment pipeline',
                description='Verify CI/CD pipeline status and recent deployments.',
                priority='medium',
                category='deployment',
                confidence=0.6,
                source='project_pattern',
                estimated_minutes=10,
                project_type='deployment'
            ))
        
        return suggestions