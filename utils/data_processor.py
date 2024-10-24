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

    def _validate_form_data(self, form_data: pd.DataFrame) -> pd.DataFrame:
        required_columns = ['Number', 'Horse', 'Barrier', 'Weight', 'Jockey', 'Form', 'Rating']
        
        # Check for missing columns
        missing_columns = set(required_columns) - set(form_data.columns)
        if missing_columns:
            # Add missing columns with default values
            for col in missing_columns:
                form_data[col] = ''
        
        # Ensure correct data types
        try:
            form_data['Number'] = form_data['Number'].astype(str)
            form_data['Horse'] = form_data['Horse'].astype(str)
            form_data['Barrier'] = form_data['Barrier'].astype(str)
            form_data['Weight'] = pd.to_numeric(form_data['Weight'], errors='coerce').fillna(0)
            form_data['Jockey'] = form_data['Jockey'].astype(str)
            form_data['Form'] = form_data['Form'].astype(str)
            form_data['Rating'] = pd.to_numeric(form_data['Rating'], errors='coerce').fillna(0)
        except Exception as e:
            print(f"Error converting data types: {str(e)}")
        
        # Reorder columns to match required order
        return form_data[required_columns]

    def prepare_form_guide(self, race_data) -> pd.DataFrame:
        try:
            # Extract runners based on data structure
            runners = []
            if isinstance(race_data, dict) and 'payLoad' in race_data:
                payload = race_data['payLoad']
                if isinstance(payload, dict) and 'runners' in payload:
                    runners = payload['runners']
                elif isinstance(payload, list):
                    runners = payload
            elif isinstance(race_data, list):
                runners = race_data
                
            # Process each runner
            processed_data = []
            for runner in runners:
                if not isinstance(runner, dict):
                    continue
                    
                try:
                    # Extract data with proper error handling
                    horse_data = {
                        'Number': str(runner.get('number', '')),
                        'Horse': str(runner.get('name', '')),
                        'Barrier': str(runner.get('barrier', '')),
                        'Weight': self._extract_weight(runner),
                        'Jockey': self._extract_jockey_name(runner),
                        'Form': self._extract_form(runner),
                        'Rating': float(self.calculate_rating(runner))
                    }
                    processed_data.append(horse_data)
                except Exception as e:
                    print(f"Error processing runner: {str(e)}")
                    continue
            
            if processed_data:
                form_data = pd.DataFrame(processed_data)
                form_data = self._validate_form_data(form_data)
            else:
                # Return empty DataFrame with correct structure
                form_data = pd.DataFrame(columns=['Number', 'Horse', 'Barrier', 'Weight', 'Jockey', 'Form', 'Rating'])
            
            return form_data
            
        except Exception as e:
            print(f"Error in prepare_form_guide: {str(e)}")
            # Return empty DataFrame with correct structure
            return pd.DataFrame(columns=['Number', 'Horse', 'Barrier', 'Weight', 'Jockey', 'Form', 'Rating'])

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
            return jockey.get('fullName', jockey.get('name', ''))
        return str(jockey) if jockey else ''

    def _extract_form(self, runner: Dict) -> str:
        """Safely extract form data from runner"""
        form = runner.get('form', runner.get('last5Runs', ''))
        if isinstance(form, dict):
            return form.get('last5Runs', form.get('lastFive', ''))
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
