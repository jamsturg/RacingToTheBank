from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import requests
import logging
import json
import time
import pytz
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
    """TAB API Client with OAuth authentication"""
    
    def __init__(self):
        self.base_url = "https://api.beta.tab.com.au"
        self.client_id = os.getenv("TAB_CLIENT_ID")
        self.client_secret = os.getenv("TAB_CLIENT_SECRET")
        if not self.client_id or not self.client_secret:
            raise ValueError("TAB_CLIENT_ID and TAB_CLIENT_SECRET must be set in environment")
            
        self.bearer_token = None
        self.token_expiry = None
        self.session = requests.Session()

    def get_bearer_token(self) -> str:
        """Get valid bearer token, refreshing if necessary"""
        if self.bearer_token and self.token_expiry and datetime.now(pytz.UTC) < self.token_expiry:
            return self.bearer_token

        url = f"{self.base_url}/oauth/token"
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()
            token_data = response.json()
            self.bearer_token = token_data['access_token']
            self.token_expiry = datetime.now(pytz.UTC) + timedelta(seconds=token_data['expires_in'])
            return self.bearer_token
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to retrieve access token: {str(e)}")
            raise APIError(f"Authentication failed: {str(e)}")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict:
        """Make API request with automatic token refresh"""
        url = f"{self.base_url}{endpoint}"
        
        # Ensure we have a valid token
        bearer_token = self.get_bearer_token()
        
        # Update headers with bearer token
        request_headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        if headers:
            request_headers.update(headers)
        
        for attempt in range(3):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=request_headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    try:
                        return response.json()
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON response: {str(e)}")
                        raise APIError(f"Invalid response format: {str(e)}")
                elif response.status_code == 401:
                    # Token might be expired, try to refresh and retry
                    if attempt < 2:
                        logger.info("Token expired, refreshing...")
                        self.bearer_token = None  # Force token refresh
                        bearer_token = self.get_bearer_token()
                        request_headers["Authorization"] = f"Bearer {bearer_token}"
                        continue
                    raise APIError("Authentication failed. Invalid credentials.")
                elif response.status_code == 403:
                    raise APIError("Insufficient permissions for this request.")
                elif response.status_code == 429:
                    if attempt < 2:
                        time.sleep(2 ** attempt)  # Exponential backoff
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
                time.sleep(2 ** attempt)
                continue
                
        raise APIError("Request failed after all retries")

    # Account endpoints
    def verify_credentials(self) -> bool:
        """Verify API credentials by attempting to get account info"""
        try:
            response = self._make_request("GET", "/v1/account/info")
            return bool(response and not response.get('error'))
        except APIError:
            return False

    def get_account_balance(self) -> Dict:
        """Get current account balance"""
        return self._make_request("GET", "/v1/account/balance")

    def get_account_bets(self, status: Optional[str] = None) -> Dict:
        """Get account bets with optional status filter"""
        params = {"status": status} if status else None
        return self._make_request("GET", "/v1/account/bets", params=params)

    def get_bet_history(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """Get betting history within date range"""
        params = {}
        if start_date:
            params["startDate"] = format_date(start_date)
        if end_date:
            params["endDate"] = format_date(end_date)
        return self._make_request("GET", "/v1/account/bets/history", params=params)

    def get_pending_bets(self) -> Dict:
        """Get pending bets"""
        return self._make_request("GET", "/v1/account/bets/pending")

    def place_bet(self, bet_data: Dict) -> Dict:
        """Place a new bet"""
        return self._make_request("POST", "/v1/account/bets", data=bet_data)

    def cancel_bet(self, bet_id: str) -> Dict:
        """Cancel a pending bet"""
        return self._make_request("DELETE", f"/v1/account/bets/{bet_id}")
