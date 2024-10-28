import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, List

class RacingVisualizations:
    def render_speed_map(self, race_data: Dict):
        """Render speed map visualization"""
        try:
            # Create sample speed map data
            runners = [
                {'name': 'Horse 1', 'barrier': 4, 'early_speed': 85},
                {'name': 'Horse 2', 'barrier': 7, 'early_speed': 90},
                {'name': 'Horse 3', 'barrier': 2, 'early_speed': 75},
                {'name': 'Horse 4', 'barrier': 5, 'early_speed': 80}
            ]
            
            # Create speed map figure
            fig = go.Figure()
            
            # Add runners to speed map
            for runner in runners:
                fig.add_trace(go.Scatter(
                    x=[runner['barrier'], runner['early_speed']/20],
                    y=[0, 1],
                    mode='lines+markers+text',
                    name=runner['name'],
                    text=[runner['name'], ''],
                    textposition='top center',
                    line=dict(width=2),
                    marker=dict(size=10)
                ))
            
            # Update layout
            fig.update_layout(
                title="Speed Map - First 200m",
                xaxis=dict(
                    title="Track Width",
                    range=[0, 12],
                    showgrid=True,
                    gridcolor='rgba(255,255,255,0.2)'
                ),
                yaxis=dict(
                    title="Distance",
                    range=[-0.1, 1.1],
                    showgrid=True,
                    gridcolor='rgba(255,255,255,0.2)'
                ),
                showlegend=True,
                template="plotly_dark",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Add speed map analysis
            st.markdown("### Speed Map Analysis")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Early Speed**")
                for runner in sorted(runners, key=lambda x: x['early_speed'], reverse=True):
                    st.write(f"{runner['name']}: {runner['early_speed']}")
            
            with col2:
                st.write("**Predicted Positions**")
                positions = [
                    {'name': 'Horse 2', 'position': '1st'},
                    {'name': 'Horse 1', 'position': '2nd'},
                    {'name': 'Horse 4', 'position': '3rd'},
                    {'name': 'Horse 3', 'position': '4th'}
                ]
                for pos in positions:
                    st.write(f"{pos['name']}: {pos['position']}")
            
        except Exception as e:
            st.error(f"Error rendering speed map: {str(e)}")

    def render_form_comparison(self, runners: List[Dict]):
        """Render form comparison visualization"""
        try:
            # Create sample form comparison data
            form_data = pd.DataFrame({
                'Runner': ['Horse 1', 'Horse 2', 'Horse 3'],
                'Last Start': [1, 2, 3],
                'Two Back': [2, 1, 4],
                'Three Back': [1, 3, 2],
                'Win Rate': [0.33, 0.25, 0.40],
                'Place Rate': [0.67, 0.50, 0.80]
            })
            
            # Create form comparison figure
            fig = go.Figure()
            
            # Add bars for win and place rates
            fig.add_trace(go.Bar(
                name='Win Rate',
                x=form_data['Runner'],
                y=form_data['Win Rate'],
                marker_color='#1E3D59'
            ))
            
            fig.add_trace(go.Bar(
                name='Place Rate',
                x=form_data['Runner'],
                y=form_data['Place Rate'],
                marker_color='#2B4F76'
            ))
            
            # Update layout
            fig.update_layout(
                title="Form Comparison",
                barmode='group',
                xaxis_title="Runner",
                yaxis_title="Rate",
                template="plotly_dark",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Add recent form table
            st.markdown("### Recent Form")
            recent_form = pd.DataFrame({
                'Runner': form_data['Runner'],
                'Last 3 Starts': [
                    f"1-2-1 ({form_data['Win Rate'][0]*100:.1f}%)",
                    f"2-1-3 ({form_data['Win Rate'][1]*100:.1f}%)",
                    f"3-2-1 ({form_data['Win Rate'][2]*100:.1f}%)"
                ]
            })
            st.dataframe(recent_form, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error rendering form comparison: {str(e)}")

    def render_odds_movement(self, odds_data: List[Dict]):
        """Render odds movement visualization"""
        try:
            # Create sample odds movement data
            times = ['13:00', '13:30', '14:00', '14:30', '15:00']
            odds_movement = pd.DataFrame({
                'Time': times,
                'Horse 1': [2.80, 2.60, 2.40, 2.20, 2.40],
                'Horse 2': [3.00, 3.20, 3.50, 3.80, 3.50],
                'Horse 3': [4.00, 4.20, 4.00, 3.80, 4.00]
            })
            
            # Create odds movement figure
            fig = go.Figure()
            
            # Add line for each runner
            for runner in odds_movement.columns[1:]:
                fig.add_trace(go.Scatter(
                    name=runner,
                    x=odds_movement['Time'],
                    y=odds_movement[runner],
                    mode='lines+markers',
                    line=dict(width=2),
                    marker=dict(size=8)
                ))
            
            # Update layout
            fig.update_layout(
                title="Odds Movement",
                xaxis_title="Time",
                yaxis_title="Odds ($)",
                template="plotly_dark",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Add market analysis
            st.markdown("### Market Analysis")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Market Movers**")
                movers = [
                    {'name': 'Horse 1', 'movement': -0.40},
                    {'name': 'Horse 2', 'movement': 0.50},
                    {'name': 'Horse 3', 'movement': 0.00}
                ]
                for mover in movers:
                    movement = "↓" if mover['movement'] < 0 else "↑" if mover['movement'] > 0 else "→"
                    st.write(f"{mover['name']}: {movement} ${abs(mover['movement']):.2f}")
            
            with col2:
                st.write("**Market Confidence**")
                confidence = [
                    {'name': 'Horse 1', 'level': 'High'},
                    {'name': 'Horse 2', 'level': 'Medium'},
                    {'name': 'Horse 3', 'level': 'Low'}
                ]
                for conf in confidence:
                    st.write(f"{conf['name']}: {conf['level']}")
            
        except Exception as e:
            st.error(f"Error rendering odds movement: {str(e)}")

    def render_track_bias(self, track_data: Dict):
        """Render track bias visualization"""
        try:
            # Create sample track bias data
            bias_data = pd.DataFrame({
                'Position': ['Inside', 'Middle', 'Outside'],
                'Win Rate': [0.22, 0.35, 0.18],
                'Place Rate': [0.45, 0.55, 0.40]
            })
            
            # Create track bias figure
            fig = go.Figure()
            
            # Add bars for win and place rates
            fig.add_trace(go.Bar(
                name='Win Rate',
                x=bias_data['Position'],
                y=bias_data['Win Rate'],
                marker_color='#1E3D59'
            ))
            
            fig.add_trace(go.Bar(
                name='Place Rate',
                x=bias_data['Position'],
                y=bias_data['Place Rate'],
                marker_color='#2B4F76'
            ))
            
            # Update layout
            fig.update_layout(
                title="Track Bias Analysis",
                barmode='group',
                xaxis_title="Track Position",
                yaxis_title="Rate",
                template="plotly_dark",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Add bias analysis
            st.markdown("### Track Bias Summary")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Position Analysis**")
                for _, row in bias_data.iterrows():
                    st.write(f"{row['Position']}: {row['Win Rate']*100:.1f}% Win, {row['Place Rate']*100:.1f}% Place")
            
            with col2:
                st.write("**Recommendations**")
                st.write("- Prefer runners drawn middle barriers")
                st.write("- Inside runners performing below average")
                st.write("- Outside barriers challenging today")
            
        except Exception as e:
            st.error(f"Error rendering track bias: {str(e)}")

    def render_performance_metrics(self, performance_data: Dict):
        """Render performance metrics visualization"""
        try:
            # Create sample performance data
            metrics = pd.DataFrame({
                'Metric': ['Speed', 'Stamina', 'Form', 'Class'],
                'Horse 1': [85, 75, 80, 90],
                'Horse 2': [80, 85, 75, 85],
                'Horse 3': [75, 80, 85, 80]
            })
            
            # Create radar chart
            fig = go.Figure()
            
            # Add trace for each runner
            for runner in metrics.columns[1:]:
                fig.add_trace(go.Scatterpolar(
                    name=runner,
                    r=metrics[runner],
                    theta=metrics['Metric'],
                    fill='toself',
                    line=dict(width=2)
                ))
            
            # Update layout
            fig.update_layout(
                title="Performance Comparison",
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )
                ),
                showlegend=True,
                template="plotly_dark",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Add detailed metrics
            st.markdown("### Detailed Metrics")
            for metric in metrics['Metric']:
                st.write(f"**{metric}**")
                for runner in metrics.columns[1:]:
                    value = metrics.loc[metrics['Metric'] == metric, runner].iloc[0]
                    st.write(f"{runner}: {value}")
                st.write("")
            
        except Exception as e:
            st.error(f"Error rendering performance metrics: {str(e)}")
