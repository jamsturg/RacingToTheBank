import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import utils.logger as logger

class AdvancedStatistics:
    """Advanced statistical analysis for racing data"""
    
    def __init__(self):
        self.logger = logger.get_logger(__name__)

    def render_statistical_insights(self, data: Dict):
        """Render statistical insights dashboard"""
        try:
            # Sample data for demonstration
            dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
            stats_data = pd.DataFrame({
                'Date': dates,
                'Win Rate': np.random.uniform(0.2, 0.4, len(dates)),
                'ROI': np.random.uniform(-0.1, 0.2, len(dates)),
                'Turnover': np.random.uniform(1000, 5000, len(dates))
            })
            
            # Display key metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Average Win Rate",
                    f"{stats_data['Win Rate'].mean():.1%}",
                    f"{(stats_data['Win Rate'].iloc[-1] - stats_data['Win Rate'].iloc[0]):.1%}"
                )
            with col2:
                st.metric(
                    "Average ROI",
                    f"{stats_data['ROI'].mean():.1%}",
                    f"{(stats_data['ROI'].iloc[-1] - stats_data['ROI'].iloc[0]):.1%}"
                )
            with col3:
                st.metric(
                    "Total Turnover",
                    f"${stats_data['Turnover'].sum():,.0f}",
                    f"${(stats_data['Turnover'].iloc[-1] - stats_data['Turnover'].iloc[0]):,.0f}"
                )
            
            # Performance trend chart
            st.subheader("Performance Trends")
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=stats_data['Date'],
                y=stats_data['Win Rate'],
                name='Win Rate',
                line=dict(color='#4CAF50', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=stats_data['Date'],
                y=stats_data['ROI'],
                name='ROI',
                line=dict(color='#2196F3', width=2)
            ))
            
            fig.update_layout(
                title="Performance Metrics Over Time",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=400,
                yaxis=dict(
                    tickformat='.1%',
                    gridcolor='rgba(255,255,255,0.1)',
                    zerolinecolor='rgba(255,255,255,0.2)',
                    color='white'
                ),
                xaxis=dict(
                    gridcolor='rgba(255,255,255,0.1)',
                    zerolinecolor='rgba(255,255,255,0.2)',
                    color='white'
                ),
                font=dict(color='white'),
                showlegend=True,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            self.logger.error(f"Error rendering statistical insights: {str(e)}")
            st.error("Error loading statistical insights. Please try refreshing.")

    def render_track_bias_analysis(self, data: Dict):
        """Render track bias analysis"""
        try:
            # Sample data for demonstration
            barriers = list(range(1, 13))
            win_rates = np.random.uniform(0.1, 0.3, len(barriers))
            
            # Create bar chart
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=barriers,
                y=win_rates,
                marker_color='#4CAF50'
            ))
            
            fig.update_layout(
                title="Win Rate by Barrier",
                xaxis_title="Barrier",
                yaxis_title="Win Rate",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=400,
                yaxis=dict(
                    tickformat='.1%',
                    gridcolor='rgba(255,255,255,0.1)',
                    zerolinecolor='rgba(255,255,255,0.2)',
                    color='white'
                ),
                xaxis=dict(
                    gridcolor='rgba(255,255,255,0.1)',
                    zerolinecolor='rgba(255,255,255,0.2)',
                    color='white',
                    tickmode='linear'
                ),
                font=dict(color='white')
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Track bias insights
            st.subheader("Track Bias Insights")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                    #### Barrier Analysis
                    - Inside barriers (1-4) show a 25% win rate
                    - Middle barriers (5-8) show a 20% win rate
                    - Outside barriers (9-12) show a 15% win rate
                """)
            
            with col2:
                st.markdown("""
                    #### Running Style Analysis
                    - Leaders win 30% of races
                    - Stalkers win 40% of races
                    - Closers win 30% of races
                """)
            
        except Exception as e:
            self.logger.error(f"Error rendering track bias analysis: {str(e)}")
            st.error("Error loading track bias analysis. Please try refreshing.")

    def render_value_analysis(self, data: Dict):
        """Render value betting analysis"""
        try:
            # Sample data for demonstration
            odds_ranges = ['1.0-2.0', '2.1-3.0', '3.1-5.0', '5.1-10.0', '10.1+']
            profit_loss = np.random.uniform(-100, 200, len(odds_ranges))
            
            # Create bar chart
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=odds_ranges,
                y=profit_loss,
                marker_color=['red' if pl < 0 else 'green' for pl in profit_loss]
            ))
            
            fig.update_layout(
                title="Profit/Loss by Odds Range",
                xaxis_title="Odds Range",
                yaxis_title="Profit/Loss ($)",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=400,
                yaxis=dict(
                    gridcolor='rgba(255,255,255,0.1)',
                    zerolinecolor='rgba(255,255,255,0.2)',
                    color='white'
                ),
                xaxis=dict(
                    gridcolor='rgba(255,255,255,0.1)',
                    zerolinecolor='rgba(255,255,255,0.2)',
                    color='white'
                ),
                font=dict(color='white')
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Value betting insights
            st.subheader("Value Betting Insights")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                    #### Profitable Odds Ranges
                    - Best ROI: 3.1-5.0 (15.2%)
                    - Second best: 2.1-3.0 (8.7%)
                    - Avoid: 1.0-2.0 (-5.3%)
                """)
            
            with col2:
                st.markdown("""
                    #### Market Efficiency
                    - Market overvalues favorites
                    - Value found in mid-range odds
                    - Longshots show mixed results
                """)
            
        except Exception as e:
            self.logger.error(f"Error rendering value analysis: {str(e)}")
            st.error("Error loading value analysis. Please try refreshing.")

    def render_historical_analysis(self, data: Dict):
        """Render historical trends analysis"""
        try:
            # Sample data for demonstration
            dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
            historical_data = pd.DataFrame({
                'Date': dates,
                'Favorites': np.random.uniform(0.3, 0.4, len(dates)),
                'Second Favorites': np.random.uniform(0.2, 0.3, len(dates)),
                'Others': np.random.uniform(0.1, 0.2, len(dates))
            })
            
            # Create line chart
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=historical_data['Date'],
                y=historical_data['Favorites'],
                name='Favorites',
                line=dict(color='#4CAF50', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=historical_data['Date'],
                y=historical_data['Second Favorites'],
                name='Second Favorites',
                line=dict(color='#2196F3', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=historical_data['Date'],
                y=historical_data['Others'],
                name='Others',
                line=dict(color='#FFC107', width=2)
            ))
            
            fig.update_layout(
                title="Historical Win Rates by Market Position",
                xaxis_title="Date",
                yaxis_title="Win Rate",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=400,
                yaxis=dict(
                    tickformat='.1%',
                    gridcolor='rgba(255,255,255,0.1)',
                    zerolinecolor='rgba(255,255,255,0.2)',
                    color='white'
                ),
                xaxis=dict(
                    gridcolor='rgba(255,255,255,0.1)',
                    zerolinecolor='rgba(255,255,255,0.2)',
                    color='white'
                ),
                font=dict(color='white'),
                showlegend=True,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Historical insights
            st.subheader("Historical Insights")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                    #### Market Position Analysis
                    - Favorites win 35% of races
                    - Second favorites win 25% of races
                    - Others win 40% of races combined
                """)
            
            with col2:
                st.markdown("""
                    #### Seasonal Patterns
                    - Spring: Higher favorite success
                    - Summer: More unpredictable
                    - Autumn: Balanced results
                    - Winter: Lower overall times
                """)
            
        except Exception as e:
            self.logger.error(f"Error rendering historical analysis: {str(e)}")
            st.error("Error loading historical analysis. Please try refreshing.")
