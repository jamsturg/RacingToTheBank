import logging
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import requests
import json
import time
import pytz
from dataclasses import dataclass
from enum import Enum
import os
from utils.date_utils import format_date
from utils.logger import api_logger, LoggerMixin, log_execution_time

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

class TABApiClient(LoggerMixin):
    """TAB API Client with OAuth authentication"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.tab.com.au"
        self.client_id = os.getenv("TAB_CLIENT_ID")
        self.client_secret = os.getenv("TAB_CLIENT_SECRET")
        
        # Validate credentials at initialization
        if not self.client_id or not self.client_secret:
            logger.error("Missing required API credentials")
            raise ValueError("TAB_CLIENT_ID and TAB_CLIENT_SECRET must be set in environment")
            
        self.bearer_token = None
        self.refresh_token = None
        self.token_expiry = None
        
        # Configure session with retry logic
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "RacingAnalysisPlatform/1.0",
            "X-Requested-With": "XMLHttpRequest"
        })
        
        # Configure WebSocket reconnection
        self.ws_retry_count = 0
        self.ws_max_retries = 3
        self.ws_retry_delay = 1000  # Start with 1 second delay

    def _refresh_token(self) -> bool:
        """Refresh OAuth token using refresh token"""
        if not self.refresh_token:
            logger.warning("No refresh token available")
            return False
            
        url = f"{self.base_url}/oauth/token"
        data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        try:
            response = requests.post(url, data=data, headers=headers, timeout=30)
            logger.info(f"Token refresh response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    token_data = response.json()
                    self.bearer_token = token_data['access_token']
                    self.token_expiry = datetime.now(pytz.UTC) + timedelta(seconds=token_data.get('expires_in', 3600))
                    if new_refresh := token_data.get('refresh_token'):
                        self.refresh_token = new_refresh
                    return True
                except (ValueError, KeyError) as e:
                    logger.error(f"Failed to parse refresh token response: {str(e)}")
                    return False
            else:
                logger.error(f"Token refresh failed with status {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Token refresh request failed: {str(e)}")
            return False

    def get_bearer_token(self) -> Optional[str]:
        """Get valid bearer token, refreshing if necessary"""
        # Check if current token is valid
        if self.bearer_token and self.token_expiry:
            time_until_expiry = self.token_expiry - datetime.now(pytz.UTC)
            
            # Try to refresh token if it expires soon (within 5 minutes)
            if time_until_expiry < timedelta(minutes=5):
                logger.info("Token expiring soon, attempting refresh")
                if self._refresh_token():
                    return self.bearer_token
                    
            # Return current token if still valid
            if time_until_expiry > timedelta(0):
                return self.bearer_token

        # Request new token if no valid token exists
        url = f"{self.base_url}/oauth/token"
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        try:
            response = requests.post(url, data=data, headers=headers, timeout=30)
            logger.info(f"Token request response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    token_data = response.json()
                    self.bearer_token = token_data['access_token']
                    self.token_expiry = datetime.now(pytz.UTC) + timedelta(seconds=token_data.get('expires_in', 3600))
                    if refresh := token_data.get('refresh_token'):
                        self.refresh_token = refresh
                    return self.bearer_token
                except (ValueError, KeyError) as e:
                    logger.error(f"Failed to parse token response: {str(e)}")
                    return None
            else:
                logger.error(f"Token request failed with status {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Token request failed: {str(e)}")
            return None

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict:
        """Make API request with automatic token refresh and improved error handling"""
        url = f"{self.base_url}{endpoint}"
        
        # Get valid token
        bearer_token = self.get_bearer_token()
        if not bearer_token:
            raise APIError("Failed to obtain valid authentication token")
            
        # Prepare request headers
        request_headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        if headers:
            request_headers.update(headers)
            
        # Log request details (excluding sensitive data)
        logger.info(f"Making {method} request to {endpoint}")
        if params:
            logger.debug(f"Request params: {params}")
        
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
                
                # Log response details
                logger.info(f"Response status: {response.status_code}")
                logger.debug(f"Response headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        logger.debug("Response parsed successfully")
                        return response_data
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON response: {str(e)}")
                        raise APIError(f"Invalid response format: {str(e)}")
                elif response.status_code == 401:
                    logger.warning("Token expired, attempting refresh")
                    if attempt < 2 and self._refresh_token():
                        bearer_token = self.bearer_token
                        request_headers["Authorization"] = f"Bearer {bearer_token}"
                        continue
                    raise APIError("Authentication failed")
                elif response.status_code == 403:
                    raise APIError("Insufficient permissions")
                elif response.status_code == 429:
                    if attempt < 2:
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limited, waiting {wait_time}s")
                        time.sleep(wait_time)
                        continue
                    raise APIError("Rate limit exceeded")
                else:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('error_description', f"Request failed with status {response.status_code}")
                        logger.error(f"API error: {error_msg}")
                        raise APIError(error_msg)
                    except (json.JSONDecodeError, KeyError):
                        raise APIError(f"Request failed with status {response.status_code}")
                        
            except requests.exceptions.RequestException as e:
                if attempt == 2:
                    logger.error(f"Request failed after all retries: {str(e)}")
                    raise APIError(f"Request failed: {str(e)}")
                time.sleep(2 ** attempt)
                continue
                
        raise APIError("Request failed after all retries")

    # Account endpoints with improved error handling
    def verify_credentials(self) -> bool:
        """Verify API credentials"""
        try:
            response = self._make_request("GET", "/v1/account/info")
            return bool(response and not response.get('error'))
        except APIError:
            return False

    def get_account_balance(self) -> Dict:
        """Get current account balance with validation"""
        response = self._make_request("GET", "/v1/account/balance")
        if not isinstance(response.get('balance'), (int, float)):
            raise APIError("Invalid balance data in response")
        return response

    def get_account_bets(self, status: Optional[str] = None) -> Dict:
        """Get account bets with validation"""
        params = {"status": status} if status else None
        return self._make_request("GET", "/v1/account/bets", params=params)

    def get_bet_history(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """Get betting history with date validation"""
        params = {}
        if start_date:
            formatted_start = format_date(start_date)
            if not formatted_start:
                raise ValueError("Invalid start date format")
            params["startDate"] = formatted_start
            
        if end_date:
            formatted_end = format_date(end_date)
            if not formatted_end:
                raise ValueError("Invalid end date format")
            params["endDate"] = formatted_end
            
        return self._make_request("GET", "/v1/account/bets/history", params=params)

    def get_pending_bets(self) -> Dict:
        """Get pending bets"""
        return self._make_request("GET", "/v1/account/bets/pending")

    def place_bet(self, bet_data: Dict) -> Dict:
        """Place bet with data validation"""
        required_fields = ['raceId', 'selectionId', 'betType', 'stake']
        if not all(field in bet_data for field in required_fields):
            raise ValueError("Missing required bet data fields")
            
        return self._make_request("POST", "/v1/account/bets", data=bet_data)

    def cancel_bet(self, bet_id: str) -> Dict:
        """Cancel bet with ID validation"""
        if not bet_id or not isinstance(bet_id, str):
            raise ValueError("Invalid bet ID")
            
        return self._make_request("DELETE", f"/v1/account/bets/{bet_id}")
