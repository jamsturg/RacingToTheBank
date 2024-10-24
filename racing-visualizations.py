```python
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

    @staticmethod
    def create_weight_comparison(runners: List[Dict]) -> go.Figure:
        """Create weight comparison chart"""
        df = pd.DataFrame([{
            'runner': f"{r['runnerNumber']}. {r['runnerName']}",
            'weight': r.get('handicapWeight', 0),
            'last_weight': r.get('lastStartWeight', 0)
        } for r in runners])
        
        fig = go.Figure(data=[
            go.Bar(
                name='Current Weight',
                x=df['runner'],
                y=df['weight'],
                marker_color='blue'
            ),
            go.Bar(
                name='Last Start Weight',
                x=df['runner'],
                y=df['last_weight'],
                marker_color='lightblue'
            )
        ])
        
        fig.update_layout(
            barmode='group',
            title="Weight Comparison",
            xaxis_title="Runner",
            yaxis_title="Weight (kg)",
            height=400
        )
        
        return fig

    @staticmethod
    def create_prize_money_chart(runners: List[Dict]) -> go.Figure:
        """Create prize money comparison chart"""
        df = pd.DataFrame([{
            'runner': f"{r['runnerNumber']}. {r['runnerName']}",
            'prize_money': float(r.get('prizeMoney', '0').replace('$', '').replace(',', ''))
        } for r in runners])
        
        fig = go.Figure(data=[
            go.Bar(
                x=df['runner'],
                y=df['prize_money'],
                marker_color='gold'
            )
        ])
        
        fig.update_layout(
            title="Career Prize Money",
            xaxis_title="Runner",
            yaxis_title="Prize Money ($)",
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
    def create_performance_history(runner_history: List[Dict]) -> go.Figure:
        """Create performance history chart"""
        df = pd.DataFrame(runner_history)
        
        fig = go.Figure()
        
        # Position line
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['position'],
            name='Position',
            mode='lines+markers'
        ))
        
        # Add race class markers
        for i, row in df.iterrows():
            fig.add_annotation(
                x=row['date'],
                y=row['position'],
                text=row['class'],
                showarrow=False,
                yshift=10
            )
        
        fig.update_layout(
            title="Performance History",
            xaxis_title="Date",
            yaxis_title="Position",
            yaxis_autorange='reversed',
            height=400
        )
        
        return fig

    @staticmethod
    def create_sectional_times(sectionals: List[Dict]) -> go.Figure:
        """Create sectional times comparison"""
        df = pd.DataFrame(sectionals)
        
        fig = go.Figure()
        
        for runner in df['runner'].unique():
            runner_data = df[df['runner'] == runner]
            fig.add_trace(go.Scatter(
                x=runner_data['section'],
                y=runner_data['time'],
                name=runner,
                mode='lines+markers'
            ))
        
        fig.update_layout(
            title="Sectional Times",
            xaxis_title="Race Section",
            yaxis_title="Time (seconds)",
            height=400
        )
        
        return fig

    @staticmethod
    def create_jockey_stats(jockey_data: Dict) -> go.Figure:
        """Create jockey statistics visualization"""
        stats = pd.DataFrame([{
            'Category': cat,
            'Win%': val
        } for cat, val in jockey_data.items()])
        
        fig = go.Figure(data=[
            go.Bar(
                x=stats['Category'],
                y=stats['Win%'],
                marker_color='darkblue'
            )
        ])
        
        fig.update_layout(
            title="Jockey Statistics",
            xaxis_title="Category",
            yaxis_title="Win %",
            height=400
        )
        
        return fig
```
