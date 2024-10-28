import requests
from config import Config
from typing import Dict, List, Optional, Union
import logging
from datetime import datetime, timedelta
import time
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

class RacingAPIClient:
    def __init__(self):
        self.api_key = Config.PUNTING_FORM_API_KEY
        self.base_url = 'https://api.puntingform.com.au/v2/form'
        self.setup_logging()
        self.setup_session()

    def setup_logging(self):
        """Initialize logging configuration"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def setup_session(self):
        """Configure requests session with retry logic and proper headers"""
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,  # Maximum number of retries
            backoff_factor=0.5,  # Wait 0.5s * (2 ^ (retry - 1)) between retries
            status_forcelist=[429, 500, 502, 503, 504],  # HTTP status codes to retry on
            allowed_methods=["GET", "POST"]
        )
        
        # Mount the adapter to the session
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'RacingAnalysisPlatform/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        })

    def _make_request(self, url: str, params: Dict) -> Optional[Dict]:
        """Make API request with enhanced error handling and retries"""
        if not self.api_key:
            self.logger.error("API key is missing")
            raise ValueError("API key is required")

        try:
            # Add API key to params
            params['apiKey'] = self.api_key

            # Make request with timeout
            response = self.session.get(
                url,
                params=params,
                timeout=(5, 30)  # (connect timeout, read timeout)
            )
            
            response.raise_for_status()  # Raise exception for bad status codes
            
            data = response.json()
            if not data:
                raise ValueError("Empty response received")
            return data

        except requests.exceptions.Timeout:
            self.logger.error("Request timed out")
            raise TimeoutError("API request timed out")
        except requests.exceptions.ConnectionError:
            self.logger.error("Connection error occurred")
            raise ConnectionError("Failed to connect to API")
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error occurred: {str(e)}")
            raise
        except ValueError as e:
            self.logger.error(f"Invalid response: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            raise

    def get_meetings(self, date: Optional[str] = None) -> List[Dict]:
        """Get race meetings for a specific date with enhanced error handling"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            url = f"{self.base_url}/meetingslist"
            params = {'meetingDate': date}
            
            self.logger.info(f"Fetching meetings for date: {date}")
            data = self._make_request(url, params)
            
            if isinstance(data, dict) and 'payLoad' in data:
                meetings = data['payLoad']
                if isinstance(meetings, list):
                    self.logger.info(f"Successfully fetched {len(meetings)} meetings")
                    return meetings
            
            raise ValueError("Invalid data format received from API")
            
        except Exception as e:
            self.logger.error(f"Error fetching meetings: {str(e)}")
            raise

    def get_race_data(self, meeting_id: str, race_number: int) -> Optional[Dict]:
        """Get detailed race data with enhanced validation and error handling"""
        try:
            if not meeting_id or not isinstance(race_number, int) or not (1 <= race_number <= 12):
                raise ValueError("Invalid meeting ID or race number")

            url = f"{self.base_url}/form"
            params = {
                'meetingId': meeting_id,
                'raceNumber': race_number
            }

            data = self._make_request(url, params)
            if isinstance(data, dict):
                self.logger.info(f"Successfully fetched race data for meeting {meeting_id}, race {race_number}")
                return data

            raise ValueError("Invalid data format received from API")

        except Exception as e:
            self.logger.error(f"Error fetching race data: {str(e)}")
            raise

    def check_api_health(self) -> bool:
        """Check API health and connectivity with enhanced error handling"""
        try:
            url = f"{self.base_url}/meetingslist"
            params = {'meetingDate': datetime.now().strftime("%Y-%m-%d")}
            response = self._make_request(url, params)
            return bool(response and isinstance(response, dict))
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False

class TABApiClient(RacingAPIClient):
    """Enhanced API client with TAB-specific functionality"""
    
    def __init__(self):
        super().__init__()
        self.tab_base_url = 'https://api.tab.com.au/v1'
        self.setup_tab_session()

    def setup_tab_session(self):
        """Configure TAB-specific session settings"""
        self.tab_session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        # Mount the adapter to the session
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.tab_session.mount("http://", adapter)
        self.tab_session.mount("https://", adapter)
        
        # Set TAB-specific headers
        self.tab_session.headers.update({
            'User-Agent': 'TABRacingAnalysis/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    def get_odds(self, meeting_id: str, race_number: int) -> Optional[Dict]:
        """Get current odds for a race"""
        try:
            url = f"{self.tab_base_url}/racing/{meeting_id}/races/{race_number}/odds"
            response = self.tab_session.get(url, timeout=(5, 30))
            response.raise_for_status()
            
            data = response.json()
            if not data:
                raise ValueError("Empty response received")
                
            self.logger.info(f"Successfully fetched odds for meeting {meeting_id}, race {race_number}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching odds: {str(e)}")
            return None

    def get_fluctuations(self, meeting_id: str, race_number: int) -> Optional[Dict]:
        """Get price fluctuations for a race"""
        try:
            url = f"{self.tab_base_url}/racing/{meeting_id}/races/{race_number}/fluctuations"
            response = self.tab_session.get(url, timeout=(5, 30))
            response.raise_for_status()
            
            data = response.json()
            if not data:
                raise ValueError("Empty response received")
                
            self.logger.info(f"Successfully fetched fluctuations for meeting {meeting_id}, race {race_number}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching fluctuations: {str(e)}")
            return None

    def get_results(self, meeting_id: str, race_number: int) -> Optional[Dict]:
        """Get race results"""
        try:
            url = f"{self.tab_base_url}/racing/{meeting_id}/races/{race_number}/results"
            response = self.tab_session.get(url, timeout=(5, 30))
            response.raise_for_status()
            
            data = response.json()
            if not data:
                raise ValueError("Empty response received")
                
            self.logger.info(f"Successfully fetched results for meeting {meeting_id}, race {race_number}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching results: {str(e)}")
            return None

    def get_speed_maps(self, meeting_id: str, race_number: int) -> Optional[Dict]:
        """Get speed maps for a race"""
        try:
            url = f"{self.tab_base_url}/racing/{meeting_id}/races/{race_number}/speedmaps"
            response = self.tab_session.get(url, timeout=(5, 30))
            response.raise_for_status()
            
            data = response.json()
            if not data:
                raise ValueError("Empty response received")
                
            self.logger.info(f"Successfully fetched speed maps for meeting {meeting_id}, race {race_number}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching speed maps: {str(e)}")
            return None

    def get_track_conditions(self, meeting_id: str) -> Optional[Dict]:
        """Get track conditions for a meeting"""
        try:
            url = f"{self.tab_base_url}/racing/{meeting_id}/conditions"
            response = self.tab_session.get(url, timeout=(5, 30))
            response.raise_for_status()
            
            data = response.json()
            if not data:
                raise ValueError("Empty response received")
                
            self.logger.info(f"Successfully fetched track conditions for meeting {meeting_id}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching track conditions: {str(e)}")
            return None
