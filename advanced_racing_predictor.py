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
import utils.logger as logger

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
        self.logger = logger.get_logger(__name__)
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

    def predict_performance(
        self,
        runner: Dict,
        race_conditions: RaceConditions
    ) -> PredictionResult:
        """Generate comprehensive performance prediction"""
        try:
            # Prepare features
            features = self.prepare_features(runner, race_conditions)
            if features.size == 0:
                return self._get_default_prediction()
            
            # Scale features
            scaled_features = self.scaler.transform(features)
            
            # Get predictions from each model
            predictions = {}
            probabilities = {}
            for name, model in self.models.items():
                try:
                    pred = model.predict(scaled_features)[0]
                    prob = model.predict_proba(scaled_features)[0]
                    predictions[name] = pred
                    probabilities[name] = prob
                except Exception as e:
                    self.logger.error(f"Error with model {name}: {str(e)}")
                    predictions[name] = 0
                    probabilities[name] = np.zeros(2)
            
            # Calculate weighted ensemble prediction
            ensemble_prob = np.zeros_like(probabilities['rf'])
            for name, prob in probabilities.items():
                if name in self.models:
                    weight = 1 / len(self.models)  # Equal weights for now
                    ensemble_prob += prob * weight
            
            # Calculate feature importance
            feature_importance = self._calculate_feature_importance(
                scaled_features, predictions
            )
            
            # Calculate various ratings
            speed_rating = self._calculate_speed_rating(runner)
            form_rating = self._calculate_form_rating(runner)
            class_rating = self._calculate_class_rating(runner)
            
            # Calculate overall rating
            overall_rating = (speed_rating * 0.4 + 
                            form_rating * 0.3 + 
                            class_rating * 0.3)
            
            # Determine confidence level
            confidence = self._determine_confidence(
                ensemble_prob, predictions, feature_importance
            )
            
            return PredictionResult(
                probability=float(ensemble_prob[1]),  # Probability of winning
                confidence=confidence,
                predicted_position=int(np.argmin([p[0] for p in probabilities.values()])) + 1,
                win_probability=float(ensemble_prob[1]),
                place_probability=float(sum(ensemble_prob[1:4])),
                value_rating=self._calculate_value_rating(
                    float(ensemble_prob[1]), 
                    runner.get('fixed_odds', 0.0)
                ),
                speed_rating=speed_rating,
                form_rating=form_rating,
                class_rating=class_rating,
                overall_rating=overall_rating,
                model_contributions={
                    name: float(pred) 
                    for name, pred in predictions.items()
                },
                feature_importance=feature_importance
            )
        except Exception as e:
            self.logger.error(f"Error predicting performance: {str(e)}")
            return self._get_default_prediction()

    def _get_default_prediction(self) -> PredictionResult:
        """Get default prediction result"""
        return PredictionResult(
            probability=0.0,
            confidence='Low',
            predicted_position=0,
            win_probability=0.0,
            place_probability=0.0,
            value_rating=0.0,
            speed_rating=0.0,
            form_rating=0.0,
            class_rating=0.0,
            overall_rating=0.0,
            model_contributions={},
            feature_importance={}
        )

    def _calculate_feature_importance(
        self,
        features: np.ndarray,
        predictions: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate feature importance scores"""
        try:
            importance_scores = {}
            for name, model in self.models.items():
                if hasattr(model, 'feature_importances_'):
                    for feature_name, importance in zip(
                        self.feature_names, 
                        model.feature_importances_
                    ):
                        if feature_name not in importance_scores:
                            importance_scores[feature_name] = []
                        importance_scores[feature_name].append(importance)
            
            # Average importance scores across models
            return {
                feature: float(np.mean(scores))
                for feature, scores in importance_scores.items()
            }
        except Exception as e:
            self.logger.error(f"Error calculating feature importance: {str(e)}")
            return {}

    def _determine_confidence(
        self,
        probabilities: np.ndarray,
        predictions: Dict[str, float],
        feature_importance: Dict[str, float]
    ) -> str:
        """Determine prediction confidence level"""
        try:
            # Calculate prediction agreement
            unique_predictions = len(set(predictions.values()))
            if unique_predictions == 1:
                agreement_score = 1.0
            else:
                agreement_score = 1.0 / unique_predictions
            
            # Calculate probability strength
            prob_strength = max(probabilities)
            
            # Calculate feature reliability
            important_features = sorted(
                feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            feature_reliability = np.mean([imp for _, imp in important_features])
            
            # Combined confidence score
            confidence_score = (
                agreement_score * 0.4 +
                prob_strength * 0.4 +
                feature_reliability * 0.2
            )
            
            if confidence_score >= 0.8:
                return 'High'
            elif confidence_score >= 0.6:
                return 'Medium'
            else:
                return 'Low'
        except Exception as e:
            self.logger.error(f"Error determining confidence: {str(e)}")
            return 'Low'

    def _calculate_value_rating(
        self,
        win_probability: float,
        fixed_odds: float
    ) -> float:
        """Calculate value rating based on probability and odds"""
        try:
            if fixed_odds <= 1.0 or win_probability <= 0:
                return 0.0
            
            # Convert odds to probability
            market_probability = 1 / fixed_odds
            
            # Calculate value ratio
            value = (win_probability - market_probability) / market_probability
            
            return max(0.0, value * 100)  # Convert to percentage
        except Exception as e:
            self.logger.error(f"Error calculating value rating: {str(e)}")
            return 0.0

    def _calculate_speed_rating(self, runner: Dict) -> float:
        """Calculate speed rating"""
        try:
            history = runner.get('history', [])
            if not history:
                return 0.0
            
            speed_ratings = [
                float(run.get('speed_rating', 0))
                for run in history
                if run.get('speed_rating')
            ]
            
            if not speed_ratings:
                return 0.0
            
            # Weight recent ratings more heavily
            weights = np.array([0.4, 0.3, 0.2, 0.1])[:len(speed_ratings)]
            weights = weights / weights.sum()  # Normalize weights
            
            return float(np.average(speed_ratings[:len(weights)], weights=weights))
        except Exception as e:
            self.logger.error(f"Error calculating speed rating: {str(e)}")
            return 0.0

    def _calculate_form_rating(self, runner: Dict) -> float:
        """Calculate form rating"""
        try:
            form = self.analyze_form(runner)
            
            # Weight different aspects of form
            win_component = form.win_rate * 0.4
            place_component = form.place_rate * 0.3
            consistency = self._calculate_consistency_rating(form) * 0.3
            
            return float(win_component + place_component + consistency)
        except Exception as e:
            self.logger.error(f"Error calculating form rating: {str(e)}")
            return 0.0
