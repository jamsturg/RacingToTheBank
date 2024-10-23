import os
import json
import requests
from datetime import datetime
import logging
from typing import List, Dict, Tuple
import pandas as pd
import numpy as np

class RacePredictionTool:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
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
            response = requests.get(f"https://api.racingcom.com.au/v3/meetings?date={date}")
            response.raise_for_status()
            meetings = response.json()
            self.logger.info(f"Retrieved {len(meetings)} meetings")
            return meetings
        except Exception as e:
            self.logger.error(f"Error fetching meetings: {str(e)}")
            return []

    def get_race_data(self, meeting_key: str, date: str = None) -> Dict:
        """Fetch detailed race data for a specific meeting"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
            
        self.logger.info(f"Fetching race data for meeting {meeting_key} on {date}")
        
        try:
            response = requests.get(
                f"https://api.racingcom.com.au/v3/meetings/{meeting_key}/ratings?date={date}"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching race data: {str(e)}")
            return {"error": str(e)}

    def parse_horse_data(self, race_data: Dict) -> List[Dict]:
        """Parse raw race data into structured format for analysis"""
        horses = []
        
        try:
            for runner in race_data.get('runners', []):
                horse = {
                    'Horse': runner.get('horse_name'),
                    'PFAIS': runner.get('rating', {}).get('pfais', '0'),
                    'Wt': runner.get('weight', '0'),
                    'Bar': runner.get('barrier', '0'),
                    'last_5': runner.get('form', {}).get('last_5', ''),
                    'Distance': runner.get('stats', {}).get('distance_record', '0: 0-0-0'),
                    'Track': runner.get('stats', {}).get('track_record', '0: 0-0-0'),
                    'Jockey': runner.get('jockey', {}).get('name', ''),
                    'Trainer': runner.get('trainer', {}).get('name', '')
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

    def predict_race(self, meeting_key: str, race_number: int, date: str = None) -> List[Tuple[str, float]]:
        """Generate predictions for a specific race"""
        try:
            # Fetch race data
            race_data = self.get_race_data(meeting_key, date)
            
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

    def analyze_race(self, meeting_key: str, race_number: int, date: str = None) -> str:
        """Provide comprehensive race analysis with predictions"""
        predictions = self.predict_race(meeting_key, race_number, date)
        
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
    
    # Get today's date
    date = datetime.now().strftime("%Y-%m-%d")
    
    # Get available meetings
    meetings = tool.get_race_meetings(date)
    
    if meetings:
        print("\nAvailable Meetings:")
        for meeting in meetings:
            print(f"Meeting Key: {meeting['Key']} - Venue: {meeting['Value']}")
        
        # Example analysis for first meeting, first race
        if meetings:
            example_meeting = meetings[0]['Key']
            analysis = tool.analyze_race(example_meeting, 1, date)
            print(f"\nExample Analysis for {meetings[0]['Value']}:\n")
            print(analysis)
    else:
        print("No meetings found for today.")

if __name__ == "__main__":
    main()