import requests
from config import Config
from typing import Dict, List, Optional, Union, Any
import logging
from datetime import datetime, timedelta
import time
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import json
from functools import lru_cache
import asyncio
import aiohttp
from ratelimit import limits, sleep_and_retry
from .logger import get_logger

class APIRateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period
        self.timestamps = []

    def __call__(self, func):
        async def wrapper(*args, **kwargs):
            now = time.time()
            self.timestamps = [ts for ts in self.timestamps if ts > now - self.period]
            
            if len(self.timestamps) >= self.calls:
                sleep_time = self.timestamps[0] - (now - self.period)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
            
            self.timestamps.append(now)
            return await func(*args, **kwargs)
        return wrapper

class APICache:
    """Cache for API responses"""
    
    def __init__(self, ttl: int = 300):  # 5 minutes default TTL
        self.cache = {}
        self.ttl = ttl

    def get(self, key: str) -> Optional[Dict]:
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.ttl):
                return data
            del self.cache[key]
        return None

    def set(self, key: str, value: Dict):
        self.cache[key] = (value, datetime.now())

    def clear(self):
        self.cache.clear()

class RacingAPIClient:
    """Enhanced Racing API client with advanced features"""
    
    def __init__(self):
        self.api_key = Config.PUNTING_FORM_API_KEY
        self.base_url = 'https://api.puntingform.com.au/v2/form'
        self.logger = get_logger(__name__)
        self.cache = APICache()
        self.setup_session()

    def setup_session(self):
        """Configure requests session with retry logic and proper headers"""
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
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

    async def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        use_cache: bool = True
    ) -> Optional[Dict]:
        """Make API request with enhanced error handling and caching"""
        if not self.api_key:
            self.logger.error("API key is missing")
            raise ValueError("API key is required")

        cache_key = f"{method}:{url}:{json.dumps(params)}:{json.dumps(data)}"
        
        if use_cache:
            cached_response = self.cache.get(cache_key)
            if cached_response:
                self.logger.debug(f"Cache hit for {cache_key}")
                return cached_response

        try:
            params = params or {}
            params['apiKey'] = self.api_key

            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    params=params,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    if not data:
                        raise ValueError("Empty response received")
                    
                    if use_cache:
                        self.cache.set(cache_key, data)
                    
                    return data

        except aiohttp.ClientTimeout:
            self.logger.error("Request timed out")
            raise TimeoutError("API request timed out")
        except aiohttp.ClientConnectionError:
            self.logger.error("Connection error occurred")
            raise ConnectionError("Failed to connect to API")
        except aiohttp.ClientResponseError as e:
            self.logger.error(f"HTTP error occurred: {str(e)}")
            raise
        except ValueError as e:
            self.logger.error(f"Invalid response: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            raise

    @APIRateLimiter(calls=100, period=60)  # 100 calls per minute
    async def get_meetings(
        self,
        date: Optional[str] = None,
        track: Optional[str] = None,
        state: Optional[str] = None
    ) -> List[Dict]:
        """Get race meetings with enhanced filtering"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            params = {'meetingDate': date}
            if track:
                params['track'] = track
            if state:
                params['state'] = state
            
            url = f"{self.base_url}/meetingslist"
            data = await self._make_request('GET', url, params=params)
            
            if isinstance(data, dict) and 'payLoad' in data:
                meetings = data['payLoad']
                if isinstance(meetings, list):
                    self.logger.info(f"Successfully fetched {len(meetings)} meetings")
                    return meetings
            
            raise ValueError("Invalid data format received from API")
            
        except Exception as e:
            self.logger.error(f"Error fetching meetings: {str(e)}")
            raise

    @APIRateLimiter(calls=100, period=60)
    async def get_race_data(
        self,
        meeting_id: str,
        race_number: int,
        include_scratched: bool = False
    ) -> Optional[Dict]:
        """Get detailed race data with enhanced options"""
        try:
            if not meeting_id or not isinstance(race_number, int) or not (1 <= race_number <= 12):
                raise ValueError("Invalid meeting ID or race number")

            url = f"{self.base_url}/form"
            params = {
                'meetingId': meeting_id,
                'raceNumber': race_number,
                'includeScratched': include_scratched
            }

            data = await self._make_request('GET', url, params=params)
            if isinstance(data, dict):
                self.logger.info(f"Successfully fetched race data for meeting {meeting_id}, race {race_number}")
                return data

            raise ValueError("Invalid data format received from API")

        except Exception as e:
            self.logger.error(f"Error fetching race data: {str(e)}")
            raise

    async def check_api_health(self) -> Dict[str, Any]:
        """Enhanced API health check with detailed status"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/meetingslist"
            params = {'meetingDate': datetime.now().strftime("%Y-%m-%d")}
            
            response = await self._make_request('GET', url, params=params, use_cache=False)
            
            latency = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            return {
                'status': 'healthy',
                'latency_ms': round(latency, 2),
                'timestamp': datetime.now().isoformat(),
                'api_version': '2.0',
                'cache_size': len(self.cache.cache)
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def clear_cache(self):
        """Clear the API cache"""
        self.cache.clear()
        self.logger.info("API cache cleared")

class TABApiClient(RacingAPIClient):
    """Enhanced TAB API client with advanced features"""
    
    def __init__(self):
        super().__init__()
        self.tab_base_url = 'https://api.tab.com.au/v1'
        self.setup_tab_session()

    def setup_tab_session(self):
        """Configure TAB-specific session settings"""
        self.tab_session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.tab_session.mount("http://", adapter)
        self.tab_session.mount("https://", adapter)
        
        self.tab_session.headers.update({
            'User-Agent': 'TABRacingAnalysis/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    @APIRateLimiter(calls=100, period=60)
    async def get_odds(
        self,
        meeting_id: str,
        race_number: int,
        bet_type: str = 'WIN'
    ) -> Optional[Dict]:
        """Get current odds with enhanced options"""
        try:
            url = f"{self.tab_base_url}/racing/{meeting_id}/races/{race_number}/odds"
            params = {'betType': bet_type}
            
            data = await self._make_request('GET', url, params=params)
            if not data:
                raise ValueError("Empty response received")
                
            self.logger.info(f"Successfully fetched odds for meeting {meeting_id}, race {race_number}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching odds: {str(e)}")
            return None

    @APIRateLimiter(calls=100, period=60)
    async def get_fluctuations(
        self,
        meeting_id: str,
        race_number: int,
        runner_number: Optional[int] = None
    ) -> Optional[Dict]:
        """Get price fluctuations with filtering"""
        try:
            url = f"{self.tab_base_url}/racing/{meeting_id}/races/{race_number}/fluctuations"
            params = {}
            if runner_number:
                params['runnerNumber'] = runner_number
            
            data = await self._make_request('GET', url, params=params)
            if not data:
                raise ValueError("Empty response received")
                
            self.logger.info(f"Successfully fetched fluctuations for meeting {meeting_id}, race {race_number}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching fluctuations: {str(e)}")
            return None

    @APIRateLimiter(calls=100, period=60)
    async def get_results(
        self,
        meeting_id: str,
        race_number: int,
        include_dividends: bool = True
    ) -> Optional[Dict]:
        """Get race results with enhanced options"""
        try:
            url = f"{self.tab_base_url}/racing/{meeting_id}/races/{race_number}/results"
            params = {'includeDividends': include_dividends}
            
            data = await self._make_request('GET', url, params=params)
            if not data:
                raise ValueError("Empty response received")
                
            self.logger.info(f"Successfully fetched results for meeting {meeting_id}, race {race_number}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching results: {str(e)}")
            return None

    @APIRateLimiter(calls=100, period=60)
    async def get_speed_maps(
        self,
        meeting_id: str,
        race_number: int,
        include_historical: bool = False
    ) -> Optional[Dict]:
        """Get speed maps with enhanced options"""
        try:
            url = f"{self.tab_base_url}/racing/{meeting_id}/races/{race_number}/speedmaps"
            params = {'includeHistorical': include_historical}
            
            data = await self._make_request('GET', url, params=params)
            if not data:
                raise ValueError("Empty response received")
                
            self.logger.info(f"Successfully fetched speed maps for meeting {meeting_id}, race {race_number}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching speed maps: {str(e)}")
            return None

    @APIRateLimiter(calls=100, period=60)
    async def get_track_conditions(
        self,
        meeting_id: str,
        include_history: bool = False
    ) -> Optional[Dict]:
        """Get track conditions with enhanced options"""
        try:
            url = f"{self.tab_base_url}/racing/{meeting_id}/conditions"
            params = {'includeHistory': include_history}
            
            data = await self._make_request('GET', url, params=params)
            if not data:
                raise ValueError("Empty response received")
                
            self.logger.info(f"Successfully fetched track conditions for meeting {meeting_id}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching track conditions: {str(e)}")
            return None

    @APIRateLimiter(calls=100, period=60)
    async def get_runner_history(
        self,
        runner_id: str,
        limit: int = 10
    ) -> Optional[Dict]:
        """Get runner's racing history"""
        try:
            url = f"{self.tab_base_url}/racing/runners/{runner_id}/history"
            params = {'limit': limit}
            
            data = await self._make_request('GET', url, params=params)
            if not data:
                raise ValueError("Empty response received")
                
            self.logger.info(f"Successfully fetched history for runner {runner_id}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching runner history: {str(e)}")
            return None

    @APIRateLimiter(calls=100, period=60)
    async def get_jockey_statistics(
        self,
        jockey_id: str,
        period: str = '12M'
    ) -> Optional[Dict]:
        """Get jockey performance statistics"""
        try:
            url = f"{self.tab_base_url}/racing/jockeys/{jockey_id}/statistics"
            params = {'period': period}
            
            data = await self._make_request('GET', url, params=params)
            if not data:
                raise ValueError("Empty response received")
                
            self.logger.info(f"Successfully fetched statistics for jockey {jockey_id}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching jockey statistics: {str(e)}")
            return None
