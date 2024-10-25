import pytz
from datetime import datetime, date
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def format_date(date_obj: Optional[datetime | date | str], include_time: bool = False) -> Optional[str]:
    """Format date with proper timezone handling"""
    if not date_obj:
        return None
        
    try:
        tz = pytz.timezone('Australia/Sydney')
        
        if isinstance(date_obj, datetime):
            return date_obj.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S" if include_time else "%Y-%m-%d")
        elif isinstance(date_obj, str):
            try:
                if 'T' in date_obj:  # ISO format
                    dt = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
                    dt = dt.astimezone(tz)
                else:
                    dt = datetime.strptime(date_obj, "%Y-%m-%d")
                return dt.strftime("%Y-%m-%d %H:%M:%S" if include_time else "%Y-%m-%d")
            except ValueError as e:
                logger.error(f"Invalid date format: {date_obj}, error: {str(e)}")
                return None
        elif isinstance(date_obj, date):
            dt = datetime.combine(date_obj, datetime.min.time())
            dt = dt.replace(tzinfo=tz)
            return dt.strftime("%Y-%m-%d")
            
        return None
    except Exception as e:
        logger.error(f"Date formatting error: {str(e)}")
        return None

def format_countdown(start_time: Optional[str]) -> str:
    """Format countdown timer with proper timezone handling"""
    if not start_time:
        return "N/A"
        
    try:
        tz = pytz.timezone('Australia/Sydney')
        if ' ' in start_time:  # Has time component
            race_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        else:
            race_time = datetime.strptime(start_time, "%Y-%m-%d")
        race_time = race_time.replace(tzinfo=tz)
        now = datetime.now(tz)
        delta = race_time - now
        
        if delta.total_seconds() < 0:
            return "Started"
        
        minutes = delta.seconds // 60
        if minutes < 60:
            return f"{minutes}m"
        else:
            hours = minutes // 60
            return f"{hours}h {minutes % 60}m"
    except Exception as e:
        logger.error(f"Error formatting countdown: {str(e)}")
        return "N/A"
