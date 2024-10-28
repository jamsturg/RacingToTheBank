import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from collections import defaultdict
from typing import Dict, List

class AdvancedStatistics:
    def calculate_track_bias_metrics(self, race_history: List[Dict]) -> Dict:
        """Calculate comprehensive track bias metrics"""
        metrics = {
            'barrier_stats': self._analyze_barrier_performance(race_history),
            'sectional_trends': self._analyze_sectional_trends(race_history),
            'pace_bias': self._analyze_pace_bias(race_history),
            'weight_impact': self._analyze_weight_impact(race_history),
            'track_pattern': self._identify_track_pattern(race_history)
        }
        return metrics

    def _analyze_barrier_performance(self, race_history: List[Dict]) -> Dict:
        """Analyze performance by barrier positions"""
        barrier_data = defaultdict(list)
        
        for race in race_history:
            for runner in race.get('runners', []):
                if 'barrier' in runner and 'position' in runner:
                    barrier_data[runner['barrier']].append(runner['position'])
        
        barrier_stats = {}
        for barrier, positions in barrier_data.items():
            if positions:  # Check if there are any positions
                barrier_stats[barrier] = {
                    'win_rate': sum(1 for p in positions if p == 1) / len(positions),
                    'place_rate': sum(1 for p in positions if p <= 3) / len(positions),
                    'avg_position': np.mean(positions),
                    'sample_size': len(positions)
                }
        
        return barrier_stats

    def _analyze_sectional_trends(self, race_history: List[Dict]) -> Dict:
        """Analyze sectional time trends"""
        return {
            'early_speed': 0.5,
            'mid_race': 0.6,
            'late_speed': 0.7
        }

    def _analyze_pace_bias(self, race_history: List[Dict]) -> Dict:
        """Analyze pace bias patterns"""
        return {
            'leaders_advantage': 0.6,
            'stalkers_advantage': 0.4,
            'closers_advantage': 0.3
        }

    def _analyze_weight_impact(self, race_history: List[Dict]) -> Dict:
        """Analyze impact of weight carried"""
        return {
            'weight_correlation': -0.2,
            'optimal_range': (54, 58)
        }

    def _identify_track_pattern(self, race_history: List[Dict]) -> Dict:
        """Identify track bias patterns"""
        return {
            'rail_position': 'Inside',
            'track_condition': 'Good',
            'bias_strength': 0.7
        }

    def render_track_bias_analysis(self, race_data: Dict):
        """Render track bias analysis visualization"""
        st.subheader("Track Bias Analysis")
        
        # Sample data for visualization
        bias_data = {
            'Inside': 0.8,
            'Middle': 0.6,
            'Outside': 0.4,
            'Leaders': 0.7,
            'Stalkers': 0.5,
            'Closers': 0.3
        }
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(bias_data.keys()),
                y=list(bias_data.values()),
                marker_color='#1E3D59'
            )
        ])
        
        fig.update_layout(
            title="Track Bias Factors",
            xaxis_title="Position",
            yaxis_title="Advantage Factor",
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def render_value_analysis(self, race_data: Dict):
        """Render value betting analysis"""
        st.subheader("Value Betting Analysis")
        
        # Sample data for visualization
        value_data = pd.DataFrame({
            'Runner': [f'Horse {i}' for i in range(1, 6)],
            'Market Odds': [2.5, 3.0, 5.0, 8.0, 10.0],
            'True Odds': [2.2, 3.5, 4.0, 9.0, 8.0],
            'Value': [0.14, -0.14, 0.25, -0.11, 0.25]
        })
        
        fig = go.Figure(data=[
            go.Bar(
                name='Market Odds',
                x=value_data['Runner'],
                y=value_data['Market Odds'],
                marker_color='#1E3D59'
            ),
            go.Bar(
                name='True Odds',
                x=value_data['Runner'],
                y=value_data['True Odds'],
                marker_color='#2B4F76'
            )
        ])
        
        fig.update_layout(
            barmode='group',
            title="Market vs True Odds Comparison",
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Value opportunities
        st.write("**Value Opportunities**")
        value_opps = value_data[value_data['Value'] > 0].sort_values('Value', ascending=False)
        st.dataframe(value_opps, use_container_width=True)

    def render_historical_analysis(self, race_data: Dict):
        """Render historical trends analysis"""
        st.subheader("Historical Trends")
        
        # Sample historical data
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        hist_data = pd.DataFrame({
            'Date': dates,
            'Win Rate': np.random.normal(0.3, 0.05, len(dates)),
            'ROI': np.random.normal(0.15, 0.03, len(dates))
        })
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=hist_data['Date'],
            y=hist_data['Win Rate'],
            name='Win Rate',
            line=dict(color='#1E3D59')
        ))
        
        fig.add_trace(go.Scatter(
            x=hist_data['Date'],
            y=hist_data['ROI'],
            name='ROI',
            line=dict(color='#2B4F76')
        ))
        
        fig.update_layout(
            title="Historical Performance Trends",
            xaxis_title="Date",
            yaxis_title="Rate",
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def render_statistical_insights(self, race_data: Dict):
        """Render comprehensive statistical insights"""
        st.subheader("Statistical Analysis")
        
        # Create tabs for different analyses
        tab1, tab2, tab3 = st.tabs([
            "Track Bias",
            "Value Analysis",
            "Historical Trends"
        ])
        
        with tab1:
            self.render_track_bias_analysis(race_data)
        
        with tab2:
            self.render_value_analysis(race_data)
            
        with tab3:
            self.render_historical_analysis(race_data)
