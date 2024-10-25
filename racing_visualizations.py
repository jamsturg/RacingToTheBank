import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict
import numpy as np

class RacingVisualizations:
    @staticmethod
    def create_speed_map(runners: List[Dict]) -> go.Figure:
        """Create interactive speed map visualization"""
        positions = ['Inside', 'Mid', 'Outside']
        sections = ['Early', 'Middle', 'Late']
        
        # Create position matrix
        position_matrix = np.random.randint(1, len(runners) + 1, (len(positions), len(sections)))
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=position_matrix,
            x=sections,
            y=positions,
            colorscale='Viridis',
            showscale=False
        ))
        
        # Add runner annotations
        for i, runner in enumerate(runners, 1):
            positions = np.where(position_matrix == i)
            if len(positions[0]) > 0:
                fig.add_annotation(
                    x=sections[positions[1][0]],
                    y=positions[0][0],
                    text=f"{i}. {runner['runnerName']}",
                    showarrow=False
                )
        
        fig.update_layout(
            title="Predicted Running Positions",
            xaxis_title="Race Section",
            yaxis_title="Track Position",
            height=400
        )
        
        return fig

    @staticmethod
    def create_track_bias(track_data: Dict) -> go.Figure:
        """Create track bias visualization"""
        sections = ['0-400m', '400-800m', '800-1200m', '1200m+']
        positions = ['Inside', 'Middle', 'Outside']
        
        bias_matrix = np.random.uniform(0, 1, (len(positions), len(sections)))
        
        fig = go.Figure(data=go.Heatmap(
            z=bias_matrix,
            x=sections,
            y=positions,
            colorscale='RdYlGn',
            showscale=True
        ))
        
        fig.update_layout(
            title="Track Bias Analysis",
            xaxis_title="Race Section",
            yaxis_title="Track Position",
            height=400
        )
        
        return fig

    @staticmethod
    def create_odds_movement(odds_history: List[Dict]) -> go.Figure:
        """Create odds movement chart"""
        df = pd.DataFrame(odds_history)
        
        fig = go.Figure()
        
        for runner in df['runner'].unique():
            runner_data = df[df['runner'] == runner]
            fig.add_trace(go.Scatter(
                x=runner_data['timestamp'],
                y=runner_data['odds'],
                name=runner,
                mode='lines+markers'
            ))
        
        fig.update_layout(
            title="Odds Movement",
            xaxis_title="Time",
            yaxis_title="Fixed Odds ($)",
            height=400,
            legend_title="Runners"
        )
        
        return fig

    @staticmethod
    def create_horse_network(race_data: Dict):
        """Create simple relationship visualization without networkx"""
        fig = go.Figure()
        
        # Create nodes for horses
        horse_x, horse_y = [], []
        horse_text = []
        for i, runner in enumerate(race_data['runners']):
            horse_x.append(0)
            horse_y.append(i)
            horse_text.append(runner['runnerName'])
        
        # Add horse nodes
        fig.add_trace(go.Scatter(
            x=horse_x,
            y=horse_y,
            mode='markers+text',
            name='Horses',
            text=horse_text,
            textposition='middle right',
            marker=dict(size=15, color='blue')
        ))
        
        fig.update_layout(
            title="Race Connections",
            showlegend=True,
            height=400,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        return fig

    @staticmethod
    def create_form_radar(runner_stats: Dict) -> go.Figure:
        """Create runner form radar chart"""
        categories = ['Speed', 'Form', 'Class', 'Distance', 'Track']
        
        fig = go.Figure(data=go.Scatterpolar(
            r=[
                runner_stats.get('speed_rating', 0),
                runner_stats.get('form_rating', 0),
                runner_stats.get('class_rating', 0),
                runner_stats.get('distance_rating', 0),
                runner_stats.get('track_rating', 0)
            ],
            theta=categories,
            fill='toself'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=False,
            height=400
        )
        
        return fig
