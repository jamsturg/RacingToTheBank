import plotly.graph_objects as go
from typing import Dict

def create_track_bias_chart(track_bias: Dict) -> go.Figure:
    """Create track bias visualization"""
    barrier_data = track_bias.get('barrier_bias', {})
    
    fig = go.Figure()
    
    if not barrier_data:
        fig.add_annotation(
            text="No track bias data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        return fig
    
    # Add barrier bias trace
    fig.add_trace(go.Bar(
        x=list(barrier_data.keys()),
        y=list(barrier_data.values()),
        name='Barrier Bias',
        marker_color=['#90EE90' if v > 0 else '#FFB6C1' for v in barrier_data.values()]
    ))
    
    fig.update_layout(
        title='Track Bias Analysis',
        xaxis_title='Barrier',
        yaxis_title='Bias Factor',
        plot_bgcolor='white',
        showlegend=False,
        margin=dict(t=50, b=50, l=50, r=50)
    )
    
    fig.update_xaxes(
        gridcolor='lightgrey',
        gridwidth=1
    )
    
    fig.update_yaxes(
        gridcolor='lightgrey',
        gridwidth=1
    )
    
    return fig
