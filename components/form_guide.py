import streamlit as st
import pandas as pd
from typing import Dict
import plotly.graph_objects as go

def render_form_guide(form_data: pd.DataFrame):
    """Render interactive form guide table"""
    
    st.subheader("Form Guide")
    
    # Add sorting functionality
    sort_col = st.selectbox("Sort by:", form_data.columns)
    ascending = st.checkbox("Ascending", value=False)
    
    sorted_data = form_data.sort_values(by=sort_col, ascending=ascending)
    
    # Create color conditions for ratings
    def color_rating(val):
        if val >= 80:
            return 'background-color: #90EE90'
        elif val >= 70:
            return 'background-color: #FFFFE0'
        else:
            return ''
    
    # Style the dataframe
    styled_df = sorted_data.style\
        .apply(lambda x: ['background-color: #F0F2F6' if i % 2 else '' 
                         for i in range(len(x))], axis=0)\
        .applymap(color_rating, subset=['Rating'])
    
    st.dataframe(styled_df, height=400)

def create_speed_map(form_data: pd.DataFrame) -> go.Figure:
    """Create interactive speed map visualization"""
    
    # Sort by barrier
    data = form_data.sort_values('Barrier')
    
    fig = go.Figure()
    
    # Add horses to their barriers
    fig.add_trace(go.Scatter(
        x=data['Barrier'],
        y=[1] * len(data),
        mode='markers+text',
        text=data['Horse'],
        textposition='top center',
        marker=dict(size=20, symbol='square'),
        name='Runners'
    ))
    
    # Customize layout
    fig.update_layout(
        title="Speed Map",
        xaxis_title="Barrier",
        yaxis_title="",
        yaxis_showticklabels=False,
        plot_bgcolor='white',
        width=800,
        height=400
    )
    
    return fig
