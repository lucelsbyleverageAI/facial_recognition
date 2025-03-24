import datetime
from typing import Optional, Union
import re

def parse_datetime(dt_str: str) -> Optional[datetime.datetime]:
    """
    Parse a datetime string into a datetime object.
    Handles multiple formats including ISO, custom, and unix timestamps.
    
    Args:
        dt_str: The datetime string to parse
        
    Returns:
        Parsed datetime object or None if parsing fails
    """
    if not dt_str:
        return None
        
    # Try common formats
    formats = [
        '%Y-%m-%dT%H:%M:%S.%fZ',  # ISO 8601 with microseconds and Z
        '%Y-%m-%dT%H:%M:%SZ',      # ISO 8601 without microseconds
        '%Y-%m-%dT%H:%M:%S.%f',    # ISO 8601 with microseconds
        '%Y-%m-%dT%H:%M:%S',       # ISO 8601 without microseconds
        '%Y-%m-%d %H:%M:%S.%f',    # PostgreSQL timestamp with microseconds
        '%Y-%m-%d %H:%M:%S',       # PostgreSQL timestamp without microseconds
        '%Y-%m-%d',                # Date only
    ]
    
    for fmt in formats:
        try:
            return datetime.datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    
    # Try to parse unix timestamp (seconds since epoch)
    try:
        # Check if it's a numeric string
        if re.match(r'^\d+(\.\d+)?$', dt_str):
            timestamp = float(dt_str)
            return datetime.datetime.fromtimestamp(timestamp)
    except (ValueError, OverflowError):
        pass
    
    # Log error if we can't parse the datetime
    return None

def format_datetime(dt: Union[datetime.datetime, str], format_str: str = '%Y-%m-%dT%H:%M:%S.%fZ') -> Optional[str]:
    """
    Format a datetime object or string into a specified format.
    
    Args:
        dt: Datetime object or string to format
        format_str: Format string to use
        
    Returns:
        Formatted datetime string or None if formatting fails
    """
    if not dt:
        return None
        
    # If dt is a string, parse it first
    if isinstance(dt, str):
        dt = parse_datetime(dt)
        if not dt:
            return None
    
    return dt.strftime(format_str)

def format_for_database(dt: Union[datetime.datetime, str]) -> Optional[str]:
    """
    Format a datetime for database storage.
    
    Args:
        dt: Datetime object or string to format
        
    Returns:
        ISO 8601 formatted string for database storage
    """
    return format_datetime(dt, '%Y-%m-%dT%H:%M:%S.%fZ')

def format_for_display(dt: Union[datetime.datetime, str]) -> Optional[str]:
    """
    Format a datetime for user display.
    
    Args:
        dt: Datetime object or string to format
        
    Returns:
        Human-readable datetime string
    """
    return format_datetime(dt, '%b %d, %Y %I:%M %p')

def parse_timecode(timecode: str) -> Optional[float]:
    """
    Parse a timecode string (HH:MM:SS:FF or HH:MM:SS.ms) into seconds.
    
    Args:
        timecode: Timecode string in HH:MM:SS:FF or HH:MM:SS.ms format
        
    Returns:
        Seconds as float or None if parsing fails
    """
    if not timecode:
        return None
    
    # Try HH:MM:SS:FF format (frames)
    match = re.match(r'^(\d+):(\d+):(\d+):(\d+)$', timecode)
    if match:
        hours, minutes, seconds, frames = map(int, match.groups())
        # Assume 24 frames per second, can adjust as needed
        return hours * 3600 + minutes * 60 + seconds + frames / 24.0
    
    # Try HH:MM:SS.ms format (milliseconds)
    match = re.match(r'^(\d+):(\d+):(\d+)\.(\d+)$', timecode)
    if match:
        hours, minutes, seconds, ms = match.groups()
        ms_value = int(ms) / (10 ** len(ms))
        return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + ms_value
    
    # Try MM:SS format
    match = re.match(r'^(\d+):(\d+)$', timecode)
    if match:
        minutes, seconds = map(int, match.groups())
        return minutes * 60 + seconds
    
    return None

def format_timecode(seconds: float, include_frames: bool = True) -> str:
    """
    Format seconds into a timecode string.
    
    Args:
        seconds: Time in seconds
        include_frames: Whether to include frames in the output
        
    Returns:
        Timecode string in HH:MM:SS:FF or HH:MM:SS format
    """
    if seconds is None:
        return "00:00:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds_part = int(seconds % 60)
    
    if include_frames:
        frames = int((seconds - int(seconds)) * 24)  # Assuming 24 fps
        return f"{hours:02d}:{minutes:02d}:{seconds_part:02d}:{frames:02d}"
    else:
        return f"{hours:02d}:{minutes:02d}:{seconds_part:02d}" 