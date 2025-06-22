"""
CRUD operations for all database models
Provides high-level database operations with error handling
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from .models import Activity, Todo, Pattern, Report, SessionSummary
from .connection import get_db_session

logger = logging.getLogger(__name__)


class ActivityCRUD:
    """CRUD operations for Activity model"""
    
    @staticmethod
    def create(db: Session, activity_data: Dict[str, Any]) -> Optional[Activity]:
        """Create new activity record"""
        try:
            activity = Activity(**activity_data)
            db.add(activity)
            db.commit()
            db.refresh(activity)
            return activity
        except Exception as e:
            logger.error(f"Failed to create activity: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def get_by_session(db: Session, session_id: str) -> List[Activity]:
        """Get all activities for a session"""
        return db.query(Activity).filter(
            Activity.session_id == session_id
        ).order_by(Activity.timestamp).all()
    
    @staticmethod
    def get_by_timerange(
        db: Session,
        start_time: datetime,
        end_time: datetime,
        application_name: Optional[str] = None
    ) -> List[Activity]:
        """Get activities within time range"""
        query = db.query(Activity).filter(
            and_(
                Activity.timestamp >= start_time,
                Activity.timestamp <= end_time
            )
        )
        
        if application_name:
            query = query.filter(Activity.application_name == application_name)
        
        return query.order_by(Activity.timestamp).all()
    
    @staticmethod
    def get_productive_time(
        db: Session,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, float]:
        """Get productive vs unproductive time"""
        activities = db.query(
            Activity.is_productive,
            func.sum(Activity.duration_seconds).label('total_seconds')
        ).filter(
            and_(
                Activity.timestamp >= start_time,
                Activity.timestamp <= end_time
            )
        ).group_by(Activity.is_productive).all()
        
        result = {'productive': 0, 'unproductive': 0}
        for is_productive, total_seconds in activities:
            if is_productive:
                result['productive'] = float(total_seconds or 0) / 60
            else:
                result['unproductive'] = float(total_seconds or 0) / 60
        
        return result
    
    @staticmethod
    def get_category_breakdown(
        db: Session,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, float]:
        """Get time breakdown by category"""
        activities = db.query(
            Activity.category,
            func.sum(Activity.duration_seconds).label('total_seconds')
        ).filter(
            and_(
                Activity.timestamp >= start_time,
                Activity.timestamp <= end_time,
                Activity.category.isnot(None)
            )
        ).group_by(Activity.category).all()
        
        return {
            category: float(total_seconds or 0) / 60
            for category, total_seconds in activities
        }
    
    @staticmethod
    def cleanup_old_activities(db: Session, days_to_keep: int = 30) -> int:
        """Remove activities older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        deleted = db.query(Activity).filter(
            Activity.timestamp < cutoff_date
        ).delete()
        
        db.commit()
        return deleted


class TodoCRUD:
    """CRUD operations for Todo model"""
    
    @staticmethod
    def create(db: Session, todo_data: Dict[str, Any]) -> Optional[Todo]:
        """Create new todo"""
        try:
            todo = Todo(**todo_data)
            db.add(todo)
            db.commit()
            db.refresh(todo)
            return todo
        except Exception as e:
            logger.error(f"Failed to create todo: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def get_active(db: Session, category: Optional[str] = None) -> List[Todo]:
        """Get all active (non-completed) todos"""
        query = db.query(Todo).filter(
            Todo.status.in_(['pending', 'in_progress'])
        )
        
        if category:
            query = query.filter(Todo.category == category)
        
        return query.order_by(
            desc(Todo.priority == 'urgent'),
            desc(Todo.priority == 'high'),
            desc(Todo.priority == 'medium'),
            Todo.due_date
        ).all()
    
    @staticmethod
    def get_by_id(db: Session, todo_id: int) -> Optional[Todo]:
        """Get todo by ID"""
        return db.query(Todo).filter(Todo.id == todo_id).first()
    
    @staticmethod
    def update(db: Session, todo_id: int, update_data: Dict[str, Any]) -> Optional[Todo]:
        """Update todo"""
        todo = db.query(Todo).filter(Todo.id == todo_id).first()
        if not todo:
            return None
        
        try:
            for key, value in update_data.items():
                if hasattr(todo, key):
                    setattr(todo, key, value)
            
            if 'status' in update_data and update_data['status'] == 'completed':
                todo.completed_at = datetime.utcnow()
            
            db.commit()
            db.refresh(todo)
            return todo
        except Exception as e:
            logger.error(f"Failed to update todo: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def get_overdue(db: Session) -> List[Todo]:
        """Get overdue todos"""
        return db.query(Todo).filter(
            and_(
                Todo.status.in_(['pending', 'in_progress']),
                Todo.due_date < datetime.utcnow()
            )
        ).order_by(Todo.due_date).all()
    
    @staticmethod
    def get_upcoming(db: Session, days: int = 7) -> List[Todo]:
        """Get todos due in next N days"""
        future_date = datetime.utcnow() + timedelta(days=days)
        
        return db.query(Todo).filter(
            and_(
                Todo.status.in_(['pending', 'in_progress']),
                Todo.due_date <= future_date,
                Todo.due_date >= datetime.utcnow()
            )
        ).order_by(Todo.due_date).all()
    
    @staticmethod
    def create_recurring(db: Session, parent_todo: Todo) -> Optional[Todo]:
        """Create next occurrence of recurring todo"""
        if not parent_todo.is_recurring or not parent_todo.recurrence_pattern:
            return None
        
        pattern = parent_todo.recurrence_pattern
        
        # Calculate next due date based on pattern
        if pattern.get('type') == 'daily':
            next_due = parent_todo.due_date + timedelta(days=pattern.get('interval', 1))
        elif pattern.get('type') == 'weekly':
            next_due = parent_todo.due_date + timedelta(weeks=pattern.get('interval', 1))
        elif pattern.get('type') == 'monthly':
            # Simple month addition (could be improved)
            next_due = parent_todo.due_date + timedelta(days=30 * pattern.get('interval', 1))
        else:
            return None
        
        # Create new todo
        new_todo_data = {
            'title': parent_todo.title,
            'description': parent_todo.description,
            'priority': parent_todo.priority,
            'category': parent_todo.category,
            'tags': parent_todo.tags,
            'due_date': next_due,
            'estimated_minutes': parent_todo.estimated_minutes,
            'is_recurring': True,
            'recurrence_pattern': parent_todo.recurrence_pattern,
            'parent_todo_id': parent_todo.id,
            'is_ai_generated': parent_todo.is_ai_generated
        }
        
        return TodoCRUD.create(db, new_todo_data)


class PatternCRUD:
    """CRUD operations for Pattern model"""
    
    @staticmethod
    def create(db: Session, pattern_data: Dict[str, Any]) -> Optional[Pattern]:
        """Create new pattern"""
        try:
            pattern = Pattern(**pattern_data)
            db.add(pattern)
            db.commit()
            db.refresh(pattern)
            return pattern
        except Exception as e:
            logger.error(f"Failed to create pattern: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def get_active(db: Session, pattern_type: Optional[str] = None) -> List[Pattern]:
        """Get active patterns"""
        query = db.query(Pattern).filter(Pattern.is_active == True)
        
        if pattern_type:
            query = query.filter(Pattern.pattern_type == pattern_type)
        
        return query.order_by(desc(Pattern.confidence_score)).all()
    
    @staticmethod
    def update_occurrence(db: Session, pattern_id: int) -> Optional[Pattern]:
        """Update pattern occurrence count and timestamp"""
        pattern = db.query(Pattern).filter(Pattern.id == pattern_id).first()
        if not pattern:
            return None
        
        try:
            pattern.occurrence_count += 1
            pattern.last_occurrence = datetime.utcnow()
            db.commit()
            db.refresh(pattern)
            return pattern
        except Exception as e:
            logger.error(f"Failed to update pattern occurrence: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def find_similar(
        db: Session,
        pattern_type: str,
        trigger_conditions: Dict
    ) -> Optional[Pattern]:
        """Find similar existing pattern"""
        # This is a simplified version - in production would use more
        # sophisticated similarity matching
        patterns = db.query(Pattern).filter(
            and_(
                Pattern.pattern_type == pattern_type,
                Pattern.is_active == True
            )
        ).all()
        
        for pattern in patterns:
            if pattern.trigger_conditions == trigger_conditions:
                return pattern
        
        return None


class ReportCRUD:
    """CRUD operations for Report model"""
    
    @staticmethod
    def create(db: Session, report_data: Dict[str, Any]) -> Optional[Report]:
        """Create new report"""
        try:
            report = Report(**report_data)
            db.add(report)
            db.commit()
            db.refresh(report)
            return report
        except Exception as e:
            logger.error(f"Failed to create report: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def get_recent(db: Session, report_type: Optional[str] = None, limit: int = 10) -> List[Report]:
        """Get recent reports"""
        query = db.query(Report)
        
        if report_type:
            query = query.filter(Report.report_type == report_type)
        
        return query.order_by(desc(Report.created_at)).limit(limit).all()
    
    @staticmethod
    def get_by_token(db: Session, share_token: str) -> Optional[Report]:
        """Get report by share token"""
        return db.query(Report).filter(Report.share_token == share_token).first()
    
    @staticmethod
    def generate_share_token(db: Session, report_id: int) -> Optional[str]:
        """Generate share token for report"""
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return None
        
        try:
            token = str(uuid4()).replace('-', '')
            report.share_token = token
            report.is_shared = True
            db.commit()
            return token
        except Exception as e:
            logger.error(f"Failed to generate share token: {e}")
            db.rollback()
            return None


class SessionSummaryCRUD:
    """CRUD operations for SessionSummary model"""
    
    @staticmethod
    def create(db: Session, summary_data: Dict[str, Any]) -> Optional[SessionSummary]:
        """Create session summary"""
        try:
            summary = SessionSummary(**summary_data)
            db.add(summary)
            db.commit()
            db.refresh(summary)
            return summary
        except Exception as e:
            logger.error(f"Failed to create session summary: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def get_by_session(db: Session, session_id: str) -> Optional[SessionSummary]:
        """Get summary by session ID"""
        return db.query(SessionSummary).filter(
            SessionSummary.session_id == session_id
        ).first()
    
    @staticmethod
    def get_recent_sessions(db: Session, limit: int = 10) -> List[SessionSummary]:
        """Get recent session summaries"""
        return db.query(SessionSummary).order_by(
            desc(SessionSummary.start_time)
        ).limit(limit).all()
    
    @staticmethod
    def get_productivity_stats(
        db: Session,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get productivity statistics for date range"""
        summaries = db.query(SessionSummary).filter(
            and_(
                SessionSummary.start_time >= start_date,
                SessionSummary.start_time <= end_date
            )
        ).all()
        
        if not summaries:
            return {
                'avg_productivity': 0,
                'avg_focus': 0,
                'total_productive_hours': 0,
                'total_sessions': 0
            }
        
        total_sessions = len(summaries)
        avg_productivity = sum(s.productivity_score or 0 for s in summaries) / total_sessions
        avg_focus = sum(s.focus_score or 0 for s in summaries) / total_sessions
        total_productive_hours = sum(s.productive_minutes or 0 for s in summaries) / 60
        
        return {
            'avg_productivity': round(avg_productivity, 2),
            'avg_focus': round(avg_focus, 2),
            'total_productive_hours': round(total_productive_hours, 2),
            'total_sessions': total_sessions,
            'daily_breakdown': SessionSummaryCRUD._get_daily_breakdown(summaries)
        }
    
    @staticmethod
    def _get_daily_breakdown(summaries: List[SessionSummary]) -> Dict[str, Dict]:
        """Get daily breakdown of productivity"""
        daily_stats = {}
        
        for summary in summaries:
            date_key = summary.start_time.date().isoformat()
            
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    'sessions': 0,
                    'total_minutes': 0,
                    'productive_minutes': 0,
                    'productivity_scores': []
                }
            
            daily_stats[date_key]['sessions'] += 1
            daily_stats[date_key]['total_minutes'] += summary.duration_minutes or 0
            daily_stats[date_key]['productive_minutes'] += summary.productive_minutes or 0
            daily_stats[date_key]['productivity_scores'].append(summary.productivity_score or 0)
        
        # Calculate daily averages
        for date_key, stats in daily_stats.items():
            scores = stats.pop('productivity_scores')
            stats['avg_productivity'] = round(sum(scores) / len(scores), 2) if scores else 0
            stats['total_hours'] = round(stats['total_minutes'] / 60, 2)
            stats['productive_hours'] = round(stats['productive_minutes'] / 60, 2)
        
        return daily_stats