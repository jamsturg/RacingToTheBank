import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from sklearn.preprocessing import StandardScaler
from typing import Dict

class FormAnalysis:
    def __init__(self):
        self.scaler = StandardScaler()
        self.weights = {
            'recent_form': 0.3,
            'class': 0.2,
            'distance': 0.15,
            'track': 0.15,
            'time': 0.2
        }

    def analyze_form(self, runner_data: Dict) -> Dict:
        """Analyze recent form and performance"""
        form_string = runner_data.get('form', '')
        score = 0
        consistency = 0
        trend = 'Unknown'
        
        if form_string:
            positions = []
            for char in form_string:
                if char.isdigit():
                    positions.append(int(char))
                elif char.upper() == 'W':
                    positions.append(1)
                    
            if positions:
                avg_pos = sum(positions) / len(positions)
                score = max(0, 20 - (avg_pos * 2))
                
                if len(positions) >= 3:
                    recent = positions[-3:]
                    if all(x <= y for x, y in zip(recent, recent[1:])):
                        trend = 'Improving'
                    elif all(x >= y for x, y in zip(recent, recent[1:])):
                        trend = 'Declining'
                    else:
                        trend = 'Mixed'
                        
                if len(positions) > 1:
                    consistency = 100 * (1 - np.std(positions) / max(positions))
        
        return {
            'form_score': round(score, 2),
            'consistency': round(consistency, 2),
            'trend': trend
        }

    def render_form_dashboard(self, runner_data: Dict):
        """Render comprehensive form analysis dashboard"""
        if not runner_data:
            st.warning("No runner data available")
            return

        # Performance Ratings Tab
        tabs = st.tabs([
            "Form Analysis",
            "Performance Trends",
            "Class Analysis",
            "Track Profile"
        ])

        with tabs[0]:
            self._render_form_analysis(runner_data)
        
        with tabs[1]:
            self._render_performance_trends(runner_data)
            
        with tabs[2]:
            self._render_class_analysis(runner_data)
            
        with tabs[3]:
            self._render_track_profile(runner_data)

    def _render_form_analysis(self, runner_data: Dict):
        """Render form analysis visualization"""
        st.subheader("Recent Form Analysis")
        
        # Calculate form metrics
        form_metrics = self.analyze_form(runner_data)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Form Score",
                f"{form_metrics['form_score']:.1f}",
                delta="8.5" if form_metrics['trend'] == 'Improving' else "-3.2"
            )
        
        with col2:
            st.metric(
                "Consistency",
                f"{form_metrics['consistency']:.1f}%"
            )
            
        with col3:
            st.metric(
                "Trend",
                form_metrics['trend']
            )
        
        # Form visualization
        st.subheader("Form Progression")
        dates = pd.date_range(end=pd.Timestamp.now(), periods=6, freq='W')
        form_data = pd.DataFrame({
            'Date': dates,
            'Position': [3, 2, 4, 1, 2, 1],
            'Rating': [75, 78, 72, 85, 82, 88]
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=form_data['Date'],
            y=form_data['Rating'],
            mode='lines+markers',
            name='Rating',
            line=dict(color='#1E3D59', width=2),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="Rating Progression",
            xaxis_title="Date",
            yaxis_title="Rating",
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def _render_performance_trends(self, runner_data: Dict):
        """Render performance trends visualization"""
        st.subheader("Performance Trends")
        
        # Sample performance data
        perf_data = pd.DataFrame({
            'Category': ['Speed', 'Stamina', 'Early Pace', 'Late Pace', 'Recovery'],
            'Current': [85, 75, 80, 70, 90],
            'Average': [80, 70, 75, 75, 85]
        })
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=perf_data['Current'],
            theta=perf_data['Category'],
            fill='toself',
            name='Current',
            line_color='#1E3D59'
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=perf_data['Average'],
            theta=perf_data['Category'],
            fill='toself',
            name='Average',
            line_color='#2B4F76'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def _render_class_analysis(self, runner_data: Dict):
        """Render class analysis visualization"""
        st.subheader("Class Analysis")
        
        # Sample class data
        class_data = pd.DataFrame({
            'Class': ['G1', 'G2', 'G3', 'Listed', 'Other'],
            'Runs': [2, 3, 5, 4, 8],
            'Wins': [1, 1, 2, 1, 3],
            'Places': [1, 2, 2, 2, 3],
            'Win Rate': [50, 33.3, 40, 25, 37.5]
        })
        
        fig = go.Figure(data=[
            go.Bar(
                name='Wins',
                x=class_data['Class'],
                y=class_data['Wins'],
                marker_color='#1E3D59'
            ),
            go.Bar(
                name='Places',
                x=class_data['Class'],
                y=class_data['Places'],
                marker_color='#2B4F76'
            )
        ])
        
        fig.update_layout(
            barmode='group',
            title="Performance by Class",
            xaxis_title="Class",
            yaxis_title="Count",
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def _render_track_profile(self, runner_data: Dict):
        """Render track profile visualization"""
        st.subheader("Track Profile")
        
        # Sample track data
        track_data = pd.DataFrame({
            'Track': ['Randwick', 'Flemington', 'Rosehill', 'Eagle Farm'],
            'Runs': [5, 4, 3, 2],
            'Wins': [2, 1, 1, 0],
            'Places': [2, 2, 1, 1],
            'Win Rate': [40, 25, 33.3, 0]
        })
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(
                track_data,
                values='Runs',
                names='Track',
                title='Runs by Track'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = go.Figure(data=[
                go.Bar(
                    x=track_data['Track'],
                    y=track_data['Win Rate'],
                    marker_color='#1E3D59'
                )
            ])
            
            fig.update_layout(
                title="Win Rate by Track",
                xaxis_title="Track",
                yaxis_title="Win Rate (%)",
                template="plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)
