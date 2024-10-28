import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import plotly.graph_objects as go
import plotly.express as px
from dataclasses import dataclass
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from .logger import get_logger

@dataclass
class FormMetrics:
    """Stores comprehensive form metrics"""
    win_rate: float
    place_rate: float
    roi: float
    consistency: float
    avg_position: float
    trend: str
    class_performance: Dict[str, float]
    distance_performance: Dict[str, float]
    track_performance: Dict[str, float]
    jockey_stats: Dict[str, float]
    speed_ratings: List[float]
    weight_carried: List[float]
    barrier_stats: Dict[int, float]

class FormAnalysis:
    """Enhanced form analysis with advanced features"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=5, random_state=42)

    def calculate_form_metrics(self, runner_data: Dict) -> FormMetrics:
        """Calculate comprehensive form metrics"""
        try:
            # Extract recent form
            form_string = runner_data.get('form', '')
            recent_results = []
            
            # Convert form string to list of positions
            for char in form_string:
                if char.isdigit():
                    recent_results.append(int(char))
                elif char.upper() == 'W':
                    recent_results.append(1)
                    
            if not recent_results:
                return self._get_default_metrics()

            # Calculate basic metrics
            wins = sum(1 for pos in recent_results if pos == 1)
            places = sum(1 for pos in recent_results if pos <= 3)
            avg_pos = np.mean(recent_results)
            consistency = 100 * (1 - np.std(recent_results) / max(recent_results))
            
            # Calculate ROI
            total_stake = len(recent_results) * 10  # Assuming $10 bets
            returns = wins * 25  # Assuming average win dividend of $2.50
            roi = ((returns - total_stake) / total_stake) * 100

            # Determine trend
            if len(recent_results) >= 3:
                last_three = recent_results[-3:]
                if all(x <= y for x, y in zip(last_three, last_three[1:])):
                    trend = 'Declining'
                elif all(x >= y for x, y in zip(last_three, last_three[1:])):
                    trend = 'Improving'
                else:
                    trend = 'Mixed'
            else:
                trend = 'Insufficient data'

            # Calculate class performance
            class_perf = self._analyze_class_performance(runner_data.get('history', []))
            
            # Calculate distance performance
            distance_perf = self._analyze_distance_performance(runner_data.get('history', []))
            
            # Calculate track performance
            track_perf = self._analyze_track_performance(runner_data.get('history', []))
            
            # Calculate jockey statistics
            jockey_stats = self._analyze_jockey_performance(runner_data.get('jockey_history', []))
            
            # Extract speed ratings and weights
            speed_ratings = [
                float(run.get('speed_rating', 0))
                for run in runner_data.get('history', [])
                if run.get('speed_rating')
            ]
            
            weights = [
                float(run.get('weight_carried', 0))
                for run in runner_data.get('history', [])
                if run.get('weight_carried')
            ]
            
            # Calculate barrier statistics
            barrier_stats = self._analyze_barrier_performance(runner_data.get('history', []))

            return FormMetrics(
                win_rate=wins / len(recent_results) * 100,
                place_rate=places / len(recent_results) * 100,
                roi=roi,
                consistency=consistency,
                avg_position=avg_pos,
                trend=trend,
                class_performance=class_perf,
                distance_performance=distance_perf,
                track_performance=track_perf,
                jockey_stats=jockey_stats,
                speed_ratings=speed_ratings,
                weight_carried=weights,
                barrier_stats=barrier_stats
            )

        except Exception as e:
            self.logger.error(f"Error calculating form metrics: {str(e)}")
            return self._get_default_metrics()

    def _get_default_metrics(self) -> FormMetrics:
        """Return default metrics when data is insufficient"""
        return FormMetrics(
            win_rate=0,
            place_rate=0,
            roi=0,
            consistency=0,
            avg_position=0,
            trend='Insufficient data',
            class_performance={},
            distance_performance={},
            track_performance={},
            jockey_stats={},
            speed_ratings=[],
            weight_carried=[],
            barrier_stats={}
        )

    def _analyze_class_performance(self, history: List[Dict]) -> Dict[str, float]:
        """Analyze performance by race class"""
        class_stats = {}
        for run in history:
            race_class = run.get('class', 'Unknown')
            position = run.get('position', 0)
            if race_class not in class_stats:
                class_stats[race_class] = {'runs': 0, 'wins': 0}
            class_stats[race_class]['runs'] += 1
            if position == 1:
                class_stats[race_class]['wins'] += 1

        return {
            cls: stats['wins'] / stats['runs'] * 100
            for cls, stats in class_stats.items()
        }

    def _analyze_distance_performance(self, history: List[Dict]) -> Dict[str, float]:
        """Analyze performance by race distance"""
        distance_stats = {}
        for run in history:
            distance = run.get('distance', 0)
            position = run.get('position', 0)
            distance_range = f"{(distance // 200) * 200}-{((distance // 200) + 1) * 200}"
            
            if distance_range not in distance_stats:
                distance_stats[distance_range] = {'runs': 0, 'wins': 0}
            distance_stats[distance_range]['runs'] += 1
            if position == 1:
                distance_stats[distance_range]['wins'] += 1

        return {
            dist: stats['wins'] / stats['runs'] * 100
            for dist, stats in distance_stats.items()
        }

    def _analyze_track_performance(self, history: List[Dict]) -> Dict[str, float]:
        """Analyze performance by track"""
        track_stats = {}
        for run in history:
            track = run.get('track', 'Unknown')
            position = run.get('position', 0)
            if track not in track_stats:
                track_stats[track] = {'runs': 0, 'wins': 0}
            track_stats[track]['runs'] += 1
            if position == 1:
                track_stats[track]['wins'] += 1

        return {
            track: stats['wins'] / stats['runs'] * 100
            for track, stats in track_stats.items()
        }

    def _analyze_jockey_performance(self, history: List[Dict]) -> Dict[str, float]:
        """Analyze performance by jockey"""
        jockey_stats = {}
        for run in history:
            jockey = run.get('jockey', 'Unknown')
            position = run.get('position', 0)
            if jockey not in jockey_stats:
                jockey_stats[jockey] = {'runs': 0, 'wins': 0}
            jockey_stats[jockey]['runs'] += 1
            if position == 1:
                jockey_stats[jockey]['wins'] += 1

        return {
            jockey: stats['wins'] / stats['runs'] * 100
            for jockey, stats in jockey_stats.items()
        }

    def _analyze_barrier_performance(self, history: List[Dict]) -> Dict[int, float]:
        """Analyze performance by barrier"""
        barrier_stats = {}
        for run in history:
            barrier = run.get('barrier', 0)
            position = run.get('position', 0)
            if barrier not in barrier_stats:
                barrier_stats[barrier] = {'runs': 0, 'wins': 0}
            barrier_stats[barrier]['runs'] += 1
            if position == 1:
                barrier_stats[barrier]['wins'] += 1

        return {
            barrier: stats['wins'] / stats['runs'] * 100
            for barrier, stats in barrier_stats.items()
        }

    def cluster_performances(self, history: List[Dict]) -> List[str]:
        """Cluster performances using KMeans"""
        try:
            if not history:
                return []

            # Extract features for clustering
            features = []
            for run in history:
                features.append([
                    float(run.get('position', 0)),
                    float(run.get('speed_rating', 0)),
                    float(run.get('weight_carried', 0)),
                    float(run.get('barrier', 0))
                ])

            # Scale features
            features = self.scaler.fit_transform(features)
            
            # Perform clustering
            clusters = self.kmeans.fit_predict(features)
            
            # Map clusters to performance levels
            cluster_means = pd.DataFrame(features).groupby(clusters).mean()
            cluster_ranks = cluster_means[0].rank().to_dict()  # Use position as ranking criteria
            
            return [
                f"Performance Group {int(cluster_ranks[c])}"
                for c in clusters
            ]

        except Exception as e:
            self.logger.error(f"Error clustering performances: {str(e)}")
            return []

    def render_form_dashboard(self, runner_data: Dict):
        """Render enhanced form analysis dashboard"""
        try:
            # Calculate metrics
            metrics = self.calculate_form_metrics(runner_data)
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Win Rate",
                    f"{metrics.win_rate:.1f}%",
                    help="Percentage of wins in recent starts"
                )
                
            with col2:
                st.metric(
                    "Place Rate",
                    f"{metrics.place_rate:.1f}%",
                    help="Percentage of placings (top 3) in recent starts"
                )
                
            with col3:
                st.metric(
                    "ROI",
                    f"{metrics.roi:.1f}%",
                    help="Return on Investment"
                )
                
            # Form trend
            st.subheader("Form Analysis")
            trend_color = {
                'Improving': 'green',
                'Declining': 'red',
                'Mixed': 'orange',
                'Insufficient data': 'grey'
            }
            
            st.markdown(
                f"""
                <div style='background-color: {trend_color[metrics.trend]}; padding: 10px; border-radius: 5px;'>
                    <h4 style='color: white; margin: 0;'>Current Trend: {metrics.trend}</h4>
                    <p style='color: white; margin: 0;'>Consistency: {metrics.consistency:.1f}%</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Performance visualizations
            st.subheader("Performance Analysis")
            
            # Create tabs for different analyses
            tab1, tab2, tab3, tab4 = st.tabs([
                "Speed Ratings", "Class Analysis", "Distance Analysis", "Track Analysis"
            ])
            
            with tab1:
                if metrics.speed_ratings:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        y=metrics.speed_ratings,
                        mode='lines+markers',
                        name='Speed Rating',
                        line=dict(color='#4CAF50', width=2),
                        marker=dict(size=8)
                    ))
                    fig.update_layout(
                        title="Speed Rating Progression",
                        yaxis_title="Rating",
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No speed rating data available")
            
            with tab2:
                if metrics.class_performance:
                    fig = px.bar(
                        x=list(metrics.class_performance.keys()),
                        y=list(metrics.class_performance.values()),
                        title="Performance by Class",
                        labels={'x': 'Class', 'y': 'Win Rate (%)'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No class performance data available")
            
            with tab3:
                if metrics.distance_performance:
                    fig = px.line(
                        x=list(metrics.distance_performance.keys()),
                        y=list(metrics.distance_performance.values()),
                        title="Performance by Distance",
                        labels={'x': 'Distance Range', 'y': 'Win Rate (%)'},
                        markers=True
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No distance performance data available")
            
            with tab4:
                if metrics.track_performance:
                    fig = px.bar(
                        x=list(metrics.track_performance.keys()),
                        y=list(metrics.track_performance.values()),
                        title="Performance by Track",
                        labels={'x': 'Track', 'y': 'Win Rate (%)'}
                    )
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No track performance data available")
            
            # Jockey analysis
            st.subheader("Jockey Performance")
            if metrics.jockey_stats:
                for jockey, win_rate in metrics.jockey_stats.items():
                    st.markdown(f"""
                        <div style='background-color: #2B4F76; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
                            <h4 style='color: white; margin: 0;'>{jockey}</h4>
                            <div style='background-color: rgba(255,255,255,0.1); height: 20px; border-radius: 10px; margin-top: 5px;'>
                                <div style='background-color: #4CAF50; width: {win_rate}%; height: 100%; border-radius: 10px;'></div>
                            </div>
                            <p style='color: white; margin: 5px 0 0 0;'>{win_rate:.1f}% win rate</p>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No jockey performance data available")
            
            # Barrier analysis
            st.subheader("Barrier Analysis")
            if metrics.barrier_stats:
                fig = px.bar(
                    x=list(metrics.barrier_stats.keys()),
                    y=list(metrics.barrier_stats.values()),
                    title="Performance by Barrier",
                    labels={'x': 'Barrier', 'y': 'Win Rate (%)'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No barrier performance data available")

        except Exception as e:
            self.logger.error(f"Error rendering form dashboard: {str(e)}")
            st.error("Error displaying form analysis")

    def export_analysis(self, runner_data: Dict) -> Dict:
        """Export form analysis data"""
        try:
            metrics = self.calculate_form_metrics(runner_data)
            return {
                'metrics': {
                    'win_rate': metrics.win_rate,
                    'place_rate': metrics.place_rate,
                    'roi': metrics.roi,
                    'consistency': metrics.consistency,
                    'trend': metrics.trend
                },
                'performance_clusters': self.cluster_performances(
                    runner_data.get('history', [])
                ),
                'class_performance': metrics.class_performance,
                'distance_performance': metrics.distance_performance,
                'track_performance': metrics.track_performance,
                'jockey_stats': metrics.jockey_stats,
                'barrier_stats': metrics.barrier_stats
            }
        except Exception as e:
            self.logger.error(f"Error exporting analysis: {str(e)}")
            return {}
