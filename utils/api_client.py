import requests
from config import Config
from typing import Dict, List, Optional
import logging

class RacingAPIClient:
    def __init__(self):
        self.api_key = Config.PUNTING_FORM_API_KEY
        self.base_url = 'https://api.puntingform.com.au/v2/form'
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def get_meetings(self, date: str = None) -> List[Dict]:
        try:
            url = f"{self.base_url}/meetingslist"
            params = {
                'meetingDate': date,
                'apiKey': self.api_key
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get('payLoad', [])
            else:
                self.logger.error(f"Error fetching meetings: {response.status_code}")
                return []
        except Exception as e:
            self.logger.error(f"Error fetching meetings: {str(e)}")
            return []

    def get_race_data(self, meeting_id: str, race_number: int) -> Optional[Dict]:
        """Get detailed race data"""
        try:
            url = f"{self.base_url}/form"
            params = {
                'meetingId': meeting_id,
                'raceNumber': race_number,
                'apiKey': self.api_key
            }
            response = requests.get(url, params=params)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            self.logger.error(f"Error getting race data: {str(e)}")
            return None
