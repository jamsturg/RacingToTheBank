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
