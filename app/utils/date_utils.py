"""Date and time utilities for OfficeRND booking system"""
from datetime import datetime, timezone
import pytz
from typing import Optional
import re
import logging

logger = logging.getLogger(__name__)


def parse_user_datetime(date_str: str, time_str: str, timezone_str: str = "America/New_York") -> Optional[datetime]:
    """Parse user-provided date and time into datetime object
    
    Args:
        date_str: Date string like "Dec 25, 2025" or "25 Dec 2025"
        time_str: Time string like "2pm" or "14:00"
        timezone_str: Timezone string (default: America/New_York)
    
    Returns:
        datetime object with timezone or None if parsing fails
    """
    try:
        # Clean up date string
        date_str = date_str.strip()
        
        # Try different date formats
        date_formats = [
            "%d %b %Y",      # "25 Dec 2025"
            "%b %d, %Y",     # "Dec 25, 2025"
            "%b %d %Y",      # "Dec 25 2025"
            "%d %B %Y",      # "25 December 2025"
            "%B %d, %Y",     # "December 25, 2025"
            "%B %d %Y",      # "December 25 2025"
            "%Y-%m-%d",      # "2025-12-25"
            "%m/%d/%Y",      # "12/25/2025"
            "%d/%m/%Y"       # "25/12/2025"
        ]
        
        date_obj = None
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        
        if not date_obj:
            logger.error(f"Could not parse date: {date_str}")
            return None
        
        # Parse time
        time_str = time_str.strip().lower()
        
        # Remove 'to' if it's there (from "1pm to 2pm")
        time_str = time_str.split(' to ')[0].split(' - ')[0]
        
        # Handle formats like "2pm", "2:30pm", "14:00"
        time_obj = None
        
        # Try parsing with AM/PM
        if 'am' in time_str or 'pm' in time_str:
            # Remove spaces between number and am/pm
            time_str = re.sub(r'(\d+)\s*(am|pm)', r'\1\2', time_str)
            
            time_formats = [
                "%I%p",        # "2pm"
                "%I:%M%p",     # "2:30pm"
            ]
            
            for fmt in time_formats:
                try:
                    time_obj = datetime.strptime(time_str, fmt).time()
                    break
                except ValueError:
                    continue
        else:
            # Try 24-hour format
            try:
                time_obj = datetime.strptime(time_str, "%H:%M").time()
            except ValueError:
                # Try just hour
                try:
                    hour = int(time_str)
                    time_obj = datetime.strptime(f"{hour:02d}:00", "%H:%M").time()
                except ValueError:
                    pass
        
        if not time_obj:
            logger.error(f"Could not parse time: {time_str}")
            return None
        
        # Combine date and time
        dt = datetime.combine(date_obj.date(), time_obj)
        
        # Add timezone
        tz = pytz.timezone(timezone_str)
        dt_with_tz = tz.localize(dt)
        
        return dt_with_tz
        
    except Exception as e:
        logger.error(f"Error parsing datetime: {str(e)}")
        return None


def datetime_to_officernd_format(dt: datetime) -> str:
    """Convert datetime to OfficeRND ISO format with Z suffix
    
    Args:
        dt: datetime object (should have timezone info)
        
    Returns:
        ISO formatted string like "2025-10-31T13:00:00.000Z"
    """
    # Convert to UTC
    dt_utc = dt.astimezone(timezone.utc)
    
    # Format as ISO with milliseconds and Z suffix
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def format_datetime_for_display(dt: datetime, timezone_str: str = "America/New_York") -> str:
    """Format datetime for user display
    
    Args:
        dt: datetime object
        timezone_str: Target timezone for display
        
    Returns:
        Formatted string like "Dec 25, 2025 at 2:00 PM EST"
    """
    # Convert to target timezone
    tz = pytz.timezone(timezone_str)
    dt_local = dt.astimezone(tz)
    
    # Format nicely
    return dt_local.strftime("%b %d, %Y at %-I:%M %p %Z")