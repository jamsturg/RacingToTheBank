from typing import Dict, List, Optional, Union
from datetime import datetime
import requests
import logging
import json
import time
from dataclasses import dataclass
from enum import Enum
import os
from utils.date_utils import format_date

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RaceType(Enum):
    THOROUGHBRED = "R"
    HARNESS = "H"
    GREYHOUND = "G"

class APIError(Exception):
    """Custom exception for API errors"""
    pass

class TABApiClient:
    """TAB API Client implementing all available endpoints"""
    
    def __init__(self, bearer_token: Optional[str] = None):
        self.base_url = "https://api.tab.com.au/v1"
        self.bearer_token = bearer_token or os.getenv("TAB_BEARER_TOKEN")
        if not self.bearer_token:
            raise ValueError("Bearer token must be provided or set in TAB_BEARER_TOKEN environment variable")
            
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.bearer_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        })

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict:
        """Make API request with error handling and retries"""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(3):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    try:
                        return response.json()
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON response: {str(e)}")
                        raise APIError(f"Invalid response format: {str(e)}")
                elif response.status_code == 401:
                    raise APIError("Authentication failed. Check your bearer token.")
                elif response.status_code == 403:
                    raise APIError("Insufficient permissions for this request.")
                elif response.status_code == 429:
                    if attempt < 2:
                        time.sleep(2)
                        continue
                    raise APIError("Rate limit exceeded. Please wait before retrying.")
                else:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('error', f"Request failed with status {response.status_code}")
                    except:
                        error_msg = f"Request failed with status {response.status_code}"
                    raise APIError(error_msg)
                    
            except requests.exceptions.RequestException as e:
                if attempt == 2:
                    raise APIError(f"Request failed: {str(e)}")
                time.sleep(2)
                continue
                
        raise APIError("Request failed after all retries")

    # Racing endpoints
    def get_meetings(self, date: str) -> Dict:
        """Get race meetings for a specific date"""
        formatted_date = format_date(date)
        if not formatted_date:
            raise ValueError("Invalid date format")
        return self._make_request("GET", f"/racing/meetings", params={"date": formatted_date})

    def get_races(self, meeting_id: str) -> Dict:
        """Get races for a specific meeting"""
        return self._make_request("GET", f"/racing/races", params={"meetingId": meeting_id})

    def get_form(self, race_id: str) -> Dict:
        """Get form guide for a specific race"""
        return self._make_request("GET", f"/racing/form", params={"raceId": race_id})

    def get_odds(self, race_id: str) -> Dict:
        """Get current odds for a specific race"""
        return self._make_request("GET", f"/racing/odds", params={"raceId": race_id})

    def get_results(self, race_id: str) -> Dict:
        """Get results for a specific race"""
        return self._make_request("GET", f"/racing/results", params={"raceId": race_id})

    # Account endpoints
    def get_account_balance(self) -> Dict:
        """Get current account balance"""
        return self._make_request("GET", "/account/balance")

    def get_account_bets(self, status: Optional[str] = None) -> Dict:
        """Get account bets with optional status filter"""
        params = {"status": status} if status else None
        return self._make_request("GET", "/account/bets", params=params)

    def get_bet_history(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """Get betting history within date range"""
        params = {}
        if start_date:
            params["startDate"] = format_date(start_date)
        if end_date:
            params["endDate"] = format_date(end_date)
        return self._make_request("GET", "/account/bets/history", params=params)

    def get_pending_bets(self) -> Dict:
        """Get pending bets"""
        return self._make_request("GET", "/account/bets/pending")

    def place_bet(self, bet_data: Dict) -> Dict:
        """Place a new bet"""
        return self._make_request("POST", "/account/bets", data=bet_data)

    def cancel_bet(self, bet_id: str) -> Dict:
        """Cancel a pending bet"""
        return self._make_request("DELETE", f"/account/bets/{bet_id}")
