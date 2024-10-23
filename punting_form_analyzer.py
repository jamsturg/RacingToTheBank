import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Tuple

class Config:
    PUNTING_FORM_API_KEY = "YOUR_API_KEY_HERE"  # Replace with your API key

class RacingAnalyzer:
    def __init__(self):
        self.base_url = 'https://api.puntingform.com.au/v2/form'
        self.api_key = Config.PUNTING_FORM_API_KEY
        self.weight_factors = {
            'pfais_score': 0.30,
            'recent_form': 0.25,
            'ratings': 0.20,
            'class': 0.15,
            'barrier': 0.10
        }

    def get_meetings(self, date=None):
        """Get all racing meetings for a date"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
            
        url = f"{self.base_url}/meetingslist"
        params = {
            'meetingDate': date,
            'apiKey': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('payLoad', [])
        except Exception as e:
            print(f"Error fetching meetings: {str(e)}")
            return []

    def get_form_guide(self, meeting_id: str, race_number: int) -> Dict:
        """Get detailed form guide for a race"""
        url = f"{self.base_url}/form"
        params = {
            'meetingId': meeting_id,
            'raceNumber': race_number,
            'apiKey': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json().get('payLoad', {})
        except Exception as e:
            print(f"Error fetching form guide: {str(e)}")
            return {}

    def get_ratings(self, meeting_id: str, race_number: int) -> Dict:
        """Get ratings data for a race"""
        url = f"{self.base_url}/ratings"
        params = {
            'meetingId': meeting_id,
            'raceNumber': race_number,
            'apiKey': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json().get('payLoad', {})
        except Exception as e:
            print(f"Error fetching ratings: {str(e)}")
            return {}

    def analyze_form(self, form_string: str) -> float:
        """Analyze recent form"""
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

    def analyze_race(self, meeting_id: str, race_number: int) -> str:
        """Analyze a specific race"""
        # Get both form guide and ratings
        form_data = self.get_form_guide(meeting_id, race_number)
        ratings_data = self.get_ratings(meeting_id, race_number)
        
        if not form_data or not ratings_data:
            return "Unable to fetch race data"
        
        # Process runners
        predictions = []
        for runner in form_data.get('runners', []):
            horse_name = runner.get('horse', {}).get('name', 'Unknown')
            
            # Get ratings for this horse
            horse_ratings = next(
                (r for r in ratings_data.get('runners', []) 
                 if r.get('horse', {}).get('name') == horse_name), 
                {}
            )
            
            # Calculate scores
            form_score = self.analyze_form(
                runner.get('form', {}).get('last_5', '')
            )
            
            # Get PFAIS score
            pfais_score = float(horse_ratings.get('pfaisScore', 0))
            
            # Get class rating
            class_rating = float(horse_ratings.get('classRating', 0))
            
            # Barrier factor
            barrier = int(runner.get('barrier', '1'))
            barrier_factor = 1 - (abs(barrier - 6) / 20)
            
            # Calculate weighted score
            final_score = (
                pfais_score * self.weight_factors['pfais_score'] +
                form_score * self.weight_factors['recent_form'] +
                class_rating * self.weight_factors['class'] +
                barrier_factor * 100 * self.weight_factors['barrier']
            )
            
            # Add prediction with detailed info
            predictions.append({
                'horse': horse_name,
                'score': final_score,
                'jockey': runner.get('jockey', {}).get('name', 'Unknown'),
                'trainer': runner.get('trainer', {}).get('name', 'Unknown'),
                'weight': runner.get('weight', 'Unknown'),
                'barrier': barrier,
                'form': runner.get('form', {}).get('last_5', ''),
                'pfais': pfais_score,
                'class_rating': class_rating
            })
        
        # Sort predictions
        predictions.sort(key=lambda x: x['score'], reverse=True)
        
        # Generate analysis
        race_info = form_data.get('raceInfo', {})
        analysis = f"Race Analysis: {race_info.get('raceName', '')}\n"
        analysis += f"Track: {race_info.get('track', '')}\n"
        analysis += f"Distance: {race_info.get('distance', '')}m\n"
        analysis += f"Track Condition: {race_info.get('trackCondition', '')}\n\n"
        
        # Top selections with details
        analysis += "Top Selections:\n"
        for i, pred in enumerate(predictions[:3], 1):
            analysis += f"{i}. {pred['horse']}\n"
            analysis += f"   Score: {pred['score']:.1f}\n"
            analysis += f"   Jockey: {pred['jockey']}\n"
            analysis += f"   Weight: {pred['weight']}\n"
            analysis += f"   Barrier: {pred['barrier']}\n"
            analysis += f"   Recent Form: {pred['form']}\n"
            analysis += f"   PFAIS: {pred['pfais']}\n"
            analysis += "\n"
        
        # Confidence level
        if len(predictions) >= 2:
            margin = predictions[0]['score'] - predictions[1]['score']
            analysis += "\nConfidence: "
            if margin > 10:
                analysis += "High - Clear top selection"
            elif margin > 5:
                analysis += "Medium - Preferred runner but competitive race"
            else:
                analysis += "Low - Very competitive race"
            
        return analysis

def main():
    analyzer = RacingAnalyzer()
    
    while True:
        print("\nPunting Form Racing Analyzer")
        print("===========================")
        print("\nOptions:")
        print("1. View today's meetings")
        print("2. Analyze race")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == '1':
            meetings = analyzer.get_meetings()
            print("\nAvailable Meetings:")
            for i, meeting in enumerate(meetings, 1):
                print(f"{i}. {meeting['meetingName']} ({meeting['meetingId']})")
                
        elif choice == '2':
            meetings = analyzer.get_meetings()
            print("\nAvailable Meetings:")
            for i, meeting in enumerate(meetings, 1):
                print(f"{i}. {meeting['meetingName']} ({meeting['meetingId']})")
                
            try:
                meeting_index = int(input("\nSelect meeting number: ")) - 1
                race_number = int(input("Enter race number: "))
                
                if 0 <= meeting_index < len(meetings):
                    meeting_id = meetings[meeting_index]['meetingId']
                    analysis = analyzer.analyze_race(meeting_id, race_number)
                    print(f"\n{analysis}")
                else:
                    print("Invalid meeting number")
            except ValueError:
                print("Invalid input. Please enter numbers only.")
                
        elif choice == '3':
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()