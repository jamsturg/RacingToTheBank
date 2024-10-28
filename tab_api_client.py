import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import requests
import json
import time
import pytz
from dataclasses import dataclass
from enum import Enum
import os
import asyncio
from utils.logger import api_logger

class RaceType(Enum):
    THOROUGHBRED = "R"
    HARNESS = "H"
    GREYHOUND = "G"

class APIError(Exception):
    """Custom exception for API errors"""
    pass

class TABApiClient:
    """Simplified TAB API Client"""
    
    def __init__(self):
        self.base_url = "https://api.tab.com.au"
        self.logger = logging.getLogger(__name__)

    def get_mock_data(self) -> Dict:
        """Get mock race data for development"""
        return {
            'races': [
                {
                    'meeting': {
                        'venueName': 'Randwick',
                        'location': 'NSW'
                    },
                    'raceNumber': 1,
                    'raceDistance': 1200,
                    'raceStartTime': '14:00',
                    'runners': [
                        {
                            'runnerNumber': 1,
                            'runnerName': 'Horse 1',
                            'barrier': 4,
                            'weight': 56.5,
                            'jockey': 'J. Smith',
                            'fixedOdds': {'returnWin': 2.40}
                        },
                        {
                            'runnerNumber': 2,
                            'runnerName': 'Horse 2',
                            'barrier': 7,
                            'weight': 55.0,
                            'jockey': 'T. Berry',
                            'fixedOdds': {'returnWin': 3.50}
                        }
                    ]
                }
            ]
        }

    def get_next_to_go_races(self, jurisdiction: str = "NSW", max_races: int = 5, include_fixed_odds: bool = True) -> Dict:
        """Get next races to jump"""
        try:
            # Add retry logic for API calls
            max_retries = 3
            retry_delay = 1  # seconds
            
            for attempt in range(max_retries):
                try:
                    # For development, return mock data
                    return self.get_mock_data()
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        raise APIError(f"Failed to get next races after {max_retries} attempts: {str(e)}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    
        except Exception as e:
            self.logger.error(f"Error getting next races: {str(e)}")
            # Return empty but valid structure instead of empty list
            return {'races': [], 'error': str(e)}

    def get_featured_races(self) -> List[Dict]:
        """Get featured races"""
        try:
            # Add error handling for API timeouts
            timeout = 10  # seconds
            # Return mock featured races
            return [
                {
                    'raceId': '1',
                    'raceName': 'The Metropolitan',
                    'prizeMoney': 750000,
                    'raceDistance': 2400,
                    'status': 'OPEN'  # Add status field
                },
                {
                    'raceId': '2',
                    'raceName': 'Epsom Handicap',
                    'prizeMoney': 1000000,
                    'raceDistance': 1600,
                    'status': 'OPEN'
                }
            ]
        except Exception as e:
            self.logger.error(f"Error getting featured races: {str(e)}")
            return []

    def get_market_movers(self) -> List[Dict]:
        """Get market movers"""
        try:
            # Return mock market movers
            return [
                {
                    'runnerName': 'Horse 1',
                    'times': ['13:00', '13:30', '14:00'],
                    'odds': [2.80, 2.60, 2.40]
                },
                {
                    'runnerName': 'Horse 2',
                    'times': ['13:00', '13:30', '14:00'],
                    'odds': [3.00, 3.20, 3.50]
                }
            ]
        except Exception as e:
            self.logger.error(f"Error getting market movers: {str(e)}")
            return []

    def search_runner(self, name: str) -> Optional[Dict]:
        """Search for a runner by name"""
        try:
            # Return mock runner data
            return {
                'runnerName': name,
                'form': '1-2-1',
                'lastFive': [
                    {'position': 1, 'prize': 50000},
                    {'position': 2, 'prize': 30000},
                    {'position': 1, 'prize': 45000}
                ]
            }
        except Exception as e:
            self.logger.error(f"Error searching runner: {str(e)}")
            return None
