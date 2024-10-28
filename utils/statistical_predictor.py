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
from sklearn.metrics import mean_squared_error, r2_score, precision_score, recall_score, f1_score
from sklearn.exceptions import NotFittedError
import streamlit as st
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from .logger import get_logger

@dataclass
class ModelMetrics:
    """Stores comprehensive model performance metrics"""
    mse: float
    rmse: float
    r2: float
    mae: float
    cv_score: float
    feature_importance: Dict[str, float]
    precision: float
    recall: float
    f1: float

class StatisticalPredictor:
    """Advanced statistical predictor with enhanced ML capabilities"""
    
    def __init__(self, random_state: int = 42):
        self.logger = get_logger(__name__)
        self.feature_names = [
            'weight', 'barrier', 'rating', 'win_rate', 'place_rate',
            'momentum', 'consistency', 'best_distance', 'distance_win_rate',
            'track_condition_score', 'jockey_rating', 'trainer_rating',
            'days_since_last_run', 'weight_carried_last_start',
            'class_level', 'prize_money', 'age', 'career_wins',
            'track_win_rate', 'seasonal_performance'
        ]
        
        # Initialize models with optimized parameters
        self.rf_model = RandomForestRegressor(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            random_state=random_state,
            n_jobs=-1
        )
        
        self.gb_model = GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=6,
            min_samples_split=5,
            min_samples_leaf=2,
            subsample=0.8,
            random_state=random_state
        )
        
        self.xgb_model = xgb.XGBRegressor(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=6,
            min_child_weight=2,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state,
            n_jobs=-1
        )
        
        self.scaler = StandardScaler()
        self.model_weights = self._initialize_model_weights()
        self.model_metrics: Dict[str, ModelMetrics] = {}
        self._initialize_models()

    def _initialize_model_weights(self) -> Dict[str, float]:
        """Initialize model weights based on performance"""
        return {
            'rf': 0.35,  # Random Forest
            'gb': 0.35,  # Gradient Boosting
            'xgb': 0.30  # XGBoost
        }

    def _initialize_models(self):
        """Initialize models with dummy data"""
        try:
            # Create comprehensive dummy data
            X_dummy = pd.DataFrame({
                feature: np.random.rand(100) for feature in self.feature_names
            })
            y_dummy = np.random.rand(100)  # Dummy target values

            # Train models with dummy data
            self.rf_model.fit(X_dummy, y_dummy)
            self.gb_model.fit(X_dummy, y_dummy)
            self.xgb_model.fit(X_dummy, y_dummy)
            self.scaler.fit(X_dummy)
            
            self.logger.info("Models initialized with dummy data")
        except Exception as e:
            self.logger.error(f"Error initializing models: {str(e)}")

    def prepare_features(self, horse_data: Dict) -> pd.DataFrame:
        """Prepare features with enhanced feature engineering"""
        try:
            # Basic numerical features
            features = {
                'weight': float(horse_data.get('weight', 0)),
                'barrier': float(horse_data.get('barrier', 0)),
                'rating': float(horse_data.get('rating', 0)),
                'win_rate': float(horse_data.get('win_rate', 0)),
                'place_rate': float(horse_data.get('place_rate', 0))
            }

            # Calculate momentum and consistency
            history = horse_data.get('performance_history', [])
            if history:
                last_5_positions = [float(run.get('position', 0)) for run in history[:5]]
                
                # Enhanced momentum calculation
                if len(last_5_positions) >= 3:
                    weighted_positions = [pos * weight for pos, weight in 
                                       zip(last_5_positions[:3], [0.5, 0.3, 0.2])]
                    features['momentum'] = sum(weighted_positions)
                    features['consistency'] = float(np.std(last_5_positions))
                else:
                    features['momentum'] = 0.0
                    features['consistency'] = 0.0

            # Enhanced distance performance
            distance_perf = horse_data.get('distance_performance', {})
            if distance_perf:
                best_dist = max(
                    distance_perf.items(),
                    key=lambda x: x[1].get('wins', 0) / max(x[1].get('runs', 1), 1)
                )
                features['best_distance'] = float(best_dist[0])
                features['distance_win_rate'] = float(
                    best_dist[1].get('wins', 0) / max(best_dist[1].get('runs', 1), 1)
                )

            # Track condition performance
            track_conditions = horse_data.get('track_condition_performance', {})
            features['track_condition_score'] = sum(
                score * runs / total_runs
                for condition, (score, runs) in track_conditions.items()
                if (total_runs := sum(r for _, r in track_conditions.values())) > 0
            )

            # Jockey and trainer ratings
            features['jockey_rating'] = float(
                horse_data.get('jockey', {}).get('rating', 0)
            )
            features['trainer_rating'] = float(
                horse_data.get('trainer', {}).get('rating', 0)
            )

            # Days since last run and weight carried
            if history:
                last_run = history[0]
                features['days_since_last_run'] = (
                    datetime.now() - datetime.fromisoformat(last_run['date'])
                ).days
                features['weight_carried_last_start'] = float(
                    last_run.get('weight_carried', 0)
                )

            # Additional features
            features['class_level'] = float(horse_data.get('class_level', 0))
            features['prize_money'] = float(horse_data.get('prize_money', 0))
            features['age'] = float(horse_data.get('age', 0))
            features['career_wins'] = float(horse_data.get('career_wins', 0))
            features['track_win_rate'] = float(horse_data.get('track_win_rate', 0))
            
            # Seasonal performance
            seasonal_perf = self._calculate_seasonal_performance(history)
            features['seasonal_performance'] = seasonal_perf

            # Create DataFrame with consistent feature order
            df = pd.DataFrame([features])
            return df[self.feature_names]

        except Exception as e:
            self.logger.error(f"Error preparing features: {str(e)}")
            return pd.DataFrame(columns=self.feature_names)

    def _calculate_seasonal_performance(self, history: List[Dict]) -> float:
        """Calculate seasonal performance score"""
        try:
            if not history:
                return 0.0

            seasonal_weights = {
                'summer': 1.0,
                'autumn': 0.9,
                'winter': 0.8,
                'spring': 1.1
            }

            performances = []
            for run in history:
                date = datetime.fromisoformat(run['date'])
                month = date.month
                if 3 <= month <= 5:
                    season = 'autumn'
                elif 6 <= month <= 8:
                    season = 'winter'
                elif 9 <= month <= 11:
                    season = 'spring'
                else:
                    season = 'summer'

                position = float(run.get('position', 0))
                weighted_perf = (1 / position) * seasonal_weights[season]
                performances.append(weighted_perf)

            return float(np.mean(performances)) if performances else 0.0

        except Exception as e:
            self.logger.error(f"Error calculating seasonal performance: {str(e)}")
            return 0.0

    def train_models(self, X: pd.DataFrame, y: pd.Series):
        """Train models with enhanced validation"""
        try:
            # Split data
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_val_scaled = self.scaler.transform(X_val)

            # Train models
            models = {
                'rf': self.rf_model,
                'gb': self.gb_model,
                'xgb': self.xgb_model
            }

            for name, model in models.items():
                # Train model
                model.fit(X_train_scaled, y_train)
                
                # Make predictions
                y_pred = model.predict(X_val_scaled)
                
                # Calculate metrics
                mse = mean_squared_error(y_val, y_pred)
                rmse = np.sqrt(mse)
                r2 = r2_score(y_val, y_pred)
                mae = np.mean(np.abs(y_val - y_pred))
                cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
                
                # Calculate classification metrics using threshold
                threshold = np.median(y_val)
                y_val_binary = y_val > threshold
                y_pred_binary = y_pred > threshold
                
                precision = precision_score(y_val_binary, y_pred_binary)
                recall = recall_score(y_val_binary, y_pred_binary)
                f1 = f1_score(y_val_binary, y_pred_binary)
                
                # Get feature importance
                if hasattr(model, 'feature_importances_'):
                    importance = dict(zip(
                        self.feature_names,
                        model.feature_importances_
                    ))
                else:
                    importance = {}

                # Store metrics
                self.model_metrics[name] = ModelMetrics(
                    mse=mse,
                    rmse=rmse,
                    r2=r2,
                    mae=mae,
                    cv_score=np.mean(cv_scores),
                    feature_importance=importance,
                    precision=precision,
                    recall=recall,
                    f1=f1
                )

            # Update model weights based on performance
            total_f1 = sum(m.f1 for m in self.model_metrics.values())
            self.model_weights = {
                name: metrics.f1 / total_f1
                for name, metrics in self.model_metrics.items()
            }

            self.logger.info("Models trained successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error training models: {str(e)}")
            return False

    def predict(self, features: pd.DataFrame) -> Dict[str, Any]:
        """Make predictions with uncertainty estimation"""
        try:
            # Scale features
            scaled_features = self.scaler.transform(features)
            
            # Get predictions from each model
            predictions = {
                'rf': self.rf_model.predict(scaled_features)[0],
                'gb': self.gb_model.predict(scaled_features)[0],
                'xgb': self.xgb_model.predict(scaled_features)[0]
            }
            
            # Calculate weighted ensemble prediction
            weighted_pred = sum(
                pred * self.model_weights[model]
                for model, pred in predictions.items()
            )
            
            # Calculate prediction uncertainty
            uncertainty = np.std(list(predictions.values()))
            
            # Determine confidence level
            if uncertainty < 0.1:
                confidence = 'High'
            elif uncertainty < 0.2:
                confidence = 'Medium'
            else:
                confidence = 'Low'
            
            return {
                'prediction': weighted_pred,
                'uncertainty': uncertainty,
                'confidence': confidence,
                'model_predictions': predictions,
                'model_weights': self.model_weights
            }

        except Exception as e:
            self.logger.error(f"Error making prediction: {str(e)}")
            return {}

class AdvancedStatistics(StatisticalPredictor):
    """Enhanced statistical analysis for racing insights"""
    
    def __init__(self):
        super().__init__()
        self.initialize_session_state()

    def initialize_session_state(self):
        """Initialize session state for statistics"""
        if 'stats_cache' not in st.session_state:
            st.session_state.stats_cache = {}

    def render_statistical_insights(self, data: Dict):
        """Render comprehensive statistical insights"""
        try:
            st.subheader("Performance Metrics")
            
            # Display key metrics with enhanced visualization
            col1, col2, col3 = st.columns(3)
            with col1:
                self._render_metric_card(
                    "Strike Rate",
                    data.get('strike_rate', 0),
                    "Percentage of wins from total starts",
                    "green" if data.get('strike_rate', 0) > 20 else "red"
                )
            with col2:
                self._render_metric_card(
                    "ROI",
                    data.get('roi', 0),
                    "Return on Investment",
                    "green" if data.get('roi', 0) > 0 else "red"
                )
            with col3:
                self._render_metric_card(
                    "Average Position",
                    data.get('avg_position', 0),
                    "Average finishing position",
                    "green" if data.get('avg_position', 0) < 4 else "red"
                )

            # Performance trends
            st.subheader("Performance Trends")
            if 'performance_history' in data:
                self._render_performance_chart(data['performance_history'])

        except Exception as e:
            self.logger.error(f"Error rendering statistical insights: {str(e)}")
            st.error("Error displaying statistical insights")

    def _render_metric_card(
        self,
        title: str,
        value: float,
        help_text: str,
        color: str
    ):
        """Render enhanced metric card"""
        st.markdown(f"""
            <div style='
                background-color: rgba(255,255,255,0.1);
                padding: 20px;
                border-radius: 10px;
                border-left: 5px solid {color};
            '>
                <h3 style='margin:0; color: white;'>{title}</h3>
                <p style='font-size: 24px; margin:10px 0; color: {color};'>
                    {value:.1f}%
                </p>
                <p style='margin:0; font-size: 12px; color: rgba(255,255,255,0.7);'>
                    {help_text}
                </p>
            </div>
        """, unsafe_allow_html=True)

    def _render_performance_chart(self, history: List[Dict]):
        """Render interactive performance chart"""
        df = pd.DataFrame(history)
        
        fig = go.Figure()
        
        # Add position line
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['position'],
            mode='lines+markers',
            name='Position',
            line=dict(color='#4CAF50', width=2),
            marker=dict(size=8)
        ))
        
        # Add prize money bars
        fig.add_trace(go.Bar(
            x=df['date'],
            y=df['prize_money'],
            name='Prize Money',
            marker_color='rgba(76, 175, 80, 0.3)',
            yaxis='y2'
        ))
        
        fig.update_layout(
            title="Performance History",
            xaxis_title="Date",
            yaxis=dict(
                title="Position",
                autorange="reversed",
                gridcolor='rgba(255,255,255,0.1)',
                zerolinecolor='rgba(255,255,255,0.2)',
                color='white'
            ),
            yaxis2=dict(
                title="Prize Money ($)",
                overlaying='y',
                side='right',
                gridcolor='rgba(255,255,255,0.1)',
                zerolinecolor='rgba(255,255,255,0.2)',
                color='white'
            ),
            showlegend=True,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def render_track_bias_analysis(self, data: Dict):
        """Render comprehensive track bias analysis"""
        try:
            st.subheader("Track Bias Analysis")
            
            # Barrier performance
            if 'barrier_stats' in data:
                st.write("Barrier Performance")
                self._render_barrier_chart(data['barrier_stats'])

            # Running style bias
            if 'style_stats' in data:
                st.write("Running Style Performance")
                self._render_style_chart(data['style_stats'])

            # Track condition bias
            if 'condition_stats' in data:
                st.write("Track Condition Impact")
                self._render_condition_chart(data['condition_stats'])

        except Exception as e:
            self.logger.error(f"Error rendering track bias analysis: {str(e)}")
            st.error("Error displaying track bias analysis")

    def render_value_analysis(self, data: Dict):
        """Render comprehensive value betting analysis"""
        try:
            st.subheader("Value Betting Analysis")
            
            # Market efficiency
            if 'market_stats' in data:
                st.write("Market Efficiency")
                self._render_market_efficiency_chart(data['market_stats'])

            # Value opportunities
            if 'value_opportunities' in data:
                st.write("Value Opportunities")
                self._render_value_opportunities(data['value_opportunities'])

        except Exception as e:
            self.logger.error(f"Error rendering value analysis: {str(e)}")
            st.error("Error displaying value analysis")

    def render_historical_analysis(self, data: Dict):
        """Render comprehensive historical trends analysis"""
        try:
            st.subheader("Historical Trends")
            
            # Seasonal patterns
            if 'seasonal_stats' in data:
                st.write("Seasonal Performance")
                self._render_seasonal_chart(data['seasonal_stats'])

            # Distance patterns
            if 'distance_stats' in data:
                st.write("Performance by Distance")
                self._render_distance_chart(data['distance_stats'])

            # Class progression
            if 'class_progression' in data:
                st.write("Class Progression")
                self._render_class_progression(data['class_progression'])

        except Exception as e:
            self.logger.error(f"Error rendering historical analysis: {str(e)}")
            st.error("Error displaying historical analysis")
