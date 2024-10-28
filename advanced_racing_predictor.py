import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
import xgboost as xgb
from dataclasses import dataclass
import joblib
from pathlib import Path
import json
from .utils.logger import get_logger

@dataclass
class RaceConditions:
    """Stores race conditions and track information"""
    track_condition: str
    weather: str
    temperature: float
    humidity: float
    wind_speed: float
    wind_direction: str
    rail_position: str
    track_bias: Dict[str, float]

@dataclass
class RunnerForm:
    """Stores comprehensive runner form data"""
    recent_positions: List[int]
    win_rate: float
    place_rate: float
    track_win_rate: float
    distance_win_rate: float
    class_win_rate: float
    jockey_win_rate: float
    trainer_win_rate: float
    weight_carried: float
    barrier: int
    speed_ratings: List[float]
    sectional_times: List[float]
    career_earnings: float
    days_since_last_run: int

@dataclass
class PredictionResult:
    """Stores comprehensive prediction results"""
    probability: float
    confidence: str
    predicted_position: int
    win_probability: float
    place_probability: float
    value_rating: float
    speed_rating: float
    form_rating: float
    class_rating: float
    overall_rating: float
    model_contributions: Dict[str, float]
    feature_importance: Dict[str, float]

class AdvancedRacingPredictor:
    """Advanced racing prediction system with multiple models and features"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.api_key = '7552b21e-851b-4803-b230-d1637a74f05c'
        self.base_url = 'https://api.puntingform.com.au/v2/form'
        
        # Initialize models
        self.models = self._initialize_models()
        self.scaler = StandardScaler()
        self.feature_names = self._get_feature_names()
        
        # Load pre-trained models if available
        self._load_models()

    def _initialize_models(self) -> Dict:
        """Initialize prediction models"""
        return {
            'rf': RandomForestClassifier(
                n_estimators=200,
                max_depth=10,
                min_samples_split=5,
                random_state=42,
                class_weight='balanced'
            ),
            'gb': GradientBoostingClassifier(
                n_estimators=200,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            ),
            'xgb': xgb.XGBClassifier(
                n_estimators=200,
                learning_rate=0.1,
                max_depth=6,
                random_state=42,
                use_label_encoder=False,
                eval_metric='logloss'
            )
        }

    def _get_feature_names(self) -> List[str]:
        """Get comprehensive list of features"""
        return [
            # Form features
            'last_start_position', 'second_last_position', 'third_last_position',
            'win_rate', 'place_rate', 'career_wins', 'career_places',
            'prize_money_total', 'prize_money_avg',
            
            # Track and distance features
            'track_win_rate', 'track_place_rate', 'distance_win_rate',
            'track_condition_rating', 'barrier_advantage', 'track_bias_rating',
            
            # Class and ratings features
            'class_rating', 'speed_rating_last', 'speed_rating_avg',
            'class_win_rate', 'weight_rating', 'weight_advantage',
            
            # Jockey and trainer features
            'jockey_win_rate', 'jockey_track_win_rate', 'jockey_class_win_rate',
            'trainer_win_rate', 'trainer_track_win_rate', 'trainer_class_win_rate',
            
            # Time and momentum features
            'days_since_last_run', 'career_starts', 'winning_momentum',
            'seasonal_performance', 'time_of_day_performance',
            
            # Advanced features
            'sectional_time_rating', 'acceleration_rating', 'stamina_rating',
            'recovery_rating', 'consistency_rating', 'versatility_rating',
            'competitive_rating', 'pressure_performance', 'track_position_rating'
        ]

    def _load_models(self):
        """Load pre-trained models if available"""
        try:
            model_dir = Path('models')
            if model_dir.exists():
                for name, model in self.models.items():
                    model_path = model_dir / f'{name}_model.joblib'
                    if model_path.exists():
                        self.models[name] = joblib.load(model_path)
                        self.logger.info(f"Loaded pre-trained model: {name}")
                
                scaler_path = model_dir / 'scaler.joblib'
                if scaler_path.exists():
                    self.scaler = joblib.load(scaler_path)
                    self.logger.info("Loaded pre-trained scaler")
        except Exception as e:
            self.logger.error(f"Error loading models: {str(e)}")

    def save_models(self):
        """Save trained models"""
        try:
            model_dir = Path('models')
            model_dir.mkdir(exist_ok=True)
            
            for name, model in self.models.items():
                model_path = model_dir / f'{name}_model.joblib'
                joblib.dump(model, model_path)
            
            scaler_path = model_dir / 'scaler.joblib'
            joblib.dump(self.scaler, scaler_path)
            
            self.logger.info("Models saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving models: {str(e)}")

    def get_race_data(self, meeting_id: str, race_number: int) -> Optional[Dict]:
        """Get enhanced race data from API"""
        try:
            url = f"{self.base_url}/form"
            params = {
                'meetingId': meeting_id,
                'raceNumber': race_number,
                'apiKey': self.api_key
            }
            response = requests.get(url, params=params)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            self.logger.error(f"Error getting race data: {str(e)}")
            return None

    def analyze_form(self, runner: Dict) -> RunnerForm:
        """Analyze comprehensive form data"""
        try:
            # Extract recent form
            form_string = runner.get('form', '')
            recent_positions = []
            for char in form_string:
                if char.isdigit():
                    recent_positions.append(int(char))
                elif char.upper() == 'W':
                    recent_positions.append(1)
            
            # Calculate performance rates
            history = runner.get('history', [])
            total_runs = len(history)
            if total_runs == 0:
                return self._get_default_form()
            
            wins = sum(1 for run in history if run.get('position') == 1)
            places = sum(1 for run in history if run.get('position', 0) <= 3)
            
            # Calculate specialized win rates
            track_wins = sum(1 for run in history 
                           if run.get('position') == 1 and 
                           run.get('track') == runner.get('track'))
            track_runs = sum(1 for run in history 
                           if run.get('track') == runner.get('track'))
            
            distance_wins = sum(1 for run in history 
                              if run.get('position') == 1 and 
                              abs(run.get('distance', 0) - 
                                  runner.get('distance', 0)) <= 100)
            distance_runs = sum(1 for run in history 
                              if abs(run.get('distance', 0) - 
                                   runner.get('distance', 0)) <= 100)
            
            class_wins = sum(1 for run in history 
                           if run.get('position') == 1 and 
                           run.get('class') == runner.get('class'))
            class_runs = sum(1 for run in history 
                           if run.get('class') == runner.get('class'))
            
            # Get speed ratings and sectional times
            speed_ratings = [
                float(run.get('speed_rating', 0)) 
                for run in history 
                if run.get('speed_rating')
            ]
            
            sectional_times = [
                float(run.get('sectional_time', 0)) 
                for run in history 
                if run.get('sectional_time')
            ]
            
            return RunnerForm(
                recent_positions=recent_positions,
                win_rate=wins / total_runs * 100,
                place_rate=places / total_runs * 100,
                track_win_rate=track_wins / max(track_runs, 1) * 100,
                distance_win_rate=distance_wins / max(distance_runs, 1) * 100,
                class_win_rate=class_wins / max(class_runs, 1) * 100,
                jockey_win_rate=float(runner.get('jockey', {}).get('win_rate', 0)),
                trainer_win_rate=float(runner.get('trainer', {}).get('win_rate', 0)),
                weight_carried=float(runner.get('weight', 0)),
                barrier=int(runner.get('barrier', 0)),
                speed_ratings=speed_ratings,
                sectional_times=sectional_times,
                career_earnings=float(runner.get('career_earnings', 0)),
                days_since_last_run=self._calculate_days_since_last_run(history)
            )
        except Exception as e:
            self.logger.error(f"Error analyzing form: {str(e)}")
            return self._get_default_form()

    def _get_default_form(self) -> RunnerForm:
        """Get default form data"""
        return RunnerForm(
            recent_positions=[],
            win_rate=0.0,
            place_rate=0.0,
            track_win_rate=0.0,
            distance_win_rate=0.0,
            class_win_rate=0.0,
            jockey_win_rate=0.0,
            trainer_win_rate=0.0,
            weight_carried=0.0,
            barrier=0,
            speed_ratings=[],
            sectional_times=[],
            career_earnings=0.0,
            days_since_last_run=0
        )

    def _calculate_days_since_last_run(self, history: List[Dict]) -> int:
        """Calculate days since last run"""
        try:
            if not history:
                return 0
            last_run = history[0]
            last_date = datetime.fromisoformat(last_run['date'])
            return (datetime.now() - last_date).days
        except Exception as e:
            self.logger.error(f"Error calculating days since last run: {str(e)}")
            return 0

    def _analyze_race_shape(self, runner_analysis: List[Dict]) -> Dict[str, Any]:
        """Analyze expected race shape and dynamics"""
        try:
            # Count running styles
            styles = {
                'leader': 0,
                'stalker': 0,
                'midfield': 0,
                'backmarker': 0
            }
            
            for runner in runner_analysis:
                style = runner.get('running_style', 'midfield')
                styles[style] += 1
            
            # Determine pace scenario
            leaders = styles['leader']
            stalkers = styles['stalker']
            
            if leaders >= 3:
                pace = 'Strong'
                beneficiaries = 'Backmarkers'
            elif leaders == 0:
                pace = 'Slow'
                beneficiaries = 'Leaders'
            elif leaders + stalkers >= 4:
                pace = 'Moderate to Strong'
                beneficiaries = 'Off-pace runners'
            else:
                pace = 'Moderate'
                beneficiaries = 'Versatile runners'
            
            return {
                'pace_scenario': pace,
                'likely_beneficiaries': beneficiaries,
                'running_styles': styles,
                'pressure_points': self._identify_pressure_points(styles),
                'tactical_advantages': self._analyze_tactical_advantages(
                    runner_analysis, pace
                )
            }
        except Exception as e:
            self.logger.error(f"Error analyzing race shape: {str(e)}")
            return {
                'pace_scenario': 'Unknown',
                'likely_beneficiaries': 'Unknown',
                'running_styles': styles,
                'pressure_points': [],
                'tactical_advantages': {}
            }

    def _identify_pressure_points(self, styles: Dict[str, int]) -> List[str]:
        """Identify potential pressure points in the race"""
        pressure_points = []
        
        if styles['leader'] >= 2:
            pressure_points.append('Early speed battle likely')
        if styles['stalker'] >= 3:
            pressure_points.append('Mid-race pressure expected')
        if styles['backmarker'] >= 4:
            pressure_points.append('Traffic issues possible for backmarkers')
            
        return pressure_points

    def _analyze_tactical_advantages(
        self,
        runner_analysis: List[Dict],
        pace_scenario: str
    ) -> Dict[str, List[str]]:
        """Analyze tactical advantages based on pace scenario"""
        advantages = {}
        
        for runner in runner_analysis:
            runner_name = runner['name']
            style = runner.get('running_style', 'midfield')
            barrier = runner.get('barrier', 0)
            
            runner_advantages = []
            
            if pace_scenario == 'Strong' and style == 'backmarker':
                runner_advantages.append('Will benefit from strong pace')
            elif pace_scenario == 'Slow' and style == 'leader':
                runner_advantages.append('Can control moderate pace')
                
            if 1 <= barrier <= 4:
                runner_advantages.append('Good barrier draw')
            elif barrier >= 12:
                runner_advantages.append('Wide draw may provide clear running')
                
            if runner_advantages:
                advantages[runner_name] = runner_advantages
                
        return advantages

    def _analyze_pace(self, runner_analysis: List[Dict]) -> Dict[str, Any]:
        """Analyze expected pace and sectional times"""
        try:
            # Group runners by running style
            pace_groups = {
                'early_speed': [],
                'mid_pack': [],
                'backmarkers': []
            }
            
            for runner in runner_analysis:
                barrier = int(runner.get('barrier', 0))
                if barrier <= 4:
                    pace_groups['early_speed'].append(runner)
                elif barrier <= 8:
                    pace_groups['mid_pack'].append(runner)
                else:
                    pace_groups['backmarkers'].append(runner)
            
            # Analyze pace pressure
            early_speed_runners = len(pace_groups['early_speed'])
            pace_pressure = 'High' if early_speed_runners >= 3 else \
                          'Moderate' if early_speed_runners == 2 else 'Low'
            
            return {
                'pace_pressure': pace_pressure,
                'early_speed_runners': [r['name'] for r in pace_groups['early_speed']],
                'mid_pack_runners': [r['name'] for r in pace_groups['mid_pack']],
                'backmarkers': [r['name'] for r in pace_groups['backmarkers']],
                'likely_scenario': self._predict_pace_scenario(pace_groups)
            }
        except Exception as e:
            self.logger.error(f"Error analyzing pace: {str(e)}")
            return {
                'pace_pressure': 'Unknown',
                'early_speed_runners': [],
                'mid_pack_runners': [],
                'backmarkers': [],
                'likely_scenario': 'Unknown'
            }

    def _predict_pace_scenario(self, pace_groups: Dict[str, List[Dict]]) -> str:
        """Predict likely pace scenario"""
        early_speed = len(pace_groups['early_speed'])
        mid_pack = len(pace_groups['mid_pack'])
        backmarkers = len(pace_groups['backmarkers'])
        
        if early_speed >= 3:
            return "Fast pace likely with multiple leaders"
        elif early_speed == 0:
            return "Slow pace likely with no clear leaders"
        elif early_speed == 1 and mid_pack >= 3:
            return "Moderate pace with one leader and strong mid-pack presence"
        elif backmarkers >= 4:
            return "Potentially muddling pace with traffic issues"
        else:
            return "Moderate, evenly distributed pace expected"

    def _identify_value_bets(self, runner_analysis: List[Dict]) -> List[Dict]:
        """Identify potential value betting opportunities"""
        try:
            value_bets = []
            
            for runner in runner_analysis:
                predicted_prob = runner['prediction']['win_probability']
                actual_odds = runner['odds']
                
                if actual_odds <= 1.0:
                    continue
                
                # Convert odds to probability
                market_prob = 1 / actual_odds
                
                # Calculate overlay percentage
                overlay = (predicted_prob - market_prob) / market_prob * 100
                
                if overlay > 20:  # Significant overlay
                    value_bets.append({
                        'runner': runner['name'],
                        'predicted_probability': predicted_prob,
                        'actual_odds': actual_odds,
                        'overlay_percentage': overlay,
                        'confidence': runner['prediction']['confidence'],
                        'bet_rating': self._calculate_bet_rating(
                            overlay,
                            runner['prediction']['confidence'],
                            predicted_prob
                        )
                    })
            
            # Sort by bet rating
            value_bets.sort(key=lambda x: x['bet_rating'], reverse=True)
            return value_bets
            
        except Exception as e:
            self.logger.error(f"Error identifying value bets: {str(e)}")
            return []

    def _calculate_bet_rating(
        self,
        overlay: float,
        confidence: str,
        probability: float
    ) -> float:
        """Calculate overall betting rating"""
        try:
            # Convert confidence to numerical value
            confidence_value = {
                'High': 1.0,
                'Medium': 0.7,
                'Low': 0.4
            }.get(confidence, 0.4)
            
            # Weight factors
            overlay_weight = 0.4
            confidence_weight = 0.3
            probability_weight = 0.3
            
            # Normalize overlay to 0-1 scale
            normalized_overlay = min(overlay / 50, 1.0)
            
            # Calculate weighted score
            rating = (
                overlay_weight * normalized_overlay +
                confidence_weight * confidence_value +
                probability_weight * probability
            ) * 100
            
            return round(rating, 1)
            
        except Exception as e:
            self.logger.error(f"Error calculating bet rating: {str(e)}")
            return 0.0

    def format_analysis(self, analysis: Dict) -> str:
        """Format analysis into readable report"""
        try:
            lines = [
                "RACE ANALYSIS REPORT",
                "===================",
                "",
                "TOP SELECTIONS:",
                "--------------"
            ]
            
            # Add selections
            for i, runner in enumerate(analysis['runners'][:3], 1):
                lines.extend([
                    f"{i}. {runner['name'].upper()}",
                    f"   Win Probability: {runner['prediction']['win_probability']:.1f}%",
                    f"   Confidence: {runner['prediction']['confidence']}",
                    f"   Value Rating: {runner['prediction']['value_rating']:.1f}",
                    ""
                ])
            
            # Add pace analysis
            lines.extend([
                "PACE ANALYSIS:",
                "--------------",
                f"Scenario: {analysis['race_shape_analysis']['pace_scenario']}",
                f"Likely Beneficiaries: {analysis['race_shape_analysis']['likely_beneficiaries']}",
                ""
            ])
            
            # Add pressure points
            if analysis['race_shape_analysis']['pressure_points']:
                lines.extend([
                    "PRESSURE POINTS:",
                    "---------------"
                ])
                for point in analysis['race_shape_analysis']['pressure_points']:
                    lines.append(f"- {point}")
                lines.append("")
            
            # Add betting suggestions
            if analysis['betting_suggestions']:
                lines.extend([
                    "BETTING SUGGESTIONS:",
                    "-------------------"
                ])
                for bet in analysis['betting_suggestions']:
                    lines.extend([
                        f"{bet['bet_type']}: {bet['runner']} ({bet['stake']})",
                        f"Confidence: {bet['confidence']}",
                        "Reasoning:"
                    ])
                    for reason in bet['reasoning']:
                        lines.append(f"- {reason}")
                    lines.append("")
            
            # Add value opportunities
            if analysis['value_opportunities']:
                lines.extend([
                    "VALUE OPPORTUNITIES:",
                    "------------------"
                ])
                for value in analysis['value_opportunities']:
                    lines.extend([
                        f"{value['runner']}",
                        f"Overlay: {value['overlay_percentage']:.1f}%",
                        f"Bet Rating: {value['bet_rating']}/100",
                        ""
                    ])
            
            return "\n".join(lines)
            
        except Exception as e:
            self.logger.error(f"Error formatting analysis: {str(e)}")
            return "Error generating analysis report"
