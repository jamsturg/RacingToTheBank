from typing import Dict, List, Optional, Union
from datetime import datetime
import requests
import logging
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
    """
    Complete TAB API Client implementing all available endpoints
    """
    
    def __init__(self, bearer_token: Optional[str] = None):
        self.base_url = "https://api.beta.tab.com.au"
        self.bearer_token = bearer_token or os.getenv("TAB_BEARER_TOKEN")
        if not self.bearer_token:
            raise ValueError("Bearer token must be provided or set in TAB_BEARER_TOKEN environment variable")
            
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.bearer_token}"
        })

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict:
        """Make API request with error handling"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers
            )
            
            logger.debug(f"Request: {method} {url}")
            logger.debug(f"Params: {params}")
            logger.debug(f"Response status: {response.status_code}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error occurred: {str(e)}")
            if response.status_code == 401:
                raise APIError("Authentication failed. Check your bearer token.")
            elif response.status_code == 403:
                raise APIError("Insufficient permissions for this request.")
            elif response.status_code == 429:
                raise APIError("Rate limit exceeded. Please wait before retrying.")
            raise APIError(f"HTTP error occurred: {str(e)}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise APIError(f"Request failed: {str(e)}")

    # Racing Endpoints
    
    def get_meeting_dates(self, jurisdiction: str) -> Dict:
        """
        Get all available meeting dates
        
        Args:
            jurisdiction: State jurisdiction (e.g., 'NSW', 'VIC')
            
        Returns:
            Dict containing available dates and their details
        """
        return self._make_request(
            "GET",
            "/v1/tab-info-service/racing/dates",
            params={"jurisdiction": jurisdiction}
        )

    def get_meetings(
        self,
        meeting_date: str,
        jurisdiction: str
    ) -> Dict:
        """
        Get meetings for a specific date
        
        Args:
            meeting_date: Date in YYYY-MM-DD format
            jurisdiction: State jurisdiction
            
        Returns:
            Dict containing meeting details
        """
        return self._make_request(
            "GET",
            f"/v1/tab-info-service/racing/dates/{meeting_date}/meetings",
            params={"jurisdiction": jurisdiction}
        )

    def get_races_in_meeting(
        self,
        meeting_date: str,
        race_type: Union[RaceType, str],
        venue_mnemonic: str,
        jurisdiction: str
    ) -> Dict:
        """
        Get all races in a meeting
        
        Args:
            meeting_date: Date in YYYY-MM-DD format
            race_type: RaceType enum or string ('R', 'H', 'G')
            venue_mnemonic: Three-letter venue code
            jurisdiction: State jurisdiction
            
        Returns:
            Dict containing race details
        """
        if isinstance(race_type, RaceType):
            race_type = race_type.value
            
        return self._make_request(
            "GET",
            f"/v1/tab-info-service/racing/dates/{meeting_date}/meetings/{race_type}/{venue_mnemonic}/races",
            params={"jurisdiction": jurisdiction}
        )

    def get_next_to_go_races(
        self,
        jurisdiction: str,
        max_races: Optional[int] = None,
        include_recently_closed: bool = False,
        wagering_product: Optional[str] = None,
        include_fixed_odds: bool = False
    ) -> Dict:
        """
        Get next races to start
        
        Args:
            jurisdiction: State jurisdiction
            max_races: Maximum number of races to return
            include_recently_closed: Include recently closed races
            wagering_product: Specific wagering product
            include_fixed_odds: Include fixed odds information
            
        Returns:
            Dict containing next races
        """
        params = {
            "jurisdiction": jurisdiction,
            "maxRaces": max_races,
            "includeRecentlyClosed": include_recently_closed,
            "wageringProduct": wagering_product,
            "includeFixedOdds": include_fixed_odds
        }
        
        return self._make_request(
            "GET",
            "/v1/tab-info-service/racing/next-to-go/races",
            params={k: v for k, v in params.items() if v is not None}
        )

    def get_race(
        self,
        meeting_date: str,
        race_type: Union[RaceType, str],
        venue_mnemonic: str,
        race_number: int,
        jurisdiction: str,
        fixed_odds: bool = False
    ) -> Dict:
        """
        Get details for a specific race
        
        Args:
            meeting_date: Date in YYYY-MM-DD format
            race_type: RaceType enum or string
            venue_mnemonic: Three-letter venue code
            race_number: Race number
            jurisdiction: State jurisdiction
            fixed_odds: Include fixed odds information
            
        Returns:
            Dict containing race details
        """
        if isinstance(race_type, RaceType):
            race_type = race_type.value
            
        return self._make_request(
            "GET",
            f"/v1/tab-info-service/racing/dates/{meeting_date}/meetings/{race_type}/{venue_mnemonic}/races/{race_number}",
            params={
                "jurisdiction": jurisdiction,
                "fixedOdds": fixed_odds
            }
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
        """
        Get form for a specific race
        
        Args:
            meeting_date: Date in YYYY-MM-DD format
            race_type: RaceType enum or string
            venue_mnemonic: Three-letter venue code
            race_number: Race number
            jurisdiction: State jurisdiction
            fixed_odds: Include fixed odds information
            
        Returns:
            Dict containing race form details
        """
        if isinstance(race_type, RaceType):
            race_type = race_type.value
            
        return self._make_request(
            "GET",
            f"/v1/tab-info-service/racing/dates/{meeting_date}/meetings/{race_type}/{venue_mnemonic}/races/{race_number}/form",
            params={
                "jurisdiction": jurisdiction,
                "fixedOdds": fixed_odds
            }
        )

    def get_runner_form(
        self,
        meeting_date: str,
        race_type: Union[RaceType, str],
        venue_mnemonic: str,
        race_number: int,
        runner_number: int,
        jurisdiction: str,
        fixed_odds: bool = False
    ) -> Dict:
        """
        Get form for a specific runner
        
        Args:
            meeting_date: Date in YYYY-MM-DD format
            race_type: RaceType enum or string
            venue_mnemonic: Three-letter venue code
            race_number: Race number
            runner_number: Runner number
            jurisdiction: State jurisdiction
            fixed_odds: Include fixed odds information
            
        Returns:
            Dict containing runner form details
        """
        if isinstance(race_type, RaceType):
            race_type = race_type.value
            
        return self._make_request(
            "GET",
            f"/v1/tab-info-service/racing/dates/{meeting_date}/meetings/{race_type}/{venue_mnemonic}/races/{race_number}/runners/{runner_number}/form",
            params={
                "jurisdiction": jurisdiction,
                "fixedOdds": fixed_odds
            }
        )

    def get_race_big_bet(
        self,
        meeting_date: str,
        race_type: Union[RaceType, str],
        venue_mnemonic: str,
        race_number: int,
        jurisdiction: str
    ) -> Dict:
        """
        Get big bet information for a race
        
        Args:
            meeting_date: Date in YYYY-MM-DD format
            race_type: RaceType enum or string
            venue_mnemonic: Three-letter venue code
            race_number: Race number
            jurisdiction: State jurisdiction
            
        Returns:
            Dict containing big bet information
        """
        if isinstance(race_type, RaceType):
            race_type = race_type.value
            
        return self._make_request(
            "GET",
            f"/v1/tab-info-service/racing/dates/{meeting_date}/meetings/{race_type}/{venue_mnemonic}/races/{race_number}/big-bets",
            params={"jurisdiction": jurisdiction}
        )

    def get_jackpot_pools(
        self,
        meeting_date: str,
        jurisdiction: str
    ) -> Dict:
        """
        Get jackpot pools for a date
        
        Args:
            meeting_date: Date in YYYY-MM-DD format
            jurisdiction: State jurisdiction
            
        Returns:
            Dict containing jackpot pool information
        """
        return self._make_request(
            "GET",
            f"/v1/tab-info-service/racing/dates/{meeting_date}/jackpot-pools",
            params={"jurisdiction": jurisdiction}
        )

    def get_open_jackpots(self, jurisdiction: str) -> Dict:
        """
        Get all open jackpots
        
        Args:
            jurisdiction: State jurisdiction
            
        Returns:
            Dict containing open jackpot information
        """
        return self._make_request(
            "GET",
            "/v1/tab-info-service/racing/jackpots",
            params={"jurisdiction": jurisdiction}
        )

    def get_approximates(
        self,
        meeting_date: str,
        race_type: Union[RaceType, str],
        venue_mnemonic: str,
        race_number: int,
        wagering_product: str,
        jurisdiction: str
    ) -> Dict:
        """
        Get pool approximates for a race
        
        Args:
            meeting_date: Date in YYYY-MM-DD format
            race_type: RaceType enum or string
            venue_mnemonic: Three-letter venue code
            race_number: Race number
            wagering_product: Product type
            jurisdiction: State jurisdiction
            
        Returns:
            Dict containing pool approximate information
        """
        if isinstance(race_type, RaceType):
            race_type = race_type.value
            
        return self._make_request(
            "GET",
            f"/v1/tab-info-service/racing/dates/{meeting_date}/meetings/{race_type}/{venue_mnemonic}/races/{race_number}/pools/{wagering_product}/approximates",
            params={"jurisdiction": jurisdiction}
        )

def main():
    """Example usage of TAB API Client"""
    try:
        # Initialize client
        client = TABApiClient()
        
        # Get next races
        next_races = client.get_next_to_go_races(
            jurisdiction="NSW",
            max_races=5,
            include_fixed_odds=True
        )
        
        # Print race details
        for race in next_races.get("races", []):
            print(f"\nRace {race['raceNumber']} at {race['meeting']['venueName']}")
            print(f"Start Time: {race['raceStartTime']}")
            print(f"Distance: {race['raceDistance']}m")
            
            print("\nRunners:")
            for runner in race.get("runners", []):
                fixed_odds = runner.get("fixedOdds", {}).get("returnWin", "N/A")
                print(f"{runner['runnerNumber']}. {runner['runnerName']} (${fixed_odds})")
                
    except APIError as e:
        logger.error(f"API Error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()