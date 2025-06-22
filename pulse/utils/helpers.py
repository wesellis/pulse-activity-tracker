"""
Helper utilities for Pulse Activity Tracker
Common functions, logging setup, and utility classes
"""

import os
import sys
import logging
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import json

def setup_logging(config=None) -> logging.Logger:
    """Setup structured logging for the application"""
    
    # Get log level and file from config if provided
    if config:
        log_level = getattr(config, 'log_level', 'INFO')
        log_file = config.get_log_path()
    else:
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        log_file = os.getenv('LOG_FILE', 'pulse.log')
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Setup root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create application logger
    logger = logging.getLogger('pulse')
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}")
    
    return logger

def sanitize_window_title(title: str, privacy_level: str = 'medium') -> str:
    """
    Sanitize window titles based on privacy settings
    
    Args:
        title: Raw window title
        privacy_level: 'high', 'medium', 'low' privacy protection
    
    Returns:
        Sanitized title string
    """
    if not title:
        return 'Unknown'
    
    if privacy_level == 'high':
        # Only keep application name, remove all content
        return extract_app_name_from_title(title)
    
    elif privacy_level == 'medium':
        # Remove sensitive patterns but keep general context
        sensitive_patterns = [
            r'\b\d{4}[-/]\d{2}[-/]\d{2}\b',  # Dates
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # IP addresses
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN-like patterns
            r'\bpassword\b|\btoken\b|\bapi.?key\b',  # Security terms
        ]
        
        sanitized = title
        for pattern in sensitive_patterns:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    else:  # low privacy
        # Minimal sanitization - just remove obvious sensitive data
        sensitive_words = ['password', 'token', 'api key', 'secret']
        sanitized = title
        
        for word in sensitive_words:
            sanitized = re.sub(rf'\b{word}\b', '[REDACTED]', sanitized, flags=re.IGNORECASE)
        
        return sanitized

def extract_app_name_from_title(title: str) -> str:
    """Extract application name from window title using common patterns"""
    if not title:
        return 'Unknown'
    
    # Common separators used by applications
    separators = [' - ', ' — ', ' | ', ' :: ', ' - ', ' – ']
    
    # Try to extract app name from the end (common pattern)
    for sep in separators:
        if sep in title:
            parts = title.split(sep)
            # Usually app name is at the end
            app_name = parts[-1].strip()
            if app_name and len(app_name) < 50:  # Reasonable app name length
                return app_name
    
    # If no separator found, try to extract first word or first few words
    words = title.split()
    if words:
        # Check if first word looks like an app name
        first_word = words[0]
        if len(first_word) > 2 and len(first_word) < 30:
            return first_word
    
    # Fallback to truncated title
    return title[:30] + '...' if len(title) > 30 else title

def calculate_app_productivity_score(app_name: str, config=None) -> float:
    """
    Calculate productivity score for an application
    
    Args:
        app_name: Name of the application
        config: Configuration object with custom productivity rules
    
    Returns:
        Productivity score (0.0 to 1.0)
    """
    app_lower = app_name.lower()
    
    # Default productivity categories
    highly_productive = {
        'code.exe', 'visual studio', 'pycharm', 'intellij', 'eclipse',
        'notepad++', 'sublime', 'atom', 'brackets', 'vim', 'emacs',
        'git.exe', 'powershell', 'cmd.exe', 'terminal', 'iterm',
        'photoshop', 'illustrator', 'sketch', 'figma', 'blender',
        'word', 'excel', 'powerpoint', 'google docs', 'notion',
        'slack', 'teams', 'zoom', 'webex'  # Communication tools
    }
    
    moderately_productive = {
        'chrome.exe', 'firefox.exe', 'safari', 'edge',  # Browsers
        'calculator', 'calendar', 'mail', 'outlook',
        'file explorer', 'finder', 'explorer.exe',
        'settings', 'system preferences', 'control panel'
    }
    
    low_productivity = {
        'spotify.exe', 'itunes', 'music', 'vlc', 'media player',
        'discord.exe', 'whatsapp', 'telegram', 'signal',
        'instagram', 'tiktok', 'snapchat'
    }
    
    unproductive = {
        'steam.exe', 'epic games', 'origin', 'battle.net',
        'netflix', 'youtube', 'twitch', 'hulu', 'disney+',
        'facebook', 'twitter', 'reddit', 'imgur'
    }
    
    # Check categories
    for app in highly_productive:
        if app in app_lower:
            return 1.0
    
    for app in moderately_productive:
        if app in app_lower:
            return 0.7
    
    for app in low_productivity:
        if app in app_lower:
            return 0.3
    
    for app in unproductive:
        if app in app_lower:
            return 0.0
    
    # Default for unknown applications (slightly productive)
    return 0.5

def hash_sensitive_data(data: str, salt: str = None) -> str:
    """
    Hash sensitive data for privacy protection
    
    Args:
        data: Data to hash
        salt: Optional salt for hashing
    
    Returns:
        Hashed string
    """
    if not data:
        return ''
    
    if salt is None:
        salt = 'pulse_default_salt_2025'
    
    # Create hash
    hash_input = f"{data}{salt}".encode('utf-8')
    return hashlib.sha256(hash_input).hexdigest()[:16]  # First 16 chars for readability

def format_time_duration(seconds: float) -> str:
    """Format seconds into human-readable duration"""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.0f}m"
    else:
        hours = seconds / 3600
        minutes = (seconds % 3600) / 60
        return f"{hours:.0f}h {minutes:.0f}m"

def is_work_related_file(file_path: str, work_directories: List[str] = None) -> bool