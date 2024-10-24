from typing import Dict, List, Optional, Union
from datetime import datetime
import requests
import logging
import json
import time
from dataclasses import dataclass
from enum import Enum
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
        self.base_url = "https://api.beta.tab.com.au"
        self.bearer_token = bearer_token or os.getenv("TAB_BEARER_TOKEN")
        if not self.bearer_token:
            raise ValueError("Bearer token must be provided or set in TAB_BEARER_TOKEN environment variable")
            
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.bearer_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Origin": "https://tab.com.au",
            "Referer": "https://tab.com.au/",
            "x-tab-client": "tab-web",
            "x-tab-jurisdiction": "NSW",
            "x-tab-web-client": "1.0.0"
        })

        # Add proxy configuration if needed
        proxy_url = os.getenv("PROXY_URL")
        if proxy_url:
            self.session.proxies = {
                "http": proxy_url,
                "https": proxy_url
            }

    def _validate_response(self, response: requests.Response) -> Dict:
        """Validate API response and handle common errors"""
        try:
            content_type = response.headers.get('content-type', '')
            if 'text/html' in content_type:
                logger.error(f"Received HTML response: {response.text[:200]}")
                raise APIError("API access is restricted. Please ensure you're using correct authentication and headers.")
                
            if not response.content:
                raise APIError("Empty response received from server")
                
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse response: {str(e)}")
                logger.error(f"Response content: {response.text[:200]}")
                raise APIError(f"Invalid JSON response: {str(e)}")

            if isinstance(data, dict):
                if 'error' in data:
                    raise APIError(f"API Error: {data['error']}")
                return data
            elif isinstance(data, list):
                return {'data': data}
            else:
                raise APIError("Invalid response format")
            
        except Exception as e:
            logger.error(f"Response validation error: {str(e)}")
            raise APIError(f"Failed to validate response: {str(e)}")

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
                logger.debug(f"Request attempt {attempt + 1}: {method} {url}")
                logger.debug(f"Params: {params}")
                
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=headers,
                    timeout=30  # Increased timeout
                )
                
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    return self._validate_response(response)
                elif response.status_code == 401:
                    raise APIError("Authentication failed. Check your bearer token.")
                elif response.status_code == 403:
                    raise APIError("Insufficient permissions for this request.")
                elif response.status_code == 429:
                    if attempt < 2:
                        time.sleep(2)  # Increased delay between retries
                        continue
                    raise APIError("Rate limit exceeded. Please wait before retrying.")
                elif response.status_code == 400:
                    error_msg = "Bad request"
                    try:
                        error_data = response.json()
                        if 'message' in error_data:
                            error_msg = error_data['message']
                    except:
                        pass
                    raise APIError(f"Bad request: {error_msg}")
                else:
                    response.raise_for_status()
                    
            except APIError as e:
                if "restricted" in str(e).lower() or "authentication failed" in str(e).lower():
                    raise  # Don't retry auth/geoblocking issues
                if attempt == 2:
                    raise
                time.sleep(2)
                continue
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                if attempt == 2:
                    raise APIError(f"Request failed after 3 retries: {str(e)}")
                time.sleep(2)
                continue
        
        raise APIError("Request failed after all retries")

    def format_date(self, date_str: str) -> str:
        """Format date string to API expected format"""
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            return date.strftime("%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")

    def get_meetings(
        self,
        meeting_date: str,
        jurisdiction: str
    ) -> Dict:
        """Get meetings for a specific date"""
        formatted_date = self.format_date(meeting_date)
        return self._make_request(
            "GET",
            f"/v1/tab-info-service/racing/dates/{formatted_date}/meetings",
            params={"jurisdiction": jurisdiction},
            headers={"x-tab-jurisdiction": jurisdiction}
        )

    def get_races_in_meeting(
        self,
        meeting_date: str,
        race_type: Union[RaceType, str],
        venue_mnemonic: str,
        jurisdiction: str
    ) -> Dict:
        """Get all races in a meeting"""
        formatted_date = self.format_date(meeting_date)
        if isinstance(race_type, RaceType):
            race_type = race_type.value
            
        return self._make_request(
            "GET",
            f"/v1/tab-info-service/racing/dates/{formatted_date}/meetings/{race_type}/{venue_mnemonic}/races",
            params={"jurisdiction": jurisdiction},
            headers={"x-tab-jurisdiction": jurisdiction}
        )

    def get_next_to_go_races(
        self,
        jurisdiction: str,
        max_races: Optional[int] = None,
        include_fixed_odds: bool = False
    ) -> Dict:
        """Get next races to start"""
        params = {
            "jurisdiction": jurisdiction,
            "maxRaces": max_races,
            "includeFixedOdds": include_fixed_odds
        }
        
        return self._make_request(
            "GET",
            "/v1/tab-info-service/racing/next-to-go/races",
            params={k: v for k, v in params.items() if v is not None},
            headers={"x-tab-jurisdiction": jurisdiction}
        )

    def get_race_form(
        self,
        meeting_date: str,
        race_type: Union[RaceType, str],
        venue_mnemonic: str,
        race_number: int,
        jurisdiction: str,
        fixed_odds: bool = False
    ) -> Dict:
        """Get form for a specific race"""
        formatted_date = self.format_date(meeting_date)
        if isinstance(race_type, RaceType):
            race_type = race_type.value
            
        return self._make_request(
            "GET",
            f"/v1/tab-info-service/racing/dates/{formatted_date}/meetings/{race_type}/{venue_mnemonic}/races/{race_number}/form",
            params={
                "jurisdiction": jurisdiction,
                "fixedOdds": fixed_odds
            },
            headers={"x-tab-jurisdiction": jurisdiction}
        )
