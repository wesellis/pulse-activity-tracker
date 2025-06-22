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
        
        # Activity tracking state
        self.last_activity_time = time.time()
        self.current_session = {
            'start_time': datetime.now(),
            'applications': {},
            'websites': {},
            'files_accessed': [],
            'productivity_score': 0.0
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
        return {
            'timestamp': datetime.now().isoformat(),
            'active_window': self._get_active_window(),
            'running_processes': self._get_running_processes(),
            'system_stats': self._get_system_stats(),
            'productivity_indicators': self._calculate_productivity(),
            'session_data': self.current_session.copy()
        }
    
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
                    
                    # Track window focus time
                    current_time = time.time()
                    if hasattr(self, '_last_window') and self._last_window == window_title:
                        focus_time = current_time - self._last_window_time
                        # Add to session data
                    
                    self._last_window = window_title
                    self._last_window_time = current_time
                
                await asyncio.sleep(1)  # Check windows more frequently
                
            except Exception as e:
                self.logger.error(f"Error monitoring windows: {e}")
                await asyncio.sleep(5)
    
    async def _monitor_idle_time(self):
        """Monitor user idle time to detect breaks"""
        while self.is_monitoring:
            try:
                # Simple idle detection based on CPU activity
                # More sophisticated methods could use mouse/keyboard monitoring
                cpu_percent = psutil.cpu_percent(interval=1)
                
                if cpu_percent < 5:  # Very low activity
                    self.last_activity_time = time.time()
                
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
        # This is a simple heuristic - can be made more sophisticated
        productive_apps = {
            'code.exe', 'chrome.exe', 'firefox.exe', 'notepad++.exe',
            'cmd.exe', 'powershell.exe', 'git.exe', 'python.exe'
        }
        
        non_productive_apps = {
            'discord.exe', 'spotify.exe', 'steam.exe', 'games'
        }
        
        total_time = sum(app_data['total_time'] for app_data in self.current_session['applications'].values())
        if total_time == 0:
            return {'productivity_score': 0.0, 'focus_score': 0.0}
        
        productive_time = sum(
            app_data['total_time'] 
            for app_name, app_data in self.current_session['applications'].items()
            if any(prod_app in app_name.lower() for prod_app in productive_apps)
        )
        
        productivity_score = (productive_time / total_time) * 100 if total_time > 0 else 0
        
        # Calculate focus score based on app switching frequency
        app_switches = len(self.current_session['applications'])
        focus_score = max(0, 100 - (app_switches * 5))  # Penalize excessive app switching
        
        return {
            'productivity_score': round(productivity_score, 2),
            'focus_score': round(focus_score, 2),
            'active_time_minutes': round(total_time / 60, 2)
        }
    
    def _extract_app_name(self, window_title: str) -> str:
        """Extract application name from window title"""
        # Simple heuristic to extract app name
        common_separators = [' - ', ' — ', ' | ', ' :: ']
        
        for sep in common_separators:
            if sep in window_title:
                return window_title.split(sep)[-1].strip()
        
        return window_title.split()[0] if window_title else 'Unknown'
    
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
