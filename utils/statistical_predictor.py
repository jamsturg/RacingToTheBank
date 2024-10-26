from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from statsmodels.tsa.seasonal import seasonal_decompose
from typing import Dict, List, Tuple, Optional, Any, Union
import logging
from dataclasses import dataclass
import xgboost as xgb
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.exceptions import NotFittedError

@dataclass
class ModelMetrics:
    """Stores model performance metrics"""
    mse: float
    r2: float
    cv_score: float
    feature_importance: Dict[str, float]

class StatisticalPredictor:
    """Advanced statistical predictor for race outcomes"""
    
    def __init__(self, random_state: int = 42):
        self.feature_names = [
            'weight', 'barrier', 'rating', 'win_rate', 'place_rate',
            'momentum', 'consistency', 'best_distance', 'distance_win_rate',
            'track_condition_score', 'jockey_rating', 'trainer_rating',
            'days_since_last_run', 'weight_carried_last_start'
        ]
        self.rf_model = RandomForestRegressor(
            n_estimators=200, 
            max_depth=10,
            min_samples_split=5,
            random_state=random_state
        )
        self.gb_model = GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=6,
            random_state=random_state
        )
        self.xgb_model = xgb.XGBRegressor(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=6,
            random_state=random_state
        )
        self.scaler = StandardScaler()
        self.model_weights = self._initialize_model_weights()
        self.model_metrics: Dict[str, ModelMetrics] = {}
        self.setup_logging()
        self._initialize_models()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _initialize_models(self):
        """Initialize models with dummy data to avoid 'not fitted' errors"""
        try:
            # Create dummy data for initial training
            X_dummy = pd.DataFrame({
                'weight': [54, 56, 58],
                'barrier': [1, 5, 10],
                'rating': [70, 75, 80],
                'win_rate': [20, 30, 40],
                'place_rate': [50, 60, 70],
                'momentum': [1, 2, 3],
                'consistency': [0.5, 1.0, 1.5],
                'best_distance': [1200, 1400, 1600],
                'distance_win_rate': [0.2, 0.3, 0.4]
            })
            X_dummy = X_dummy[self.feature_names]  # Ensure consistent feature order
            y_dummy = pd.Series([1, 2, 3])  # Dummy target values

            # Train models with dummy data
            self.rf_model.fit(X_dummy, y_dummy)
            self.gb_model.fit(X_dummy, y_dummy)
            self.xgb_model.fit(X_dummy, y_dummy)
            self.scaler.fit(X_dummy)
            
            self.logger.info("Models initialized with dummy data")
        except Exception as e:
            self.logger.error(f"Error initializing models: {str(e)}")

    def prepare_features(self, horse_data: Dict) -> pd.DataFrame:
        """Convert horse data into numerical features for modeling"""
        try:
            # Basic numerical features
            numerical_features = {
                'weight': float(horse_data.get('Weight', horse_data.get('weight', 0))),
                'barrier': float(horse_data.get('Barrier', horse_data.get('barrier', 0))),
                'rating': float(horse_data.get('Rating', horse_data.get('rating', 0))),
                'win_rate': float(horse_data.get('win_rate', 0)),
                'place_rate': float(horse_data.get('place_rate', 0)),
                'momentum': 0.0,
                'consistency': 0.0,
                'best_distance': 0.0,
                'distance_win_rate': 0.0
            }

            # Historical performance features
            history = horse_data.get('performance_history', [])
            if history:
                last_5_positions = [float(run.get('position', 0)) for run in history[:5]]
                
                # Calculate momentum and consistency
                if len(last_5_positions) >= 3:
                    numerical_features['momentum'] = float(sum(
                        pos * weight for pos, weight in 
                        zip(last_5_positions[:3], [0.5, 0.3, 0.2])
                    ))
                    numerical_features['consistency'] = float(np.std(last_5_positions))

            # Distance performance
            distance_perf = horse_data.get('distance_performance', {})
            if distance_perf:
                best_dist = max(
                    distance_perf.items(),
                    key=lambda x: x[1].get('wins', 0) / max(x[1].get('runs', 1), 1),
                    default=(0, {'wins': 0, 'runs': 1})
                )
                numerical_features['best_distance'] = float(best_dist[0])
                numerical_features['distance_win_rate'] = float(
                    best_dist[1].get('wins', 0) / max(best_dist[1].get('runs', 1), 1)
                )

            # Create DataFrame with consistent feature order
            df = pd.DataFrame([numerical_features])
            return df[self.feature_names]  # Ensure consistent feature order

        except Exception as e:
            self.logger.error(f"Error preparing features: {str(e)}")
            return pd.DataFrame(columns=self.feature_names)

    def predict_performance(self, horse_data: Dict, track_bias: Dict, recent_results: List[Dict]) -> Dict:
        """Generate comprehensive performance prediction using weighted ensemble"""
        try:
            # Prepare features
            features_df = self.prepare_features(horse_data)
            if features_df.empty:
                return {}

            # Scale features
            scaled_features = pd.DataFrame(
                self.scaler.transform(features_df),
                columns=self.feature_names
            )

            # Generate predictions
            predictions = {
                'rf': float(self.rf_model.predict(scaled_features)[0]),
                'gb': float(self.gb_model.predict(scaled_features)[0]),
                'xgb': float(self.xgb_model.predict(scaled_features)[0])
            }

            # Calculate weighted prediction and variance
            weighted_pred = sum(pred * self.model_weights[model] for model, pred in predictions.items())
            variance = float(np.var(list(predictions.values())))

            # Calculate confidence level
            confidence_level = 'High' if variance < 0.1 else 'Medium' if variance < 0.2 else 'Low'

            # Apply track bias adjustments
            barrier = int(horse_data.get('Barrier', horse_data.get('barrier', 0)))
            barrier_adj = float(track_bias.get('barrier_bias', {}).get(barrier, 0))
            style_adj = float(track_bias.get('style_bias', {}).get(
                horse_data.get('running_style', 'unknown'), 0
            ))

            final_rating = weighted_pred * (1 + barrier_adj + style_adj)

            return {
                'rating': round(final_rating, 2),
                'confidence': confidence_level,
                'variance': round(variance, 3),
                'model_predictions': predictions,
                'bias_adjustments': {
                    'barrier': round(barrier_adj, 3),
                    'style': round(style_adj, 3)
                }
            }

        except Exception as e:
            self.logger.error(f"Error in predict_performance: {str(e)}")
            return {}

    def calculate_track_bias(self, recent_results: List[Dict]) -> Dict:
        """Analyze track bias from recent results"""
        if not recent_results:
            return {
                'barrier_bias': {},
                'style_bias': {},
                'inside_advantage': 0.0,
                'pace_bias': 'Neutral'
            }

        try:
            barrier_performance = {}
            running_style_performance = {}

            for result in recent_results:
                barrier = result.get('barrier', 0)
                position = result.get('position', 0)
                running_style = result.get('running_style', 'unknown')

                # Track barrier performance
                if barrier not in barrier_performance:
                    barrier_performance[barrier] = {'positions': [], 'count': 0}
                barrier_performance[barrier]['positions'].append(position)
                barrier_performance[barrier]['count'] += 1

                # Track running style performance
                if running_style not in running_style_performance:
                    running_style_performance[running_style] = {'positions': [], 'count': 0}
                running_style_performance[running_style]['positions'].append(position)
                running_style_performance[running_style]['count'] += 1

            # Calculate bias scores
            barrier_bias = {
                barrier: float(np.mean(data['positions']) / data['count'])
                for barrier, data in barrier_performance.items()
            }

            style_bias = {
                style: float(np.mean(data['positions']) / data['count'])
                for style, data in running_style_performance.items()
            }

            return {
                'barrier_bias': barrier_bias,
                'style_bias': style_bias,
                'inside_advantage': self._calculate_inside_advantage(barrier_bias),
                'pace_bias': self._calculate_pace_bias(style_bias)
            }

        except Exception as e:
            self.logger.error(f"Error calculating track bias: {str(e)}")
            return {
                'barrier_bias': {},
                'style_bias': {},
                'inside_advantage': 0.0,
                'pace_bias': 'Unknown'
            }

    def _calculate_inside_advantage(self, barrier_bias: Dict[int, float]) -> float:
        """Calculate advantage of inside barriers"""
        try:
            inside_barriers = {k: v for k, v in barrier_bias.items() if k <= 4}
            outside_barriers = {k: v for k, v in barrier_bias.items() if k > 4}
            
            if not inside_barriers or not outside_barriers:
                return 0.0

            return float(np.mean(list(outside_barriers.values())) - np.mean(list(inside_barriers.values())))
        except:
            return 0.0

    def _calculate_pace_bias(self, style_bias: Dict[str, float]) -> str:
        """Determine if track favors certain running styles"""
        try:
            leaders = style_bias.get('leader', float('inf'))
            backmarkers = style_bias.get('backmarker', float('inf'))
            
            if leaders < backmarkers:
                return 'Favors leaders'
            elif backmarkers < leaders:
                return 'Favors backmarkers'
            else:
                return 'Neutral'
        except:
            return 'Neutral'

    def analyze_seasonal_patterns(self, historical_data: List[Dict]) -> Dict:
        """Analyze seasonal patterns in performance"""
        if not historical_data:
            return {'trend': 'Unknown', 'seasonal_effect': False}

        try:
            # Extract timestamps and performances
            valid_data = []
            for race in historical_data:
                try:
                    date = pd.to_datetime(race.get('date'))
                    position = float(race.get('position', 0))
                    valid_data.append((date, position))
                except (ValueError, TypeError):
                    continue

            if len(valid_data) < 4:
                return {'trend': 'Insufficient data', 'seasonal_effect': False}

            # Create time series
            valid_data.sort(key=lambda x: x[0])
            ts = pd.Series([x[1] for x in valid_data], index=[x[0] for x in valid_data])

            # Perform seasonal decomposition
            decomposition = seasonal_decompose(ts, period=min(len(ts), 4))

            return {
                'trend': 'Improving' if decomposition.trend.iloc[-1] < decomposition.trend.iloc[0]
                        else 'Declining',
                'seasonal_effect': bool(decomposition.seasonal.std() > 0.1),
                'seasonality_strength': round(
                    float(decomposition.seasonal.std() / decomposition.resid.std()), 2
                ) if decomposition.resid.std() != 0 else 0
            }

        except Exception as e:
            self.logger.error(f"Error analyzing seasonal patterns: {str(e)}")
            return {'trend': 'Unknown', 'seasonal_effect': False}
