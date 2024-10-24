```python
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from .helpers import format_odds

def create_speed_map(runners: List[Dict]) -> go.Figure:
    """Create interactive speed map visualization"""
    # Track layout
    track_sections = ['0-400m', '400-800m', '800-1200m', '1200m+']
    positions = ['Inside', 'Mid', 'Outside']
    
    # Initialize position matrix
    position_matrix = np.zeros((len(positions), len(track_sections)))
    
    # Map runners to positions
    for runner in runners:
        if 'run_style' in runner:
            position_idx = {
                'Leader': 0,
                'On pace': 1,
                'Midfield': 2,
                'Back': 3
            }.get(runner['run_style'], 2)
            
            for i in range(len(track_sections)):
                position_matrix[position_idx % 3][i] += 1

    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=position_matrix,
        x=track_sections,
        y=positions,
        colorscale='Viridis',
        showscale=False
    ))

    # Add runner annotations
    for i, runner in enumerate(runners):
        pos_x = i % len(track_sections)
        pos_y = (i // len(track_sections)) % len(positions)
        
        fig.add_annotation(
            x=track_sections[pos_x],
            y=positions[pos_y],
            text=f"{runner['number']}. {runner['name']}",
            showarrow=False,
            font=dict(size=10)
        )

    fig.update_layout(
        title="Speed Map",
        xaxis_title="Race Section",
        yaxis_title="Track Position",
        height=400
    )

    return fig

def create_form_chart(runner_data: Dict) -> go.Figure:
    """Create comprehensive form visualization"""
    if 'form' not in runner_data:
        return go.Figure()

    # Create subplots for multiple metrics
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Position History",
            "Distance Performance",
            "Track Performance",
            "Class Performance"
        )
    )

    # Position history
    positions = [int(pos) for pos in runner_data['form'].split('-')]
    dates = [(datetime.now() - timedelta(days=i*14)) for i in range(len(positions)-1, -1, -1)]
    
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=positions,
            mode='lines+markers',
            name='Position'
        ),
        row=1, col=1
    )
    fig.update_yaxes(autorange="reversed", row=1, col=1)

    # Distance performance
    if 'distance_stats' in runner_data:
        distances = list(runner_data['distance_stats'].keys())
        win_rates = [stats['win_rate'] for stats in runner_data['distance_stats'].values()]
        
        fig.add_trace(
            go.Bar(
                x=distances,
                y=win_rates,
                name='Win Rate'
            ),
            row=1, col=2
        )

    # Track performance
    if 'track_stats' in runner_data:
        tracks = list(runner_data['track_stats'].keys())
        track_rates = [stats['win_rate'] for stats in runner_data['track_stats'].values()]
        
        fig.add_trace(
            go.Bar(
                x=tracks,
                y=track_rates,
                name='Track Win Rate'
            ),
            row=2, col=1
        )

    # Class performance
    if 'class_stats' in runner_data:
        classes = list(runner_data['class_stats'].keys())
        class_rates = [stats['win_rate'] for stats in runner_data['class_stats'].values()]
        
        fig.add_trace(
            go.Bar(
                x=classes,
                y=class_rates,
                name='Class Win Rate'
            ),
            row=2, col=2
        )

    fig.update_layout(
        height=800,
        showlegend=False,
        title_text="Form Analysis"
    )

    return fig

def create_odds_movement_chart(odds_history: List[Dict]) -> go.Figure:
    """Create odds movement visualization"""
    fig = go.Figure()

    # Group by runner
    df = pd.DataFrame(odds_history)
    
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
        yaxis_title="Odds ($)",
        height=400,
        hovermode='x unified'
    )

    return fig

def create_roi_chart(bets: List[Dict]) -> go.Figure:
    """Create ROI and performance visualization"""
    fig = make_subplots(
        rows=2,
        cols=1,
        subplot_titles=("Cumulative ROI", "Bet Outcomes")
    )

    # Calculate cumulative ROI
    df = pd.DataFrame(bets)
    df['profit'] = df.apply(
        lambda x: x.get('return_amount', 0) - x['stake']
        if x['result'] == 'Won' else -x['stake'],
        axis=1
    )
    df['cumulative_profit'] = df['profit'].cumsum()
    df['roi'] = (df['cumulative_profit'] / df['stake'].cumsum()) * 100

    # ROI line
    fig.add_trace(
        go.Scatter(
            x=df['placed_at'],
            y=df['roi'],
            mode='lines',
            name='ROI %'
        ),
        row=1, col=1
    )

    # Outcome distribution
    outcomes = df['result'].value_counts()
    fig.add_trace(
        go.Pie(
            labels=outcomes.index,
            values=outcomes.values,
            name='Outcomes'
        ),
        row=2, col=1
    )

    fig.update_layout(
        height=800,
        showlegend=True
    )

    return fig

def create_bankroll_chart(balance_history: List[Dict]) -> go.Figure:
    """Create bankroll history visualization"""
    df = pd.DataFrame(balance_history)
    
    fig = go.Figure()

    # Balance line
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['balance'],
        mode='lines',
        name='Balance',
        fill='tozeroy'
    ))

    # Add markers for significant events
    deposits = df[df['type'] == 'deposit']
    withdrawals = df[df['type'] == 'withdrawal']
    
    fig.add_trace(go.Scatter(
        x=deposits['timestamp'],
        y=deposits['balance'],
        mode='markers',
        name='Deposits',
        marker=dict(
            symbol='triangle-up',
            size=12,
            color='green'
        )
    ))
    
    fig.add_trace(go.Scatter(
        x=withdrawals['timestamp'],
        y=withdrawals['balance'],
        mode='markers',
        name='Withdrawals',
        marker=dict(
            symbol='triangle-down',
            size=12,
            color='red'
        )
    ))

    fig.update_layout(
        title="Bankroll History",
        xaxis_title="Date",
        yaxis_title="Balance ($)",
        height=400,
        hovermode='x unified'
    )

    return fig

def create_comparison_radar(runner1: Dict, runner2: Dict) -> go.Figure:
    """Create radar chart comparing two runners"""
    categories = ['Speed', 'Form', 'Class', 'Distance', 'Track']
    
    fig = go.Figure()

    # Add runner 1
    fig.add_trace(go.Scatterpolar(
        r=[
            runner1.get('speed_rating', 0),
            runner1.get('form_rating', 0),
            runner1.get('class_rating', 0),
            runner1.get('distance_rating', 0),
            runner1.get('track_rating', 0)
        ],
        theta=categories,
        fill='toself',
        name=runner1['name']
    ))

    # Add runner 2
    fig.add_trace(go.Scatterpolar(
        r=[
            runner2.get('speed_rating', 0),
            runner2.get('form_rating', 0),
            runner2.get('class_rating', 0),
            runner2.get('distance_rating', 0),
            runner2.get('track_rating', 0)
        ],
        theta=categories,
        fill='toself',
        name=runner2['name']
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        title="Runner Comparison"
    )

    return fig

def create_track_bias_heatmap(track_data: Dict) -> go.Figure:
    """Create track bias heatmap visualization"""
    # Track sections and positions
    sections = ['Start', 'Back Straight', 'Turn', 'Home Straight']
    positions = ['Inside', 'Middle', 'Outside']

    # Create bias matrix
    bias_matrix = np.array([
        [track_data.get(f"{pos}_{sec}", 0) 
         for sec in sections]
        for pos in positions
    ])

    fig = go.Figure(data=go.Heatmap(
        z=bias_matrix,
        x=sections,
        y=positions,
        colorscale='RdYlBu',
        colorbar_title="Bias Score"
    ))

    fig.update_layout(
        title="Track Bias Analysis",
        xaxis_title="Track Section",
        yaxis_title="Running Position",
        height=400
    )

    return fig

def create_betting_patterns_chart(betting_data: List[Dict]) -> go.Figure:
    """Create betting patterns visualization"""
    df = pd.DataFrame(betting_data)
    
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Bet Type Distribution",
            "Odds Range Performance",
            "Time of Day Analysis",
            "Day of Week Performance"
        )
    )

    # Bet type distribution
    bet_types = df['bet_type'].value_counts()
    fig.add_trace(
        go.Pie(
            labels=bet_types.index,
            values=bet_types.values,
            name='Bet Types'
        ),
        row=1, col=1
    )

    # Odds range performance
    df['odds_range'] = pd.cut(
        df['odds'],
        bins=[0, 2, 5, 10, 20, float('inf')],
        labels=['1-2', '2-5', '5-10', '10-20', '20+']
    )
    odds_performance = df.groupby('odds_range')['profit'].mean()
    
    fig.add_trace(
        go.Bar(
            x=odds_performance.index,
            y=odds_performance.values,
            name='Odds Performance'
        ),
        row=1, col=2
    )

    # Time of day analysis
    df['hour'] = df['placed_at'].dt.hour
    hourly_performance = df.groupby('hour')['profit'].mean()
    
    fig.add_trace(
        go.Scatter(
            x=hourly_performance.index,
            y=hourly_performance.values,
            mode='lines+markers',
            name='Hourly Performance'
        ),
        row=2, col=1
    )

    # Day of week performance
    df['day'] = df['placed_at'].dt.day_name()
    daily_performance = df.groupby('day')['profit'].mean()
    
    fig.add_trace(
        go.Bar(
            x=daily_performance.index,
            y=daily_performance.values,
            name='Daily Performance'
        ),
        row=2, col=2
    )

    fig.update_layout(
        height=800,
        showlegend=True
    )

    return fig
```

This visualization module provides:

1. Race Analysis:
- Speed map visualization
- Form analysis charts
- Track bias heatmaps
- Runner comparisons

2. Betting Analysis:
- Odds movement tracking
- ROI visualization
- Bankroll history
- Betting patterns

3. Performance Analysis:
- Time-based analysis
- Outcome distributions
- Pattern recognition
- Comparative analysis

Would you like me to:
1. Continue with betting strategies implementation?
2. Add more visualization types?
3. Add helper functions?
4. Add statistical analysis tools?
5. Add real-time visualization updates?