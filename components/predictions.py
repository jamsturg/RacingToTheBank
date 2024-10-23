import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List

def render_predictions(predictions: List[Dict]):
    """Render predictions table with confidence levels"""
    
    st.subheader("Race Predictions")
    
    # Create DataFrame from predictions
    pred_df = pd.DataFrame(predictions)
    
    # Style the predictions table
    def style_predictions(row):
        color = '#90EE90' if row.name == 0 else \
                '#FFFFE0' if row.name == 1 else \
                '#FFB6C1' if row.name == 2 else 'white'
        return [f'background-color: {color}'] * len(row)
    
    styled_preds = pred_df.style.apply(style_predictions, axis=1)
    
    st.dataframe(styled_preds, height=200)

def create_confidence_chart(predictions: List[Dict]) -> go.Figure:
    """Create confidence level visualization"""
    
    fig = go.Figure()
    
    horses = [p['horse'] for p in predictions[:3]]
    scores = [p['score'] for p in predictions[:3]]
    
    fig.add_trace(go.Bar(
        x=horses,
        y=scores,
        marker_color=['#90EE90', '#FFFFE0', '#FFB6C1'],
        text=scores,
        textposition='auto',
    ))
    
    fig.update_layout(
        title="Prediction Confidence",
        xaxis_title="Horse",
        yaxis_title="Score",
        plot_bgcolor='white',
        width=800,
        height=400
    )
    
    return fig
