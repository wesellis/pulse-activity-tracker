"""
Time Compensation Engine for Pulse Activity Tracker
Handles time debt calculation, smart scheduling, and energy-based task optimization
"""

import json
from datetime import datetime, timedelta, time
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import logging
from collections import defaultdict

from ..utils.config import Config


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class EnergyLevel(Enum):
    """Energy level classifications"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    PEAK = 4


class SchedulePreference(Enum):
    """User's scheduling preferences"""
    IMMEDIATE = "immediate"
    DELAYED = "delayed"
    DISTRIBUTED = "distributed"
    FLEXIBLE = "flexible"


@dataclass
class TimeDebt:
    """Represents accumulated time debt"""
    deficit_hours: float
    surplus_hours: float
    net_balance: float
    last_calculated: datetime
    weekly_target: float
    daily_target: float


@dataclass
class CompensationTask:
    """Task with compensation scheduling information"""
    id: str
    title: str
    estimated_duration: float  # hours
    priority: TaskPriority
    required_energy: EnergyLevel
    deadline: Optional[datetime]
    context: str  # work, personal, health, etc.
    flexibility: float  # 0-1, how flexible the timing is
    compensation_for: Optional[str]  # what this compensates for


@dataclass
class TimeSlot:
    """Available time slot for scheduling"""
    start_time: datetime
    end_time: datetime
    available_energy: EnergyLevel
    context_type: str
    duration_hours: float
    quality_score: float  # 0-1, how good this slot is for productive work


class EnergyProfileAnalyzer:
    """Analyzes user's energy patterns for optimal scheduling"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def analyze_energy_patterns(self, activity_data: List[Dict]) -> Dict[str, Any]:
        """Analyze user's energy patterns throughout the day"""
        if not activity_data:
            return self._get_default_energy_pattern()
        
        hourly_performance = defaultdict(list)
        daily_patterns = defaultdict(list)
        
        for activity in activity_data:
            timestamp = activity.get('timestamp')
            productivity = activity.get('productivity_score', 0)
            focus = activity.get('focus_score', 0)
            
            if timestamp and productivity and focus:
                try:
                    if isinstance(timestamp, str):
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        dt = timestamp
                    
                    hour = dt.hour
                    weekday = dt.weekday()  # 0=Monday, 6=Sunday
                    
                    # Combine productivity and focus for energy score
                    energy_score = (productivity + focus) / 2
                    hourly_performance[hour].append(energy_score)
                    daily_patterns[weekday].append(energy_score)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to parse timestamp {timestamp}: {e}")
                    continue
        
        # Calculate hourly energy levels
        hourly_energy = {}
        for hour, scores in hourly_performance.items():
            avg_score = sum(scores) / len(scores) if scores else 50
            hourly_energy[hour] = self._classify_energy_level(avg_score)
        
        # Calculate daily energy patterns
        daily_energy = {}
        for day, scores in daily_patterns.items():
            avg_score = sum(scores) / len(scores) if scores else 50
            daily_energy[day] = self._classify_energy_level(avg_score)
        
        return {
            'hourly_energy_levels': hourly_energy,
            'daily_energy_patterns': daily_energy,
            'peak_hours': self._find_peak_hours(hourly_energy),
            'low_energy_periods': self._find_low_energy_periods(hourly_energy),
            'energy_type': self._determine_energy_type(hourly_energy),
            'weekly_rhythm': self._analyze_weekly_rhythm(daily_energy)
        }
    
    def _get_default_energy_pattern(self) -> Dict[str, Any]:
        """Return default energy pattern for new users"""
        return {
            'hourly_energy_levels': {
                hour: EnergyLevel.MEDIUM for hour in range(9, 17)
            },
            'daily_energy_patterns': {
                day: EnergyLevel.MEDIUM for day in range(7)
            },
            'peak_hours': [10, 11, 14, 15],
            'low_energy_periods': [13, 16, 17],
            'energy_type': 'balanced',
            'weekly_rhythm': 'consistent'
        }
    
    def _classify_energy_level(self, score: float) -> EnergyLevel:
        """Classify energy level based on score"""
        if score >= 85:
            return EnergyLevel.PEAK
        elif score >= 70:
            return EnergyLevel.HIGH
        elif score >= 50:
            return EnergyLevel.MEDIUM
        else:
            return EnergyLevel.LOW
    
    def _find_peak_hours(self, hourly_energy: Dict[int, EnergyLevel]) -> List[int]:
        """Find peak energy hours"""
        return [hour for hour, level in hourly_energy.items() 
                if level in [EnergyLevel.PEAK, EnergyLevel.HIGH]]
    
    def _find_low_energy_periods(self, hourly_energy: Dict[int, EnergyLevel]) -> List[int]:
        """Find low energy periods"""
        return [hour for hour, level in hourly_energy.items() 
                if level == EnergyLevel.LOW]
    
    def _determine_energy_type(self, hourly_energy: Dict[int, EnergyLevel]) -> str:
        """Determine if user is morning/afternoon/evening person"""
        morning_energy = sum(1 for hour in range(6, 12) 
                           if hourly_energy.get(hour, EnergyLevel.LOW) in [EnergyLevel.HIGH, EnergyLevel.PEAK])
        afternoon_energy = sum(1 for hour in range(12, 18) 
                             if hourly_energy.get(hour, EnergyLevel.LOW) in [EnergyLevel.HIGH, EnergyLevel.PEAK])
        evening_energy = sum(1 for hour in range(18, 22) 
                           if hourly_energy.get(hour, EnergyLevel.LOW) in [EnergyLevel.HIGH, EnergyLevel.PEAK])
        
        max_energy = max(morning_energy, afternoon_energy, evening_energy)
        if max_energy == morning_energy:
            return 'morning'
        elif max_energy == afternoon_energy:
            return 'afternoon'
        else:
            return 'evening'
    
    def _analyze_weekly_rhythm(self, daily_energy: Dict[int, EnergyLevel]) -> str:
        """Analyze weekly energy rhythm"""
        weekday_avg = sum(level.value for day, level in daily_energy.items() if day < 5) / 5
        weekend_avg = sum(level.value for day, level in daily_energy.items() if day >= 5) / 2
        
        if abs(weekday_avg - weekend_avg) < 0.5:
            return 'consistent'
        elif weekday_avg > weekend_avg:
            return 'weekday_focused'
        else:
            return 'weekend_recovery'


class TimeDebtCalculator:
    """Calculates and tracks time debt/surplus"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.weekly_target = config.weekly_target_hours if hasattr(config, 'weekly_target_hours') else 40.0
        self.daily_target = self.weekly_target / 7
    
    def calculate_current_debt(self, activity_data: List[Dict], period_days: int = 7) -> TimeDebt:
        """Calculate current time debt/surplus"""
        if not activity_data:
            return TimeDebt(
                deficit_hours=0,
                surplus_hours=0,
                net_balance=0,
                last_calculated=datetime.now(),
                weekly_target=self.weekly_target,
                daily_target=self.daily_target
            )
        
        # Calculate actual productive hours
        total_productive_hours = 0
        productive_days = set()
        
        for activity in activity_data:
            duration = activity.get('duration', 0)
            productivity_score = activity.get('productivity_score', 0)
            timestamp = activity.get('timestamp')
            
            if duration and productivity_score >= 50 and timestamp:  # Only count productive time
                try:
                    if isinstance(timestamp, str):
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        dt = timestamp
                    
                    productive_days.add(dt.date())
                    total_productive_hours += duration / 3600  # Convert seconds to hours
                    
                except Exception as e:
                    self.logger.warning(f"Failed to parse timestamp {timestamp}: {e}")
                    continue
        
        # Calculate expected hours for the period
        actual_days = len(productive_days) if productive_days else period_days
        expected_hours = actual_days * self.daily_target
        
        # Calculate debt/surplus
        net_balance = total_productive_hours - expected_hours
        deficit_hours = max(0, -net_balance)
        surplus_hours = max(0, net_balance)
        
        return TimeDebt(
            deficit_hours=deficit_hours,
            surplus_hours=surplus_hours,
            net_balance=net_balance,
            last_calculated=datetime.now(),
            weekly_target=self.weekly_target,
            daily_target=self.daily_target
        )
    
    def project_future_debt(self, current_debt: TimeDebt, days_ahead: int) -> Dict[str, float]:
        """Project future time debt if current patterns continue"""
        daily_deficit = current_debt.deficit_hours / 7  # Average daily deficit
        
        projections = {}
        for days in [1, 3, 7, 14, 30]:
            if days <= days_ahead:
                future_deficit = current_debt.deficit_hours + (daily_deficit * days)
                projections[f'{days}_days'] = future_deficit
        
        return projections
    
    def calculate_makeup_schedule(self, debt: TimeDebt, preference: SchedulePreference) -> List[Dict[str, Any]]:
        """Calculate optimal makeup schedule for time debt"""
        if debt.deficit_hours <= 0:
            return []
        
        makeup_sessions = []
        remaining_hours = debt.deficit_hours
        
        if preference == SchedulePreference.IMMEDIATE:
            # Concentrate makeup in next few days
            daily_makeup = min(2.0, remaining_hours / 3)  # Max 2 hours per day
            days_needed = int(remaining_hours / daily_makeup) + 1
            
            for day in range(days_needed):
                session_hours = min(daily_makeup, remaining_hours)
                if session_hours > 0:
                    makeup_sessions.append({
                        'day_offset': day + 1,
                        'hours': session_hours,
                        'type': 'intensive_makeup',
                        'flexibility': 0.3
                    })
                    remaining_hours -= session_hours
        
        elif preference == SchedulePreference.DISTRIBUTED:
            # Spread over 2 weeks
            daily_makeup = remaining_hours / 14
            
            for day in range(14):
                if daily_makeup > 0.5:  # Only schedule if significant time
                    makeup_sessions.append({
                        'day_offset': day + 1,
                        'hours': daily_makeup,
                        'type': 'distributed_makeup',
                        'flexibility': 0.7
                    })
        
        elif preference == SchedulePreference.DELAYED:
            # Schedule for next week
            daily_makeup = remaining_hours / 5  # Spread over 5 weekdays
            
            for day in range(7, 12):  # Start from next week
                makeup_sessions.append({
                    'day_offset': day,
                    'hours': daily_makeup,
                    'type': 'delayed_makeup',
                    'flexibility': 0.8
                })
        
        return makeup_sessions


class SmartScheduler:
    """Intelligent task scheduler based on energy levels and preferences"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.energy_analyzer = EnergyProfileAnalyzer(config)
        self.debt_calculator = TimeDebtCalculator(config)
    
    def generate_optimal_schedule(
        self,
        tasks: List[CompensationTask],
        available_slots: List[TimeSlot],
        energy_profile: Dict[str, Any],
        user_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate optimal schedule for compensation tasks"""
        
        # Sort tasks by priority and deadline
        sorted_tasks = sorted(tasks, key=lambda t: (
            t.deadline.timestamp() if t.deadline else float('inf'),
            -t.priority.value,
            -t.required_energy.value
        ))
        
        # Sort slots by quality and energy level
        sorted_slots = sorted(available_slots, key=lambda s: (
            -s.quality_score,
            -s.available_energy.value,
            s.duration_hours
        ))
        
        schedule = {}
        unscheduled_tasks = []
        
        for task in sorted_tasks:
            best_slot = self._find_best_slot(task, sorted_slots, energy_profile)
            
            if best_slot:
                schedule[task.id] = {
                    'task': task,
                    'slot': best_slot,
                    'start_time': best_slot.start_time,
                    'end_time': best_slot.start_time + timedelta(hours=task.estimated_duration),
                    'energy_match': self._calculate_energy_match(task.required_energy, best_slot.available_energy),
                    'efficiency_score': self._calculate_efficiency_score(task, best_slot)
                }
                
                # Remove used time from slot
                self._update_slot_availability(best_slot, task.estimated_duration, sorted_slots)
            else:
                unscheduled_tasks.append(task)
        
        return {
            'scheduled_tasks': schedule,
            'unscheduled_tasks': unscheduled_tasks,
            'total_scheduled_hours': sum(task.estimated_duration for task in tasks if task.id in schedule),
            'schedule_efficiency': self._calculate_overall_efficiency(schedule),
            'recommendations': self._generate_scheduling_recommendations(schedule, unscheduled_tasks)
        }
    
    def _find_best_slot(
        self,
        task: CompensationTask,
        available_slots: List[TimeSlot],
        energy_profile: Dict[str, Any]
    ) -> Optional[TimeSlot]:
        """Find the best available slot for a task"""
        
        for slot in available_slots:
            if slot.duration_hours >= task.estimated_duration:
                # Check energy level compatibility
                energy_match = self._calculate_energy_match(task.required_energy, slot.available_energy)
                
                # Check context compatibility
                context_match = self._check_context_compatibility(task.context, slot.context_type)
                
                # Check deadline constraints
                deadline_ok = True
                if task.deadline:
                    task_end_time = slot.start_time + timedelta(hours=task.estimated_duration)
                    deadline_ok = task_end_time <= task.deadline
                
                if energy_match >= 0.6 and context_match and deadline_ok:
                    return slot
        
        return None
    
    def _calculate_energy_match(self, required: EnergyLevel, available: EnergyLevel) -> float:
        """Calculate how well required energy matches available energy"""
        if available.value >= required.value:
            return 1.0 - (0.2 * (available.value - required.value))
        else:
            return 0.6 - (0.3 * (required.value - available.value))
    
    def _check_context_compatibility(self, task_context: str, slot_context: str) -> bool:
        """Check if task context is compatible with time slot context"""
        compatible_contexts = {
            'work': ['work', 'mixed'],
            'personal': ['personal', 'mixed'],
            'health': ['personal', 'health', 'mixed'],
            'admin': ['personal', 'work', 'mixed']
        }
        
        return slot_context in compatible_contexts.get(task_context, [task_context])
    
    def _calculate_efficiency_score(self, task: CompensationTask, slot: TimeSlot) -> float:
        """Calculate efficiency score for task-slot pairing"""
        energy_match = self._calculate_energy_match(task.required_energy, slot.available_energy)
        time_efficiency = min(1.0, slot.duration_hours / task.estimated_duration)
        quality_score = slot.quality_score
        
        return (energy_match * 0.4 + time_efficiency * 0.3 + quality_score * 0.3)
    
    def _update_slot_availability(self, slot: TimeSlot, used_hours: float, all_slots: List[TimeSlot]):
        """Update slot availability after scheduling a task"""
        if slot.duration_hours <= used_hours:
            # Remove slot completely
            if slot in all_slots:
                all_slots.remove(slot)
        else:
            # Update slot start time and duration
            slot.start_time += timedelta(hours=used_hours)
            slot.duration_hours -= used_hours
    
    def _calculate_overall_efficiency(self, schedule: Dict[str, Any]) -> float:
        """Calculate overall scheduling efficiency"""
        if not schedule:
            return 0.0
        
        efficiency_scores = [item['efficiency_score'] for item in schedule.values()]
        return sum(efficiency_scores) / len(efficiency_scores)
    
    def _generate_scheduling_recommendations(
        self,
        schedule: Dict[str, Any],
        unscheduled_tasks: List[CompensationTask]
    ) -> List[str]:
        """Generate recommendations for schedule optimization"""
        recommendations = []
        
        if unscheduled_tasks:
            urgent_unscheduled = [t for t in unscheduled_tasks if t.priority == TaskPriority.URGENT]
            if urgent_unscheduled:
                recommendations.append(f"⚠️ {len(urgent_unscheduled)} urgent tasks couldn't be scheduled - consider clearing time")
            
            recommendations.append(f"📅 {len(unscheduled_tasks)} tasks need rescheduling - try extending available time slots")
        
        if schedule:
            avg_efficiency = self._calculate_overall_efficiency(schedule)
            if avg_efficiency < 0.7:
                recommendations.append("🎯 Consider adjusting energy requirements or time slots for better efficiency")
            
            # Check for energy mismatches
            energy_mismatches = sum(1 for item in schedule.values() if item['energy_match'] < 0.7)
            if energy_mismatches > 0:
                recommendations.append(f"⚡ {energy_mismatches} tasks scheduled during suboptimal energy periods")
        
        return recommendations


class CompensationEngine:
    """Main compensation engine that coordinates all time management features"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.energy_analyzer = EnergyProfileAnalyzer(config)
        self.debt_calculator = TimeDebtCalculator(config)
        self.scheduler = SmartScheduler(config)
    
    def analyze_and_compensate(
        self,
        activity_data: List[Dict],
        tasks: List[CompensationTask],
        user_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform comprehensive analysis and generate compensation plan"""
        
        # Analyze current situation
        energy_profile = self.energy_analyzer.analyze_energy_patterns(activity_data)
        time_debt = self.debt_calculator.calculate_current_debt(activity_data)
        
        # Generate available time slots based on energy profile
        available_slots = self._generate_available_slots(energy_profile, user_preferences)
        
        # Create compensation tasks for time debt
        debt_tasks = self._create_debt_compensation_tasks(time_debt, user_preferences)
        all_tasks = tasks + debt_tasks
        
        # Generate optimal schedule
        schedule = self.scheduler.generate_optimal_schedule(
            all_tasks, available_slots, energy_profile, user_preferences
        )
        
        return {
            'energy_profile': energy_profile,
            'time_debt': time_debt.__dict__,
            'compensation_tasks': [task.__dict__ for task in debt_tasks],
            'schedule': schedule,
            'insights': self._generate_compensation_insights(energy_profile, time_debt, schedule),
            'recommendations': self._generate_compensation_recommendations(energy_profile, time_debt, schedule),
            'next_actions': self._suggest_next_actions(schedule, time_debt)
        }
    
    def _generate_available_slots(
        self,
        energy_profile: Dict[str, Any],
        user_preferences: Dict[str, Any]
    ) -> List[TimeSlot]:
        """Generate available time slots based on energy profile and preferences"""
        slots = []
        
        # Get user's work hours
        work_start = user_preferences.get('work_hours_start', 9)
        work_end = user_preferences.get('work_hours_end', 17)
        
        # Generate slots for next 7 days
        for day_offset in range(7):
            current_date = datetime.now().date() + timedelta(days=day_offset)
            
            # Work hours slot
            work_start_time = datetime.combine(current_date, time(work_start))
            work_end_time = datetime.combine(current_date, time(work_end))
            
            slots.append(TimeSlot(
                start_time=work_start_time,
                end_time=work_end_time,
                available_energy=self._get_energy_for_period(work_start, work_end, energy_profile),
                context_type='work',
                duration_hours=work_end - work_start,
                quality_score=0.9
            ))
            
            # Evening personal time slot
            evening_start = datetime.combine(current_date, time(19))
            evening_end = datetime.combine(current_date, time(21))
            
            slots.append(TimeSlot(
                start_time=evening_start,
                end_time=evening_end,
                available_energy=self._get_energy_for_period(19, 21, energy_profile),
                context_type='personal',
                duration_hours=2,
                quality_score=0.6
            ))
        
        return slots
    
    def _get_energy_for_period(self, start_hour: int, end_hour: int, energy_profile: Dict[str, Any]) -> EnergyLevel:
        """Get average energy level for a time period"""
        hourly_energy = energy_profile.get('hourly_energy_levels', {})
        
        energy_values = []
        for hour in range(start_hour, end_hour):
            energy_level = hourly_energy.get(hour, EnergyLevel.MEDIUM)
            if isinstance(energy_level, EnergyLevel):
                energy_values.append(energy_level.value)
            else:
                energy_values.append(EnergyLevel.MEDIUM.value)
        
        if energy_values:
            avg_value = sum(energy_values) / len(energy_values)
            return EnergyLevel(round(avg_value))
        
        return EnergyLevel.MEDIUM
    
    def _create_debt_compensation_tasks(
        self,
        time_debt: TimeDebt,
        user_preferences: Dict[str, Any]
    ) -> List[CompensationTask]:
        """Create tasks to compensate for time debt"""
        tasks = []
        
        if time_debt.deficit_hours > 0:
            # Break down debt into manageable chunks
            chunk_size = user_preferences.get('max_daily_makeup', 2.0)
            chunks_needed = int(time_debt.deficit_hours / chunk_size) + 1
            
            for i in range(chunks_needed):
                remaining_debt = time_debt.deficit_hours - (i * chunk_size)
                chunk_hours = min(chunk_size, remaining_debt)
                
                if chunk_hours > 0:
                    tasks.append(CompensationTask(
                        id=f"debt_compensation_{i+1}",
                        title=f"Time Makeup Session {i+1}",
                        estimated_duration=chunk_hours,
                        priority=TaskPriority.HIGH,
                        required_energy=EnergyLevel.MEDIUM,
                        deadline=datetime.now() + timedelta(days=7),
                        context='work',
                        flexibility=0.7,
                        compensation_for=f"time_debt_{chunk_hours:.1f}h"
                    ))
        
        return tasks
    
    def _generate_compensation_insights(
        self,
        energy_profile: Dict[str, Any],
        time_debt: TimeDebt,
        schedule: Dict[str, Any]
    ) -> List[str]:
        """Generate insights about compensation and scheduling"""
        insights = []
        
        # Time debt insights
        if time_debt.deficit_hours > 4:
            insights.append(f"⏰ Significant time deficit of {time_debt.deficit_hours:.1f} hours detected")
        elif time_debt.surplus_hours > 2:
            insights.append(f"🎉 Time surplus of {time_debt.surplus_hours:.1f} hours - great work!")
        
        # Energy insights
        energy_type = energy_profile.get('energy_type', 'unknown')
        peak_hours = energy_profile.get('peak_hours', [])
        if peak_hours:
            insights.append(f"⚡ Your peak energy hours are {min(peak_hours)}-{max(peak_hours)}:00")
        
        # Schedule insights
        scheduled_tasks = schedule.get('scheduled_tasks', {})
        if scheduled_tasks:
            efficiency = schedule.get('schedule_efficiency', 0)
            insights.append(f"📅 {len(scheduled_tasks)} tasks scheduled with {efficiency:.1%} efficiency")
        
        unscheduled_count = len(schedule.get('unscheduled_tasks', []))
        if unscheduled_count > 0:
            insights.append(f"⚠️ {unscheduled_count} tasks couldn't be scheduled - need more available time")
        
        return insights
    
    def _generate_compensation_recommendations(
        self,
        energy_profile: Dict[str, Any],
        time_debt: TimeDebt,
        schedule: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Time debt recommendations
        if time_debt.deficit_hours > 0:
            recommendations.append(f"📊 Schedule {time_debt.deficit_hours:.1f} hours of makeup time this week")
            recommendations.append("🎯 Focus on high-productivity tasks during makeup sessions")
        
        # Energy optimization recommendations
        energy_type = energy_profile.get('energy_type', 'balanced')
        if energy_type == 'morning':
            recommendations.append("🌅 Schedule demanding tasks before 11 AM when your energy peaks")
        elif energy_type == 'evening':
            recommendations.append("🌙 Save complex work for after 3 PM when you hit your stride")
        
        # Schedule optimization recommendations
        efficiency = schedule.get('schedule_efficiency', 0)
        if efficiency < 0.7:
            recommendations.append("⚡ Consider adjusting task timing to match your energy levels")
        
        unscheduled = schedule.get('unscheduled_tasks', [])
        if unscheduled:
            recommendations.append("📅 Block additional time slots to accommodate all tasks")
        
        return recommendations
    
    def _suggest_next_actions(self, schedule: Dict[str, Any], time_debt: TimeDebt) -> List[str]:
        """Suggest immediate next actions"""
        actions = []
        
        scheduled_tasks = schedule.get('scheduled_tasks', {})
        if scheduled_tasks:
            # Find next scheduled task
            next_task = min(scheduled_tasks.values(), key=lambda x: x['start_time'])
            actions.append(f"⏭️ Next: {next_task['task'].title} at {next_task['start_time'].strftime('%H:%M')}")
        
        if time_debt.deficit_hours > 0:
            actions.append("📝 Review and prioritize compensation tasks")
            actions.append("⏰ Block time in calendar for makeup sessions")
        
        actions.append("🔄 Review energy patterns after completing scheduled tasks")
        
        return actions