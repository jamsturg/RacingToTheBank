import requests
import logging
from datetime import datetime
import pytz
from typing import Dict, List, Optional
import os

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
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        })

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        max_retries: int = 3
    ) -> Dict:
        """Make API request with error handling and retries"""
        url = f"{self.base_url}{endpoint}"
        attempt = 0
        
        while attempt < max_retries:
            try:
                logger.debug(f"Request attempt {attempt + 1}: {method} {url}")
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.json() if response.content else {}
                elif response.status_code == 401:
                    raise APIError("Invalid API key")
                elif response.status_code == 429:
                    if attempt < max_retries - 1:
                        attempt += 1
                        continue
                    raise APIError("Rate limit exceeded")
                else:
                    response.raise_for_status()
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise APIError(f"Request failed after {max_retries} retries: {str(e)}")
                attempt += 1
                continue
                
            attempt += 1
            
        return {}  # Return empty dict if all retries failed

    def format_date(self, date_str: str) -> str:
        """Format date to API expected format"""
        try:
            if isinstance(date_str, datetime):
                date = date_str
            else:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            return date.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            raise ValueError("Invalid date format. Use YYYY-MM-DD or datetime object")

    def get_meetings(self, meeting_date: str, jurisdiction: str) -> Dict:
        """Get race meetings for a specific date"""
        try:
            formatted_date = self.format_date(meeting_date)
            return self._make_request(
                "GET",
                "/meetings",
                params={
                    "date": formatted_date,
                    "jurisdiction": jurisdiction
                }
            )
        except ValueError as e:
            logger.error(f"Date formatting error: {str(e)}")
            return {"error": str(e)}

    def get_races_in_meeting(
        self,
        meeting_date: str,
        meeting_id: str,
        jurisdiction: str
    ) -> Dict:
        """Get all races in a meeting"""
        try:
            formatted_date = self.format_date(meeting_date)
            return self._make_request(
                "GET",
                f"/meetings/{meeting_id}/races",
                params={
                    "date": formatted_date,
                    "jurisdiction": jurisdiction
                }
            )
        except ValueError as e:
            logger.error(f"Date formatting error: {str(e)}")
            return {"error": str(e)}

    def get_race_fields(
        self,
        race_id: str,
        include_form: bool = True
    ) -> Dict:
        """Get race fields and form data"""
        return self._make_request(
            "GET",
            f"/races/{race_id}/fields",
            params={"include_form": str(include_form).lower()}
        )

    def get_runner_form(
        self,
        runner_id: str,
        detailed: bool = True
    ) -> Dict:
        """Get detailed form for a specific runner"""
        return self._make_request(
            "GET",
            f"/runners/{runner_id}/form",
            params={"detailed": str(detailed).lower()}
        )

    def get_next_races(
        self,
        jurisdiction: str,
        limit: Optional[int] = None
    ) -> Dict:
        """Get upcoming races"""
        params = {
            "jurisdiction": jurisdiction
        }
        if limit is not None:
            params["limit"] = str(limit)
            
        return self._make_request(
            "GET",
            "/races/next",
            params=params
        )
