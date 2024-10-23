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
        """Process race data and return a properly formatted DataFrame"""
        # Define column dtypes
        dtypes = {
            'Number': 'str',
            'Horse': 'str',
            'Barrier': 'str',
            'Weight': 'float64',
            'Jockey': 'str',
            'Form': 'str',
            'Rating': 'float64'
        }
        
        try:
            # Extract runners based on data structure
            runners = []
            if isinstance(race_data, dict):
                if 'payLoad' in race_data:
                    payload = race_data['payLoad']
                    if isinstance(payload, dict) and 'runners' in payload:
                        runners = payload['runners']
                    else:
                        runners = [payload] if isinstance(payload, dict) else payload
                elif 'runners' in race_data:
                    runners = race_data['runners']
            elif isinstance(race_data, list):
                runners = race_data
            
            # Process each runner
            form_data = []
            for runner in runners:
                if not isinstance(runner, dict):
                    continue
                
                try:
                    # Extract and convert data with proper type handling
                    horse_data = {
                        'Number': str(runner.get('number', '')),
                        'Horse': str(runner.get('name', '')),
                        'Barrier': str(runner.get('barrier', '')),
                        'Weight': self._extract_weight(runner),
                        'Jockey': self._extract_jockey_name(runner),
                        'Form': self._extract_form(runner),
                        'Rating': float(self.calculate_rating(runner))
                    }
                    
                    # Only add valid entries
                    if horse_data['Horse'] and horse_data['Number']:
                        form_data.append(horse_data)
                except Exception as e:
                    print(f"Error processing runner: {str(e)}")
                    continue
            
            # Create DataFrame with specified dtypes
            df = pd.DataFrame(form_data)
            
            # Ensure all required columns exist with correct types
            for col, dtype in dtypes.items():
                if col not in df.columns:
                    df[col] = pd.Series(dtype=dtype)
                else:
                    df[col] = df[col].astype(dtype)
            
            # Reorder columns to match expected format
            return df[list(dtypes.keys())]
            
        except Exception as e:
            print(f"Error processing race data: {str(e)}")
            # Return empty DataFrame with correct structure
            return pd.DataFrame({col: pd.Series(dtype=dtype) for col, dtype in dtypes.items()})

    def _extract_weight(self, runner: Dict) -> float:
        """Safely extract weight from runner data"""
        try:
            weight = runner.get('weight', runner.get('handicapWeight', 0))
            if isinstance(weight, str):
                # Remove any parenthetical content and convert to float
                weight = float(weight.split('(')[0].strip())
            return float(weight)
        except:
            return 0.0

    def _extract_jockey_name(self, runner: Dict) -> str:
        """Safely extract jockey name from runner data"""
        jockey = runner.get('jockey', {})
        if isinstance(jockey, dict):
            return str(jockey.get('fullName', jockey.get('name', '')))
        return str(jockey) if jockey else ''

    def _extract_form(self, runner: Dict) -> str:
        """Safely extract form data from runner"""
        form = runner.get('form', runner.get('last5Runs', ''))
        if isinstance(form, dict):
            return str(form.get('last5Runs', form.get('lastFive', '')))
        return str(form) if form else ''

    def calculate_rating(self, runner: Dict) -> float:
        """Calculate comprehensive rating for a runner"""
        score = 0
        
        # Form component
        form_score = self.analyze_form(self._extract_form(runner))
        score += form_score * self.weight_factors['form']
        
        # Weight component
        weight = self._extract_weight(runner)
        weight_score = max(0, 15 - (weight - 54) * 2)
        score += weight_score * self.weight_factors['weight']
        
        # Barrier component
        try:
            barrier = int(runner.get('barrier', runner.get('barrierNumber', 10)))
            barrier_score = 10 - abs(barrier - 6)
            score += barrier_score * self.weight_factors['barrier']
        except:
            score += 5 * self.weight_factors['barrier']
        
        # Class/Rating component
        try:
            rating = float(runner.get('rating', runner.get('pfaisRating', 0)))
            class_score = min(20, rating / 5)
            score += class_score * self.weight_factors['class']
        except:
            score += 10 * self.weight_factors['class']
        
        return round(score, 2)

    def analyze_form(self, form_string: str) -> float:
        """Analyze recent form"""
        if not form_string:
            return 0
            
        points = {
            '1': 100, '2': 80, '3': 60, '4': 40, '5': 20,
            '6': 10, '7': 10, '8': 10, '9': 10, '0': 0,
            'W': 100, 'P': 70, 'L': 10, 'x': 0, 'X': 0, '-': 0
        }
        
        total = 0
        count = 0
        weights = [1.5, 1.3, 1.1, 1.0, 0.9]  # More recent results weighted higher
        
        for i, char in enumerate(str(form_string)[:5]):
            if char in points:
                total += points[char] * weights[min(i, len(weights)-1)]
                count += 1
                
        return (total / (count * 1.5)) if count > 0 else 0
