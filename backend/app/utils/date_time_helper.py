"""
Date and Time Helper Utilities for Philippine Standard Time (PST/UTC+8)

This module provides centralized functions for converting UTC datetime objects
to Philippine Standard Time and formatting them for display.
"""
from datetime import datetime, timezone, timedelta
from typing import Union, Optional


# Philippine Timezone (UTC+8)
PH_TZ = timezone(timedelta(hours=8))


def to_philippine_time(dt: Union[datetime, str, None]) -> Optional[datetime]:
    """
    Convert a datetime (UTC or naive) to Philippine Standard Time (UTC+8).
    
    Args:
        dt: datetime object (UTC or naive), ISO string, or None
        
    Returns:
        datetime object in Philippine timezone, or None if input is None/invalid
    """
    if dt is None:
        return None
    
    # Handle string input
    if isinstance(dt, str):
        try:
            # Try parsing ISO format
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Try parsing common formats
                dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return None
    
    # Handle naive datetime (assume UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Convert to Philippine time
    return dt.astimezone(PH_TZ)


def format_datetime_ph(dt: Union[datetime, str, None], format_str: str = '%b %d, %Y %I:%M %p %Z') -> str:
    """
    Format a datetime to Philippine Standard Time string.
    
    Args:
        dt: datetime object (UTC or naive), ISO string, or None
        format_str: strftime format string (default: '%b %d, %Y %I:%M %p %Z')
        
    Returns:
        Formatted string in Philippine time, or 'N/A' if input is None/invalid
    """
    if dt is None:
        return 'N/A'
    
    ph_dt = to_philippine_time(dt)
    if ph_dt is None:
        return 'N/A'
    
    # Replace %Z with 'PST' or 'PHST' for clarity
    formatted = ph_dt.strftime(format_str)
    if '%Z' in format_str:
        formatted = formatted.replace('+08:00', 'PST').replace('UTC+08:00', 'PST')
    
    return formatted


def format_datetime_ph_iso(dt: Union[datetime, str, None]) -> Optional[str]:
    """
    Convert datetime to Philippine Standard Time ISO format string.
    
    Args:
        dt: datetime object (UTC or naive), ISO string, or None
        
    Returns:
        ISO format string in Philippine timezone, or None if input is None/invalid
    """
    ph_dt = to_philippine_time(dt)
    if ph_dt is None:
        return None
    
    return ph_dt.isoformat()


def format_date_ph(dt: Union[datetime, str, None], format_str: str = '%b %d, %Y') -> str:
    """
    Format a datetime to Philippine Standard Time date string (no time).
    
    Args:
        dt: datetime object (UTC or naive), ISO string, or None
        format_str: strftime format string (default: '%b %d, %Y')
        
    Returns:
        Formatted date string in Philippine time, or 'N/A' if input is None/invalid
    """
    if dt is None:
        return 'N/A'
    
    ph_dt = to_philippine_time(dt)
    if ph_dt is None:
        return 'N/A'
    
    return ph_dt.strftime(format_str)


def format_time_ph(dt: Union[datetime, str, None], format_str: str = '%I:%M %p') -> str:
    """
    Format a datetime to Philippine Standard Time time string (no date).
    
    Args:
        dt: datetime object (UTC or naive), ISO string, or None
        format_str: strftime format string (default: '%I:%M %p')
        
    Returns:
        Formatted time string in Philippine time, or 'N/A' if input is None/invalid
    """
    if dt is None:
        return 'N/A'
    
    ph_dt = to_philippine_time(dt)
    if ph_dt is None:
        return 'N/A'
    
    return ph_dt.strftime(format_str)


def get_philippine_now() -> datetime:
    """
    Get current datetime in Philippine Standard Time.
    
    Returns:
        Current datetime in Philippine timezone
    """
    return datetime.now(PH_TZ)


def get_utc_now() -> datetime:
    """
    Get current datetime in UTC (for database storage).
    
    Returns:
        Current datetime in UTC timezone
    """
    return datetime.now(timezone.utc)

