"""
Activity Monitor - Core system monitoring functionality
Tracks desktop applications, windows, and user activity patterns
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import psutil
import logging

try:
    import pygetwindow as gw
except ImportError:
    gw = None
    logging.warning("pygetwindow not available - window tracking disabled")

class ActivityMonitor:
    """Monitors system activity and user behavior patterns"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.is_monitoring = False
        self.activity_data = []
        
        # Privacy controls
        self.privacy_mode = getattr(config, 'privacy_mode', False)
        self.blocked_apps = getattr(config, 'blocked_apps', set())
        self.incognito_keywords = getattr(config, 'incognito_keywords', ['private', 'incognito', 'password'])
        
        # Activity tracking state
        self.last_activity_time = time.time()
        self.idle_threshold = getattr(config, 'idle_threshold_seconds', 300)  # 5 minutes
        self.current_session = {
            'start_time': datetime.now(),
            'applications': {},
            'websites': {},
            'files_accessed': [],
            'productivity_score': 0.0,
            'idle_periods': []
        }
    
    async def start(self):
        """Start monitoring system activity"""
        self.is_monitoring = True
        self.logger.info("Activity monitoring started")
        
        # Start background monitoring tasks
        asyncio.create_task(self._monitor_processes())
        asyncio.create_task(self._monitor_windows())
        asyncio.create_task(self._monitor_idle_time())
    
    async def stop(self):
        """Stop monitoring"""
        self.is_monitoring = False
        self.logger.info("Activity monitoring stopped")
    
    async def get_current_activity(self) -> Dict[str, Any]:
        """Get current activity snapshot"""
        activity_data = {
            'timestamp': datetime.now().isoformat(),
            'active_window': self._get_active_window(),
            'running_processes': self._get_running_processes(),
            'system_stats': self._get_system_stats(),
            'productivity_indicators': self._calculate_productivity(),
            'session_data': self.current_session.copy()
        }
        
        return self._sanitize_data(activity_data)
    
    async def get_recent_activity(self, hours: int = 24) -> List[Dict]:
        """Get recent activity data for analysis"""
        # This would typically query the database
        # For now, return current session data
        return [await self.get_current_activity()]
    
    async def _monitor_processes(self):
        """Monitor running processes and applications"""
        while self.is_monitoring:
            try:
                processes = {}
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        info = proc.info
                        name = info['name']
                        
                        # Check privacy controls before tracking
                        if not self._should_track_app(name):
                            continue
                        
                        # Track application usage time
                        if name not in self.current_session['applications']:
                            self.current_session['applications'][name] = {
                                'total_time': 0,
                                'cpu_usage': [],
                                'memory_usage': [],
                                'first_seen': datetime.now()
                            }
                        
                        # Update stats
                        app_data = self.current_session['applications'][name]
                        app_data['cpu_usage'].append(info.get('cpu_percent', 0))
                        app_data['memory_usage'].append(info.get('memory_percent', 0))
                        app_data['total_time'] += self.config.monitoring_interval
                        
                        processes[name] = info
                        
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                self.logger.debug(f"Monitored {len(processes)} processes")
                await asyncio.sleep(self.config.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error monitoring processes: {e}")
                await asyncio.sleep(5)
    
    async def _monitor_windows(self):
        """Monitor active windows and titles"""
        if not gw:
            return
        
        while self.is_monitoring:
            try:
                active_window = gw.getActiveWindow()
                if active_window:
                    window_title = active_window.title
                    app_name = self._extract_app_name(window_title)
                    
                    # Check privacy controls before tracking
                    if not self._should_track_window(window_title):
                        continue
                    
                    # Track window focus time
                    current_time = time.time()
                    if hasattr(self, '_last_window') and self._last_window == window_title:
                        focus_time = current_time - self._last_window_time
                        # Add focus time to current app data
                        if app_name in self.current_session['applications']:
                            if 'focus_time' not in self.current_session['applications'][app_name]:
                                self.current_session['applications'][app_name]['focus_time'] = 0
                            self.current_session['applications'][app_name]['focus_time'] += focus_time
                    
                    self._last_window = window_title
                    self._last_window_time = current_time
                
                await asyncio.sleep(1)  # Check windows more frequently
                
            except Exception as e:
                self.logger.error(f"Error monitoring windows: {e}")
                await asyncio.sleep(5)
    
    async def _monitor_idle_time(self):
        """Monitor user idle time to detect breaks"""
        last_check = time.time()
        idle_start = None
        
        while self.is_monitoring:
            try:
                current_time = time.time()
                
                # Check if system is idle based on multiple factors
                cpu_percent = psutil.cpu_percent(interval=1)
                network_activity = self._get_network_activity()
                
                # Consider idle if low CPU and minimal network activity
                is_idle = cpu_percent < 5 and network_activity < 1000  # bytes per second
                
                if is_idle:
                    if idle_start is None:
                        idle_start = current_time
                    elif current_time - idle_start > self.idle_threshold:
                        # Record idle period
                        idle_duration = current_time - idle_start
                        self.current_session['idle_periods'].append({
                            'start': datetime.fromtimestamp(idle_start),
                            'duration_seconds': idle_duration
                        })
                        idle_start = None
                else:
                    self.last_activity_time = current_time
                    idle_start = None
                
                await asyncio.sleep(10)
                
            except Exception as e:
                self.logger.error(f"Error monitoring idle time: {e}")
                await asyncio.sleep(10)
    
    def _get_active_window(self) -> Dict[str, str]:
        """Get information about the currently active window"""
        if not gw:
            return {'title': 'Unknown', 'app': 'Unknown'}
        
        try:
            active_window = gw.getActiveWindow()
            if active_window:
                return {
                    'title': active_window.title,
                    'app': self._extract_app_name(active_window.title)
                }
        except Exception as e:
            self.logger.debug(f"Could not get active window: {e}")
        
        return {'title': 'Unknown', 'app': 'Unknown'}
    
    def _get_running_processes(self) -> List[Dict]:
        """Get list of currently running processes"""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    info = proc.info
                    if info['cpu_percent'] > 0.1:  # Only include active processes
                        processes.append({
                            'pid': info['pid'],
                            'name': info['name'],
                            'cpu_percent': info['cpu_percent']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.logger.error(f"Error getting processes: {e}")
        
        return sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:10]
    
    def _get_system_stats(self) -> Dict[str, float]:
        """Get current system resource usage"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent if psutil.disk_usage('/') else 0,
                'network_sent': psutil.net_io_counters().bytes_sent,
                'network_recv': psutil.net_io_counters().bytes_recv
            }
        except Exception as e:
            self.logger.error(f"Error getting system stats: {e}")
            return {}
    
    def _calculate_productivity(self) -> Dict[str, float]:
        """Calculate productivity indicators based on current activity"""
        # Enhanced productivity categories
        productivity_categories = {
            'development': {
                'apps': ['code.exe', 'pycharm', 'intellij', 'eclipse', 'atom', 'sublime', 'vim', 'emacs'],
                'weight': 1.0
            },
            'research': {
                'apps': ['chrome.exe', 'firefox.exe', 'edge.exe', 'safari.exe'],
                'weight': 0.8
            },
            'documentation': {
                'apps': ['notepad++.exe', 'word.exe', 'libreoffice', 'notion', 'obsidian'],
                'weight': 0.9
            },
            'communication': {
                'apps': ['slack.exe', 'teams.exe', 'zoom.exe', 'outlook.exe'],
                'weight': 0.7
            },
            'terminal': {
                'apps': ['cmd.exe', 'powershell.exe', 'terminal.exe', 'bash', 'zsh'],
                'weight': 1.0
            }
        }
        
        non_productive_apps = {
            'discord.exe', 'spotify.exe', 'steam.exe', 'games', 'netflix', 'youtube',
            'tiktok', 'instagram', 'facebook', 'twitter', 'reddit'
        }
        
        total_time = sum(app_data['total_time'] for app_data in self.current_session['applications'].values())
        if total_time == 0:
            return {
                'productivity_score': 0.0, 
                'focus_score': 0.0, 
                'active_time_minutes': 0.0,
                'distraction_score': 0.0,
                'break_efficiency': 0.0
            }
        
        # Calculate weighted productive time
        weighted_productive_time = 0
        category_breakdown = {}
        
        for app_name, app_data in self.current_session['applications'].items():
            app_time = app_data['total_time']
            app_lower = app_name.lower()
            
            # Check productivity categories
            for category, config in productivity_categories.items():
                if any(prod_app in app_lower for prod_app in config['apps']):
                    weighted_time = app_time * config['weight']
                    weighted_productive_time += weighted_time
                    category_breakdown[category] = category_breakdown.get(category, 0) + app_time
                    break
        
        # Calculate distraction time
        distraction_time = sum(
            app_data['total_time']
            for app_name, app_data in self.current_session['applications'].items()
            if any(dist_app in app_name.lower() for dist_app in non_productive_apps)
        )
        
        # Productivity score (0-100)
        productivity_score = (weighted_productive_time / total_time) * 100 if total_time > 0 else 0
        
        # Focus score based on app switching and session depth
        app_switches = len(self.current_session['applications'])
        avg_session_time = total_time / app_switches if app_switches > 0 else 0
        
        # Higher focus for fewer apps and longer average sessions
        focus_base = max(0, 100 - (app_switches * 3))
        focus_depth_bonus = min(20, avg_session_time / 600)  # Bonus for 10+ min sessions
        focus_score = min(100, focus_base + focus_depth_bonus)
        
        # Distraction score
        distraction_score = (distraction_time / total_time) * 100 if total_time > 0 else 0
        
        # Break efficiency (based on idle periods)
        total_idle_time = sum(period['duration_seconds'] for period in self.current_session['idle_periods'])
        total_session_time = (datetime.now() - self.current_session['start_time']).total_seconds()
        break_ratio = total_idle_time / total_session_time if total_session_time > 0 else 0
        
        # Optimal break ratio is around 15-20%
        if 0.10 <= break_ratio <= 0.25:
            break_efficiency = 100
        elif break_ratio < 0.10:
            break_efficiency = break_ratio * 1000  # Under-breaking penalty
        else:
            break_efficiency = max(0, 100 - ((break_ratio - 0.25) * 200))  # Over-breaking penalty
        
        return {
            'productivity_score': round(productivity_score, 2),
            'focus_score': round(focus_score, 2),
            'distraction_score': round(distraction_score, 2),
            'break_efficiency': round(break_efficiency, 2),
            'active_time_minutes': round(total_time / 60, 2),
            'category_breakdown': {k: round(v / 60, 2) for k, v in category_breakdown.items()}
        }
    
    def _extract_app_name(self, window_title: str) -> str:
        """Extract application name from window title"""
        # Simple heuristic to extract app name
        common_separators = [' - ', ' — ', ' | ', ' :: ']
        
        for sep in common_separators:
            if sep in window_title:
                return window_title.split(sep)[-1].strip()
        
        return window_title.split()[0] if window_title else 'Unknown'
    
    def _get_network_activity(self) -> float:
        """Get current network activity in bytes per second"""
        try:
            # Get network stats and calculate activity rate
            net_io = psutil.net_io_counters()
            current_time = time.time()
            
            if hasattr(self, '_last_net_check'):
                time_diff = current_time - self._last_net_check_time
                bytes_diff = (net_io.bytes_sent + net_io.bytes_recv) - self._last_net_bytes
                activity_rate = bytes_diff / time_diff if time_diff > 0 else 0
            else:
                activity_rate = 0
            
            self._last_net_check = net_io
            self._last_net_check_time = current_time
            self._last_net_bytes = net_io.bytes_sent + net_io.bytes_recv
            
            return activity_rate
        except Exception:
            return 0
    
    def _should_track_app(self, app_name: str) -> bool:
        """Check if app should be tracked based on privacy settings"""
        if self.privacy_mode:
            return False
        
        if app_name.lower() in self.blocked_apps:
            return False
        
        return True
    
    def _should_track_window(self, window_title: str) -> bool:
        """Check if window should be tracked based on privacy settings"""
        if self.privacy_mode:
            return False
        
        title_lower = window_title.lower()
        for keyword in self.incognito_keywords:
            if keyword in title_lower:
                return False
        
        return True
    
    def _sanitize_data(self, data: Dict) -> Dict:
        """Sanitize sensitive data based on privacy settings"""
        if not self.privacy_mode:
            return data
        
        # Remove or obfuscate sensitive information
        sanitized = data.copy()
        if 'active_window' in sanitized:
            sanitized['active_window'] = {'title': '[PRIVATE]', 'app': '[PRIVATE]'}
        
        return sanitized
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        session_duration = datetime.now() - self.current_session['start_time']
        
        # Find most used applications
        top_apps = sorted(
            self.current_session['applications'].items(),
            key=lambda x: x[1]['total_time'],
            reverse=True
        )[:5]
        
        return {
            'session_duration': str(session_duration),
            'total_applications': len(self.current_session['applications']),
            'top_applications': [
                {
                    'name': app_name,
                    'time_minutes': round(app_data['total_time'] / 60, 2)
                }
                for app_name, app_data in top_apps
            ],
            'productivity_metrics': self._calculate_productivity()
        }
