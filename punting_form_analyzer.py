import requests
import logging
from datetime import datetime, date
import pytz
from typing import Dict, List, Optional
import os
import json
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIError(Exception):
    """Custom exception for API errors"""
    pass

class PuntingFormAPI:
    """Client for Punting Form API"""
    
    def __init__(self, api_key: str):
        self.base_url = "https://api.puntingform.com/v1"
        self.api_key = api_key
        self.session = requests.Session()
        
        # Configure retries with backoff
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        
        # Configure adapter with retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        # Set headers
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "RacingAnalysisPlatform/1.0"
        })

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make API request with improved error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.info(f"Making {method} request to {endpoint}")
            
            # Set default timeout
            kwargs['timeout'] = kwargs.get('timeout', 30)
            
            response = self.session.request(method, url, **kwargs)
            
            # Log response details for debugging
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON response: {str(e)}")
                    return {"error": "Invalid response format"}
            elif response.status_code == 401:
                logger.error("Authentication failed")
                return {"error": "Invalid API key"}
            elif response.status_code == 403:
                logger.error("Access forbidden")
                return {"error": "Access denied"}
            elif response.status_code == 429:
                logger.warning("Rate limit exceeded")
                return {"error": "Rate limit exceeded"}
            else:
                logger.error(f"Request failed with status {response.status_code}")
                return {"error": f"Request failed: {response.status_code}"}
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {str(e)}")
            return {"error": "Connection failed"}
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout: {str(e)}")
            return {"error": "Request timed out"}
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}"}

    def format_date(self, date_obj: Optional[datetime | date | str]) -> Optional[str]:
        """Format date with proper timezone handling"""
        if not date_obj:
            return None
            
        try:
            tz = pytz.timezone('Australia/Sydney')
            
            if isinstance(date_obj, datetime):
                return date_obj.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(date_obj, str):
                try:
                    dt = datetime.strptime(date_obj, "%Y-%m-%d")
                    return dt.replace(tzinfo=tz).strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        dt = datetime.strptime(date_obj, "%Y-%m-%dT%H:%M:%S%z")
                        return dt.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        logger.error(f"Invalid date format: {date_obj}")
                        return None
            elif isinstance(date_obj, date):
                dt = datetime.combine(date_obj, datetime.min.time())
                return dt.replace(tzinfo=tz).strftime("%Y-%m-%d %H:%M:%S")
                
            return None
        except Exception as e:
            logger.error(f"Date formatting error: {str(e)}")
            return None

    def get_next_races(self, jurisdiction: str, limit: Optional[int] = None) -> Dict:
        """Get upcoming races"""
        params = {"jurisdiction": jurisdiction}
        if limit is not None:
            params["limit"] = str(limit)
            
        logger.info(f"Fetching next races for {jurisdiction}")
        return self._make_request(
            "GET",
            "/races/next",
            params=params
        )
