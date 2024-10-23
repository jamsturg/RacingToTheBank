import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

class RaceDataProcessor:
    def __init__(self):
        self.weight_factors = {
            'form': 0.25,
            'class': 0.20,
            'weight': 0.15,
            'barrier': 0.15,
            'jockey': 0.15,
            'track_condition': 0.10
        }

    def prepare_form_guide(self, race_data) -> pd.DataFrame:
        # Initialize empty form data list
        form_data = []
        
        try:
            # Handle both list and dictionary response formats
            runners = []
            if isinstance(race_data, dict) and 'payLoad' in race_data:
                race_payload = race_data['payLoad']
                if isinstance(race_payload, dict):
                    runners = race_payload.get('runners', [])
                else:
                    runners = race_payload if isinstance(race_payload, list) else []
            
            # Process each runner
            for runner in runners:
                if not isinstance(runner, dict):
                    continue
                    
                try:
                    # Extract horse data safely
                    horse_data = {
                        'Number': runner.get('number', ''),
                        'Horse': runner.get('name', ''),
                        'Barrier': runner.get('barrier', ''),
                        'Weight': float(runner.get('weight', 0)),
                        'Jockey': runner.get('jockey', {}).get('fullName', ''),
                        'Form': runner.get('form', ''),
                        'Rating': self.calculate_rating(runner)
                    }
                    form_data.append(horse_data)
                except Exception as e:
                    print(f"Error processing runner: {str(e)}")
                    continue
                    
            return pd.DataFrame(form_data)
        except Exception as e:
            print(f"Error processing race data: {str(e)}")
            return pd.DataFrame(columns=['Number', 'Horse', 'Barrier', 'Weight', 'Jockey', 'Form', 'Rating'])

    def calculate_rating(self, runner: Dict) -> float:
        """Calculate comprehensive rating for a runner"""
        score = 0
        
        # Form component
        form_string = runner.get('form', '')
        form_score = self.analyze_form(form_string)
        score += form_score * self.weight_factors['form']
        
        # Weight component
        weight = float(runner.get('weight', 58))
        weight_score = max(0, 15 - (weight - 54) * 2)
        score += weight_score * self.weight_factors['weight']
        
        # Barrier component
        try:
            barrier = int(runner.get('barrier', 10))
            barrier_score = 10 - abs(barrier - 6)
            score += barrier_score * self.weight_factors['barrier']
        except:
            score += 5 * self.weight_factors['barrier']
        
        return round(score, 2)

    def analyze_form(self, form_string: str) -> float:
        """Analyze recent form"""
        if not form_string:
            return 0
            
        points = {
            '1': 100, '2': 80, '3': 60, '4': 40, '5': 20,
            '6': 10, '7': 10, '8': 10, '9': 10, '0': 0
        }
        
        total = 0
        count = 0
        
        for char in form_string[:5]:
            if char in points:
                total += points[char]
                count += 1
                
        return (total / count) if count > 0 else 0
