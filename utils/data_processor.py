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

    def analyze_race_type(self, race_info: Dict) -> Dict:
        """Analyze race type and class based on prize money"""
        try:
            prize_money = float(race_info.get('prizeMoney', 0))
            race_type = race_info.get('raceType', '').lower()
            
            race_class = ('Group 1' if prize_money > 750000 else
                         'Group 2' if prize_money > 250000 else
                         'Group 3' if prize_money > 150000 else
                         'Listed' if prize_money > 100000 else 'Other')
            
            return {
                'class': race_class,
                'type': race_type,
                'prize_tier': 'High' if prize_money > 500000 else 'Medium' if prize_money > 100000 else 'Low'
            }
        except Exception as e:
            print(f"Error analyzing race type: {str(e)}")
            return {'class': 'Unknown', 'type': 'Unknown', 'prize_tier': 'Unknown'}

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
                        'Rating': float(self.calculate_rating(runner)),
                        'pfais_score': float(runner.get('pfaisScore', runner.get('rating', {}).get('pfais', 0))),
                        'confidence': 'Medium',  # Default confidence level
                        'trend': 'Stable'  # Default trend
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
                return self._validate_form_data(form_data)
            else:
                # Return empty DataFrame with correct structure
                return pd.DataFrame(columns=['Number', 'Horse', 'Barrier', 'Weight', 'Jockey', 'Form', 'Rating',
                                          'pfais_score', 'confidence', 'trend', 'win_rate', 'place_rate'])
            
        except Exception as e:
            print(f"Error in prepare_form_guide: {str(e)}")
            return pd.DataFrame(columns=['Number', 'Horse', 'Barrier', 'Weight', 'Jockey', 'Form', 'Rating',
                                      'pfais_score', 'confidence', 'trend', 'win_rate', 'place_rate'])

    def _validate_form_data(self, form_data: pd.DataFrame) -> pd.DataFrame:
        required_columns = ['Number', 'Horse', 'Barrier', 'Weight', 'Jockey', 'Form', 'Rating', 
                          'pfais_score', 'confidence', 'trend', 'win_rate', 'place_rate']
        
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
            form_data['pfais_score'] = pd.to_numeric(form_data['pfais_score'], errors='coerce').fillna(0)
        except Exception as e:
            print(f"Error converting data types: {str(e)}")
        
        # Reorder columns to match required order
        return form_data[required_columns]

    # ... [rest of the existing methods remain unchanged]
