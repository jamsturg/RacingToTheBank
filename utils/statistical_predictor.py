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
import streamlit as st
import utils.logger as logger

@dataclass
class ModelMetrics:
    """Stores model performance metrics"""
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
    """Advanced statistical predictor for race outcomes"""
    
    def __init__(self, random_state: int = 42):
        self.logger = logger.get_logger(__name__)
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
        self._initialize_models()

    def _initialize_model_weights(self) -> Dict[str, float]:
        return {'rf': 0.4, 'gb': 0.3, 'xgb': 0.3}

    def _initialize_models(self):
        """Initialize models with dummy data"""
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
                'distance_win_rate': [0.2, 0.3, 0.4],
                'track_condition_score': [1, 2, 3],
                'jockey_rating': [70, 75, 80],
                'trainer_rating': [75, 80, 85],
                'days_since_last_run': [14, 21, 28],
                'weight_carried_last_start': [54, 56, 58]
            })
            y_dummy = pd.Series([1, 2, 3])  # Dummy target values

            # Train models with dummy data
            self.rf_model.fit(X_dummy, y_dummy)
            self.gb_model.fit(X_dummy, y_dummy)
            self.xgb_model.fit(X_dummy, y_dummy)
            self.scaler.fit(X_dummy)
            
            self.logger.info("Models initialized with dummy data")
        except Exception as e:
            self.logger.error(f"Error initializing models: {str(e)}")

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
        """Render statistical insights dashboard"""
        try:
            st.subheader("Performance Metrics")
            
            # Display key metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Strike Rate",
                    f"{data.get('strike_rate', 0)}%",
                    help="Percentage of wins from total starts"
                )
            with col2:
                st.metric(
                    "ROI",
                    f"{data.get('roi', 0)}%",
                    help="Return on Investment"
                )
            with col3:
                st.metric(
                    "Average Position",
                    f"{data.get('avg_position', 0)}",
                    help="Average finishing position"
                )

            # Performance trends
            st.subheader("Performance Trends")
            if 'performance_history' in data:
                df = pd.DataFrame(data['performance_history'])
                st.line_chart(df.set_index('date')['position'])

        except Exception as e:
            self.logger.error(f"Error rendering statistical insights: {str(e)}")
            st.error("Error displaying statistical insights")

    def render_track_bias_analysis(self, data: Dict):
        """Render track bias analysis"""
        try:
            st.subheader("Track Bias Analysis")
            
            # Barrier performance
            if 'barrier_stats' in data:
                st.write("Barrier Performance")
                barrier_df = pd.DataFrame(data['barrier_stats'])
                st.bar_chart(barrier_df.set_index('barrier')['win_rate'])

            # Running style bias
            if 'style_stats' in data:
                st.write("Running Style Performance")
                style_df = pd.DataFrame(data['style_stats'])
                st.bar_chart(style_df.set_index('style')['win_rate'])

        except Exception as e:
            self.logger.error(f"Error rendering track bias analysis: {str(e)}")
            st.error("Error displaying track bias analysis")

    def render_value_analysis(self, data: Dict):
        """Render value betting analysis"""
        try:
            st.subheader("Value Betting Analysis")
            
            # Market efficiency
            if 'market_stats' in data:
                st.write("Market Efficiency")
                market_df = pd.DataFrame(data['market_stats'])
                st.line_chart(market_df.set_index('odds')['actual_probability'])

        except Exception as e:
            self.logger.error(f"Error rendering value analysis: {str(e)}")
            st.error("Error displaying value analysis")

    def render_historical_analysis(self, data: Dict):
        """Render historical trends analysis"""
        try:
            st.subheader("Historical Trends")
            
            # Seasonal patterns
            if 'seasonal_stats' in data:
                st.write("Seasonal Performance")
                seasonal_df = pd.DataFrame(data['seasonal_stats'])
                st.line_chart(seasonal_df.set_index('month')['win_rate'])

            # Distance patterns
            if 'distance_stats' in data:
                st.write("Performance by Distance")
                distance_df = pd.DataFrame(data['distance_stats'])
                st.bar_chart(distance_df.set_index('distance')['win_rate'])

        except Exception as e:
            self.logger.error(f"Error rendering historical analysis: {str(e)}")
            st.error("Error displaying historical analysis")
