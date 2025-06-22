"""
Database models for Pulse Activity Tracker
Defines all SQLAlchemy models for data persistence
"""

from datetime import datetime
from typing import Optional, Dict, Any
import json
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, JSON,
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

Base = declarative_base()


class Activity(Base):
    """Stores captured activity data from monitoring sessions"""
    __tablename__ = 'activities'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Window and application data
    window_title = Column(String(500))
    application_name = Column(String(255), index=True)
    application_path = Column(String(500))
    
    # Activity metrics
    duration_seconds = Column(Float, default=0)
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    
    # Productivity tracking
    category = Column(String(50), index=True)  # development, research, communication, etc.
    productivity_score = Column(Float)
    is_productive = Column(Boolean, default=True)
    
    # Privacy controls
    is_private = Column(Boolean, default=False)
    sanitized_data = Column(JSON)  # Store sanitized version if privacy mode
    
    # System context
    system_idle = Column(Boolean, default=False)
    network_activity = Column(Float)  # bytes per second
    
    # Session reference
    session_id = Column(String(36), index=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_activity_session_time', 'session_id', 'timestamp'),
        Index('idx_activity_app_time', 'application_name', 'timestamp'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'window_title': self.window_title if not self.is_private else '[PRIVATE]',
            'application_name': self.application_name,
            'duration_seconds': self.duration_seconds,
            'category': self.category,
            'productivity_score': self.productivity_score,
            'is_productive': self.is_productive,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage
        }


class Todo(Base):
    """Stores automatically generated and user-created todos"""
    __tablename__ = 'todos'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Todo content
    title = Column(String(255), nullable=False)
    description = Column(Text)
    priority = Column(String(20), default='medium')  # low, medium, high, urgent
    status = Column(String(20), default='pending')  # pending, in_progress, completed, cancelled
    
    # Categorization
    category = Column(String(50))  # work, personal, health, learning
    tags = Column(JSON)  # List of tags
    
    # Time management
    due_date = Column(DateTime)
    estimated_minutes = Column(Integer)
    actual_minutes = Column(Integer)
    completed_at = Column(DateTime)
    
    # AI generation metadata
    is_ai_generated = Column(Boolean, default=False)
    generation_reason = Column(Text)  # Why AI created this todo
    confidence_score = Column(Float)  # AI confidence in the suggestion
    
    # Recurrence
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON)  # {type: 'daily', interval: 1, days: [1,3,5]}
    parent_todo_id = Column(Integer, ForeignKey('todos.id'))
    
    # Relationships
    parent_todo = relationship('Todo', remote_side=[id])
    patterns = relationship('Pattern', secondary='todo_patterns', back_populates='todos')
    
    # Constraints
    __table_args__ = (
        CheckConstraint(priority.in_(['low', 'medium', 'high', 'urgent']), name='valid_priority'),
        CheckConstraint(status.in_(['pending', 'in_progress', 'completed', 'cancelled']), name='valid_status'),
        Index('idx_todo_status_priority', 'status', 'priority'),
    )
    
    @validates('priority')
    def validate_priority(self, key, value):
        valid_priorities = ['low', 'medium', 'high', 'urgent']
        if value not in valid_priorities:
            raise ValueError(f"Priority must be one of {valid_priorities}")
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'category': self.category,
            'tags': self.tags or [],
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_ai_generated': self.is_ai_generated,
            'is_recurring': self.is_recurring
        }


class Pattern(Base):
    """Stores detected behavioral patterns and insights"""
    __tablename__ = 'patterns'
    
    id = Column(Integer, primary_key=True)
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Pattern identification
    pattern_type = Column(String(50), nullable=False)  # productivity, distraction, break, overwork
    pattern_name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Pattern metrics
    confidence_score = Column(Float, nullable=False)  # 0-1 confidence in pattern
    occurrence_count = Column(Integer, default=1)
    last_occurrence = Column(DateTime)
    
    # Pattern details
    trigger_conditions = Column(JSON)  # What triggers this pattern
    impact_metrics = Column(JSON)  # How it affects productivity
    recommendations = Column(JSON)  # Suggested actions
    
    # Time analysis
    typical_time = Column(String(50))  # "morning", "afternoon", "evening", "late_night"
    typical_day = Column(String(50))  # "weekday", "weekend", "monday", etc.
    duration_minutes = Column(Float)
    
    # Associated data
    related_apps = Column(JSON)  # Apps involved in pattern
    related_categories = Column(JSON)  # Categories involved
    
    # Status
    is_active = Column(Boolean, default=True)
    is_positive = Column(Boolean)  # Positive or negative pattern
    
    # Relationships
    todos = relationship('Todo', secondary='todo_patterns', back_populates='patterns')
    
    # Indexes
    __table_args__ = (
        Index('idx_pattern_type_active', 'pattern_type', 'is_active'),
        Index('idx_pattern_confidence', 'confidence_score'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'pattern_type': self.pattern_type,
            'pattern_name': self.pattern_name,
            'description': self.description,
            'confidence_score': self.confidence_score,
            'is_positive': self.is_positive,
            'recommendations': self.recommendations or [],
            'last_occurrence': self.last_occurrence.isoformat() if self.last_occurrence else None
        }


class Report(Base):
    """Stores generated reports and analytics"""
    __tablename__ = 'reports'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Report metadata
    report_type = Column(String(50), nullable=False)  # daily, weekly, monthly, custom
    report_name = Column(String(255), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Report content
    summary = Column(Text)
    metrics = Column(JSON)  # Key metrics and statistics
    insights = Column(JSON)  # AI-generated insights
    recommendations = Column(JSON)  # Actionable recommendations
    
    # Visualizations
    charts_data = Column(JSON)  # Data for rendering charts
    
    # Export info
    export_format = Column(String(20))  # pdf, html, json, csv
    export_path = Column(String(500))
    
    # Sharing
    is_shared = Column(Boolean, default=False)
    share_token = Column(String(64), unique=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_report_type_period', 'report_type', 'period_start', 'period_end'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'report_type': self.report_type,
            'report_name': self.report_name,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'summary': self.summary,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SessionSummary(Base):
    """Stores aggregated session data for quick access"""
    __tablename__ = 'session_summaries'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(36), unique=True, nullable=False)
    
    # Session timing
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration_minutes = Column(Float)
    
    # Productivity metrics
    productivity_score = Column(Float)
    focus_score = Column(Float)
    distraction_score = Column(Float)
    break_efficiency = Column(Float)
    
    # Activity summary
    total_applications = Column(Integer, default=0)
    productive_minutes = Column(Float, default=0)
    distracted_minutes = Column(Float, default=0)
    idle_minutes = Column(Float, default=0)
    
    # Category breakdown
    category_breakdown = Column(JSON)  # {category: minutes}
    top_applications = Column(JSON)  # [{name, minutes, category}]
    
    # Patterns detected
    patterns_detected = Column(JSON)  # Pattern IDs detected this session
    todos_generated = Column(Integer, default=0)
    
    # System metrics
    avg_cpu_usage = Column(Float)
    avg_memory_usage = Column(Float)
    
    # Indexes
    __table_args__ = (
        Index('idx_session_time', 'start_time', 'end_time'),
        Index('idx_session_productivity', 'productivity_score'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_minutes': self.duration_minutes,
            'productivity_score': self.productivity_score,
            'focus_score': self.focus_score,
            'category_breakdown': self.category_breakdown or {},
            'top_applications': self.top_applications or []
        }


# Association table for many-to-many relationship between todos and patterns
todo_patterns = Base.metadata.tables.get('todo_patterns')
if not todo_patterns:
    from sqlalchemy import Table
    todo_patterns = Table('todo_patterns', Base.metadata,
        Column('todo_id', Integer, ForeignKey('todos.id'), primary_key=True),
        Column('pattern_id', Integer, ForeignKey('patterns.id'), primary_key=True)
    )