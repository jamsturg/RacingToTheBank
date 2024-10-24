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

    def analyze_historical_performance(self, runner: Dict) -> Dict:
        try:
            # Extract performance history
            history = runner.get('performanceHistory', [])
            if not history:
                return {
                    'win_rate': 0,
                    'place_rate': 0,
                    'avg_position': 0,
                    'trend': 'Unknown',
                    'best_distance': 'Unknown',
                    'preferred_condition': 'Unknown'
                }
                
            # Calculate performance metrics
            total_runs = len(history)
            wins = sum(1 for run in history if run.get('position', 0) == 1)
            places = sum(1 for run in history if 1 <= run.get('position', 0) <= 3)
            positions = [run.get('position', 0) for run in history]
            
            # Calculate distance performance
            distance_performance = {}
            for run in history:
                dist = run.get('distance', 0)
                if dist:
                    if dist not in distance_performance:
                        distance_performance[dist] = {'runs': 0, 'wins': 0}
                    distance_performance[dist]['runs'] += 1
                    if run.get('position', 0) == 1:
                        distance_performance[dist]['wins'] += 1
            
            # Find best distance
            best_distance = max(
                distance_performance.items(),
                key=lambda x: x[1]['wins']/x[1]['runs'] if x[1]['runs'] > 0 else 0,
                default=(0, {'runs': 0, 'wins': 0})
            )
            
            # Analyze track condition performance
            condition_performance = {}
            for run in history:
                condition = run.get('trackCondition', 'Unknown')
                if condition not in condition_performance:
                    condition_performance[condition] = {'runs': 0, 'wins': 0}
                condition_performance[condition]['runs'] += 1
                if run.get('position', 0) == 1:
                    condition_performance[condition]['wins'] += 1
                    
            # Find preferred condition
            preferred_condition = max(
                condition_performance.items(),
                key=lambda x: x[1]['wins']/x[1]['runs'] if x[1]['runs'] > 0 else 0,
                default=('Unknown', {'runs': 0, 'wins': 0})
            )
            
            # Calculate trend based on last 5 runs
            recent_positions = positions[-5:]
            trend = 'Stable'
            if len(recent_positions) >= 3:
                if all(x <= y for x, y in zip(recent_positions, recent_positions[1:])):
                    trend = 'Declining'
                elif all(x >= y for x, y in zip(recent_positions, recent_positions[1:])):
                    trend = 'Improving'
            
            return {
                'win_rate': round(wins/total_runs * 100, 2) if total_runs > 0 else 0,
                'place_rate': round(places/total_runs * 100, 2) if total_runs > 0 else 0,
                'avg_position': round(sum(positions)/len(positions), 2) if positions else 0,
                'trend': trend,
                'best_distance': f"{best_distance[0]}m" if best_distance[0] else 'Unknown',
                'preferred_condition': preferred_condition[0]
            }
            
        except Exception as e:
            print(f"Error analyzing historical performance: {str(e)}")
            return {
                'win_rate': 0,
                'place_rate': 0,
                'avg_position': 0,
                'trend': 'Error',
                'best_distance': 'Unknown',
                'preferred_condition': 'Unknown'
            }

    def _validate_form_data(self, form_data: pd.DataFrame) -> pd.DataFrame:
        required_columns = ['Number', 'Horse', 'Barrier', 'Weight', 'Jockey', 'Form', 'Rating', 
                          'win_rate', 'place_rate', 'avg_position', 'trend', 'best_distance', 'preferred_condition']
        
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
                    
                    # Add historical performance
                    historical_data = self.analyze_historical_performance(runner)
                    horse_data.update(historical_data)
                    
                    processed_data.append(horse_data)
                except Exception as e:
                    print(f"Error processing runner: {str(e)}")
                    continue
            
            if processed_data:
                form_data = pd.DataFrame(processed_data)
                form_data = self._validate_form_data(form_data)
            else:
                # Return empty DataFrame with correct structure
                form_data = pd.DataFrame(columns=['Number', 'Horse', 'Barrier', 'Weight', 'Jockey', 'Form', 'Rating',
                                                'win_rate', 'place_rate', 'avg_position', 'trend', 'best_distance', 'preferred_condition'])
            
            return form_data
            
        except Exception as e:
            print(f"Error in prepare_form_guide: {str(e)}")
            # Return empty DataFrame with correct structure
            return pd.DataFrame(columns=['Number', 'Horse', 'Barrier', 'Weight', 'Jockey', 'Form', 'Rating',
                                      'win_rate', 'place_rate', 'avg_position', 'trend', 'best_distance', 'preferred_condition'])

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
