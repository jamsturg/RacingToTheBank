import os
import json
import requests
from datetime import datetime
import logging
from typing import List, Dict, Tuple
import pandas as pd
import numpy as np

BASE_URL = 'https://api.puntingform.com.au/v2/form'

class PuntingFormAPI:
    def __init__(self):
        self.api_key = '7552b21e-851b-4803-b230-d1637a74f05c'

    def get_meetings_list(self, meeting_date):
        url = f"{BASE_URL}/meetingslist"
        params = {
            'meetingDate': meeting_date,
            'apiKey': self.api_key
        }
        response = requests.get(url, params=params)
        return response.json()

    def get_form_guide(self, meeting_id, race_number):
        url = f"{BASE_URL}/form"
        params = {
            'meetingId': meeting_id,
            'raceNumber': race_number,
            'apiKey': self.api_key
        }
        response = requests.get(url, params=params)
        return response.json()

    def get_ratings(self, meeting_id, race_number):
        url = f"{BASE_URL}/ratings"
        params = {
            'meetingId': meeting_id,
            'raceNumber': race_number,
            'apiKey': self.api_key
        }
        response = requests.get(url, params=params)
        return response.json()

class RacePredictionTool:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.api = PuntingFormAPI()
        
        # Initialize prediction weights
        self.weight_factors = {
            'pfais_score': 0.25,
            'recent_form': 0.20,
            'track_condition': 0.15,
            'distance_form': 0.15,
            'weight_penalty': 0.10,
            'barrier_position': 0.05,
            'jockey_trainer': 0.10
        }

    def get_race_meetings(self, date: str = None) -> List:
        """Fetch available race meetings for a given date"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
            
        self.logger.info(f"Fetching meetings for date: {date}")
        
        try:
            response = self.api.get_meetings_list(date)
            meetings = response.get('meetings', [])
            self.logger.info(f"Retrieved {len(meetings)} meetings")
            return meetings
        except Exception as e:
            self.logger.error(f"Error fetching meetings: {str(e)}")
            return []

    def get_race_data(self, meeting_id: str, race_number: int) -> Dict:
        """Fetch detailed race data for a specific meeting"""
        self.logger.info(f"Fetching race data for meeting {meeting_id}, race {race_number}")
        
        try:
            form_guide = self.api.get_form_guide(meeting_id, race_number)
            ratings = self.api.get_ratings(meeting_id, race_number)
            return {'form_guide': form_guide, 'ratings': ratings}
        except Exception as e:
            self.logger.error(f"Error fetching race data: {str(e)}")
            return {"error": str(e)}

    def parse_horse_data(self, race_data: Dict) -> List[Dict]:
        """Parse raw race data into structured format for analysis"""
        horses = []
        
        try:
            form_guide = race_data.get('form_guide', {}).get('runners', [])
            ratings = race_data.get('ratings', {}).get('runners', [])
            
            for runner in form_guide:
                horse_id = runner.get('runnerId')
                rating = next((r['rating'] for r in ratings if r['runnerId'] == horse_id), None)
                
                horse = {
                    'Horse': runner.get('runnerName'),
                    'PFAIS': rating,
                    'Wt': runner.get('handicapWeight'),
                    'Bar': runner.get('barrierNumber'),
                    'last_5': runner.get('last5Runs'),
                    'Distance': runner.get('distanceRecord', '0: 0-0-0'),
                    'Track': runner.get('trackRecord', '0: 0-0-0'),
                    'Jockey': runner.get('jockeyName'),
                    'Trainer': runner.get('trainerName')
                }
                horses.append(horse)
                
        except Exception as e:
            self.logger.error(f"Error parsing horse data: {str(e)}")
            
        return horses

    def calculate_performance_scores(self, horse: Dict) -> float:
        """Calculate comprehensive performance score for a horse"""
        
        # Calculate PFAIS score
        pfais = float(horse.get('PFAIS', 0))
        pfais_score = (pfais / 100) * 100 if pfais else 0
        
        # Calculate recent form score
        last_5 = horse.get('last_5', '')
        form_score = self.analyze_recent_form(last_5)
        
        # Calculate distance aptitude
        distance_record = horse.get('Distance', '0: 0-0-0')
        distance_score = self.calculate_distance_score(distance_record)
        
        # Weight factor
        weight = float(horse.get('Wt', '57').split('(')[0])
        weight_score = (1 - (weight / 60)) * 100  # Assuming max weight of 60kg
        
        # Barrier draw factor
        barrier = int(horse.get('Bar', 1))
        barrier_score = 100 - (abs(barrier - 6) * 5)  # Middle barriers preferred
        
        # Calculate weighted final score
        final_score = (
            pfais_score * self.weight_factors['pfais_score'] +
            form_score * self.weight_factors['recent_form'] +
            distance_score * self.weight_factors['distance_form'] +
            weight_score * self.weight_factors['weight_penalty'] +
            barrier_score * self.weight_factors['barrier_position']
        )
        
        return final_score

    def analyze_recent_form(self, form_string: str) -> float:
        """Analyze horse's recent form"""
        if not form_string:
            return 0
            
        points = {
            '1': 100, '2': 80, '3': 60, '4': 40, '5': 20,
            '6': 10, '7': 10, '8': 10, '9': 10, '0': 0, 'x': 0
        }
        
        total = 0
        count = 0
        weights = [1.5, 1.3, 1.1, 1.0, 0.9]
        
        for i, result in enumerate(form_string[:5]):
            if result in points:
                total += points[result] * weights[i]
                count += 1
                
        return (total / (count * 1.5 * 100)) * 100 if count else 0

    def calculate_distance_score(self, distance_record: str) -> float:
        """Calculate horse's aptitude at the race distance"""
        try:
            starts, record = distance_record.split(': ')
            wins, places, thirds = map(int, record.split('-'))
            
            if int(starts) == 0:
                return 50  # Neutral score for unproven horses
                
            win_rate = (wins / int(starts)) * 100
            place_rate = (places / int(starts)) * 50
            
            return min((win_rate + place_rate), 100)
            
        except Exception:
            return 50  # Default to neutral score if there's an error

    def predict_race(self, meeting_id: str, race_number: int) -> List[Tuple[str, float]]:
        """Generate predictions for a specific race"""
        try:
            # Fetch race data
            race_data = self.get_race_data(meeting_id, race_number)
            
            # Parse horse data
            horses = self.parse_horse_data(race_data)
            
            # Calculate scores and create predictions
            predictions = []
            for horse in horses:
                if horse['Horse']:  # Exclude scratched horses
                    score = self.calculate_performance_scores(horse)
                    predictions.append((horse['Horse'], score))
            
            # Sort by score and return top predictions
            return sorted(predictions, key=lambda x: x[1], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error in race prediction: {str(e)}")
            return []

    def analyze_race(self, meeting_id: str, race_number: int) -> str:
        """Provide comprehensive race analysis with predictions"""
        predictions = self.predict_race(meeting_id, race_number)
        
        if not predictions:
            return "Unable to generate predictions for this race."
            
        analysis = "Race Analysis:\n\n"
        
        # Top 3 selections
        analysis += "Top 3 Selections:\n"
        for i, (horse, score) in enumerate(predictions[:3], 1):
            analysis += f"{i}. {horse} (Rating: {score:.1f})\n"
        
        # Confidence levels
        top_score = predictions[0][1]
        if top_score - predictions[1][1] > 10:
            analysis += "\nConfidence: High - Clear top selection"
        elif top_score - predictions[1][1] > 5:
            analysis += "\nConfidence: Medium - Preferred runner but competitive race"
        else:
            analysis += "\nConfidence: Low - Very competitive race"
        
        return analysis

def main():
    """Main function to demonstrate tool usage"""
    tool = RacePredictionTool()
    
    # Use the test date
    date = "2024-10-23"
    
    # Get available meetings
    meetings = tool.get_race_meetings(date)
    
    if meetings:
        print(f"\nAvailable Meetings for {date}:")
        for meeting in meetings:
            print(f"Meeting ID: {meeting['meetingId']} - Venue: {meeting['venueName']}")
        
        # Example analysis for first meeting, first race
        if meetings:
            example_meeting = meetings[0]['meetingId']
            analysis = tool.analyze_race(example_meeting, 1)
            print(f"\nExample Analysis for {meetings[0]['venueName']}:\n")
            print(analysis)
    else:
        print(f"No meetings found for {date}.")

if __name__ == "__main__":
    main()
