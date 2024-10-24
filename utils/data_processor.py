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

    def calculate_rating(self, runner: Dict) -> float:
        try:
            # Calculate base rating from PFAIS score
            pfais_score = float(runner.get('pfaisScore', runner.get('rating', {}).get('pfais', 0)))
            
            # Get form factor
            form = self._extract_form(runner)
            form_factor = sum(1 for char in form if char.isdigit() and int(char) <= 3) / max(len(form), 1)
            
            # Get weight factor
            weight = float(self._extract_weight(runner))
            weight_factor = 1 - ((weight - 54) / 10) if weight > 54 else 1
            
            # Calculate weighted rating
            rating = (
                pfais_score * 0.6 +
                form_factor * 30 +
                weight_factor * 10
            )
            
            return round(rating, 2)
        except Exception as e:
            print(f"Error calculating rating: {str(e)}")
            return 0.0

    def analyze_historical_performance(self, runner: Dict) -> Dict:
        try:
            # Extract historical performance data
            history = runner.get('performance_history', [])
            if not history and 'history' in runner:
                history = runner['history']
                
            # Default return values
            historical_data = {
                'win_rate': 0.0,
                'place_rate': 0.0,
                'trend': 'Stable',
                'best_distance': '',
                'preferred_condition': 'Unknown'
            }
            
            if not history:
                return historical_data
                
            # Calculate win and place rates
            total_runs = len(history)
            if total_runs > 0:
                wins = sum(1 for run in history if run.get('position') == 1)
                places = sum(1 for run in history if run.get('position') in [2, 3])
                historical_data['win_rate'] = round((wins / total_runs) * 100, 1)
                historical_data['place_rate'] = round((places / total_runs) * 100, 1)
            
            # Analyze performance trend
            if len(history) >= 3:
                recent_positions = [float(run.get('position', 99)) for run in history[:3]]
                if all(pos < 4 for pos in recent_positions):
                    historical_data['trend'] = 'Improving'
                elif all(pos > 6 for pos in recent_positions):
                    historical_data['trend'] = 'Declining'
            
            # Find best distance and preferred condition
            if len(history) >= 5:
                distance_perf = {}
                condition_perf = {}
                
                for run in history:
                    dist = str(run.get('distance', '0'))
                    cond = str(run.get('track_condition', 'Unknown'))
                    pos = float(run.get('position', 99))
                    
                    if dist not in distance_perf:
                        distance_perf[dist] = []
                    if cond not in condition_perf:
                        condition_perf[cond] = []
                        
                    distance_perf[dist].append(pos)
                    condition_perf[cond].append(pos)
                
                # Find best distance
                best_dist = min(distance_perf.items(), 
                              key=lambda x: sum(x[1])/len(x[1]), 
                              default=('', []))
                if best_dist[0]:
                    historical_data['best_distance'] = best_dist[0]
                
                # Find preferred condition
                best_cond = min(condition_perf.items(),
                              key=lambda x: sum(x[1])/len(x[1]),
                              default=('', []))
                if best_cond[0] != 'Unknown':
                    historical_data['preferred_condition'] = best_cond[0]
            
            return historical_data
            
        except Exception as e:
            print(f"Error analyzing historical performance: {str(e)}")
            return {
                'win_rate': 0.0,
                'place_rate': 0.0,
                'trend': 'Unknown',
                'best_distance': '',
                'preferred_condition': 'Unknown'
            }

    def _extract_weight(self, runner: Dict) -> str:
        try:
            weight = runner.get('Weight', runner.get('weight', ''))
            if isinstance(weight, (int, float)):
                return str(weight)
            if isinstance(weight, str) and weight:
                # Handle weight with penalties like "58.5 (+2)"
                base_weight = weight.split('(')[0].strip()
                try:
                    return str(float(base_weight))
                except ValueError:
                    return '0'
            return '0'
        except Exception as e:
            print(f"Error extracting weight: {str(e)}")
            return '0'

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
                
            # Process each runner with error handling
            processed_data = []
            for runner in runners:
                if not isinstance(runner, dict):
                    continue
                    
                try:
                    horse_data = {
                        'Number': str(runner.get('number', '')),
                        'Horse': str(runner.get('name', '')),
                        'Barrier': str(runner.get('barrier', '')),
                        'Weight': self._extract_weight(runner),
                        'Jockey': self._extract_jockey_name(runner),
                        'Form': self._extract_form(runner),
                        'Rating': float(self.calculate_rating(runner)),
                        'pfais_score': float(runner.get('pfaisScore', runner.get('rating', {}).get('pfais', 0))),
                        'confidence': 'Medium',  # Default confidence level
                        'trend': 'Stable',  # Default trend
                        'win_rate': 0.0,  # Default win rate
                        'place_rate': 0.0  # Default place rate
                    }
                    
                    # Add historical performance with error handling
                    try:
                        historical_data = self.analyze_historical_performance(runner)
                        horse_data.update(historical_data)
                    except Exception as e:
                        print(f"Error processing historical data: {str(e)}")
                    
                    processed_data.append(horse_data)
                except Exception as e:
                    print(f"Error processing runner: {str(e)}")
                    continue
            
            if processed_data:
                form_data = pd.DataFrame(processed_data)
                return self._validate_form_data(form_data)
            else:
                # Return empty DataFrame with correct structure
                return pd.DataFrame(columns=['Number', 'Horse', 'Barrier', 'Weight', 'Jockey', 'Form', 'Rating',
                                         'pfais_score', 'confidence', 'trend', 'win_rate', 'place_rate'])
            
        except Exception as e:
            print(f"Error in prepare_form_guide: {str(e)}")
            return pd.DataFrame()

    def _validate_form_data(self, form_data: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean form data"""
        try:
            required_columns = [
                'Number', 'Horse', 'Barrier', 'Weight', 'Jockey', 'Form', 'Rating',
                'pfais_score', 'confidence', 'trend', 'win_rate', 'place_rate'
            ]
            
            # Add missing columns with default values
            for col in required_columns:
                if col not in form_data.columns:
                    form_data[col] = '' if col in ['Number', 'Horse', 'Barrier', 'Jockey', 'Form'] else 0.0
            
            # Convert numeric columns
            numeric_columns = ['Weight', 'Rating', 'pfais_score', 'win_rate', 'place_rate']
            for col in numeric_columns:
                form_data[col] = pd.to_numeric(form_data[col], errors='coerce').fillna(0)
            
            # Ensure string columns are strings
            string_columns = ['Number', 'Horse', 'Barrier', 'Jockey', 'Form']
            for col in string_columns:
                form_data[col] = form_data[col].astype(str)
            
            return form_data[required_columns]
            
        except Exception as e:
            print(f"Error validating form data: {str(e)}")
            return form_data

    def _extract_jockey_name(self, runner: Dict) -> str:
        """Extract jockey name with error handling"""
        try:
            if 'jockey' in runner:
                jockey = runner['jockey']
                if isinstance(jockey, dict):
                    return jockey.get('name', jockey.get('fullName', 'Unknown'))
                return str(jockey)
            return 'Unknown'
        except Exception as e:
            print(f"Error extracting jockey name: {str(e)}")
            return 'Unknown'

    def _extract_form(self, runner: Dict) -> str:
        """Extract form data with error handling"""
        try:
            if 'form' in runner:
                form = runner['form']
                if isinstance(form, dict):
                    return form.get('last_5', '')
                return str(form)
            return ''
        except Exception as e:
            print(f"Error extracting form: {str(e)}")
            return ''
