import requests
import logging
from datetime import datetime
import pytz
from typing import Dict, List, Optional
import os
import urllib3
import certifi
import json
import time
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
        
        # Configure SSL verification
        self.session.verify = True
        
        # Configure retries with backoff
        retry_strategy = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=['GET', 'POST']
        )
        
        # Configure adapter with retry strategy and SSL settings
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10
        )
        
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        # Set request headers
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "RacingAnalysisPlatform/1.0"
        })
        
        # Add proxy if configured
        proxy_url = os.getenv("PROXY_URL")
        if proxy_url:
            self.session.proxies = {
                "http": proxy_url,
                "https": proxy_url
            }

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make API request with improved error handling"""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(3):
            try:
                logger.info(f"Making {method} request to {endpoint}")
                
                # Set default timeout if not provided
                if 'timeout' not in kwargs:
                    kwargs['timeout'] = 30
                
                response = self.session.request(method, url, **kwargs)
                
                # Log response status and headers for debugging
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response headers: {dict(response.headers)}")
                
                try:
                    response_data = response.json() if response.content else {}
                except json.JSONDecodeError as e:
                    if attempt < 2:
                        time.sleep(1)
                        continue
                    logger.error(f"Failed to parse JSON response: {str(e)}")
                    return {"error": "Invalid JSON response", "details": str(e)}
                
                if response.status_code == 200:
                    return response_data
                elif response.status_code == 401:
                    return {"error": "Invalid API key or unauthorized access"}
                elif response.status_code == 429:
                    if attempt < 2:
                        time.sleep(2)
                        continue
                    return {"error": "Rate limit exceeded. Please try again later"}
                else:
                    if attempt < 2:
                        time.sleep(1)
                        continue
                    response.raise_for_status()
                    
            except requests.exceptions.SSLError as e:
                if attempt < 2:
                    time.sleep(1)
                    continue
                logger.error(f"SSL Error: {str(e)}")
                return {"error": "SSL verification failed", "details": str(e)}
            except requests.exceptions.ConnectionError as e:
                if attempt < 2:
                    time.sleep(1)
                    continue
                logger.error(f"Connection Error: {str(e)}")
                return {"error": "Connection failed", "details": str(e)}
            except requests.exceptions.Timeout as e:
                if attempt < 2:
                    time.sleep(1)
                    continue
                logger.error(f"Timeout Error: {str(e)}")
                return {"error": "Request timed out", "details": str(e)}
            except Exception as e:
                if attempt < 2:
                    time.sleep(1)
                    continue
                logger.error(f"Request failed: {str(e)}")
                return {"error": "Request failed", "details": str(e)}
        
        return {"error": "Request failed after all retries"}

    def format_date(self, date_obj) -> Optional[str]:
        """Format date for API requests with timezone handling"""
        try:
            tz = pytz.timezone('Australia/Sydney')
            if isinstance(date_obj, datetime):
                return date_obj.astimezone(tz).strftime("%Y-%m-%d")
            elif isinstance(date_obj, str):
                dt = datetime.strptime(date_obj, "%Y-%m-%d")
                return dt.astimezone(tz).strftime("%Y-%m-%d")
            return date_obj.astimezone(tz).strftime("%Y-%m-%d")
        except Exception as e:
            logger.error(f"Date formatting error: {str(e)}")
            return None

    def get_meetings(self, meeting_date: str, jurisdiction: str) -> Dict:
        """Get race meetings for a specific date"""
        formatted_date = self.format_date(meeting_date)
        if not formatted_date:
            return {"error": "Invalid date format"}
            
        logger.info(f"Fetching meetings for {formatted_date} in {jurisdiction}")
        return self._make_request(
            "GET",
            "/meetings",
            params={
                "date": formatted_date,
                "jurisdiction": jurisdiction
            }
        )

    def get_races_in_meeting(self, meeting_date: str, meeting_id: str, jurisdiction: str) -> Dict:
        """Get all races in a meeting"""
        formatted_date = self.format_date(meeting_date)
        if not formatted_date:
            return {"error": "Invalid date format"}
            
        logger.info(f"Fetching races for meeting {meeting_id}")
        return self._make_request(
            "GET",
            f"/meetings/{meeting_id}/races",
            params={
                "date": formatted_date,
                "jurisdiction": jurisdiction
            }
        )

    def get_race_fields(self, race_id: str, include_form: bool = True) -> Dict:
        """Get race fields and form data"""
        logger.info(f"Fetching fields for race {race_id}")
        return self._make_request(
            "GET",
            f"/races/{race_id}/fields",
            params={"include_form": str(include_form).lower()}
        )

    def get_runner_form(self, runner_id: str, detailed: bool = True) -> Dict:
        """Get detailed form for a specific runner"""
        logger.info(f"Fetching form for runner {runner_id}")
        return self._make_request(
            "GET",
            f"/runners/{runner_id}/form",
            params={"detailed": str(detailed).lower()}
        )

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
