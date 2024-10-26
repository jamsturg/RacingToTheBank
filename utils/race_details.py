import streamlit as st
from typing import Dict, Optional
from datetime import datetime
import pandas as pd

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

def render_race_details(race_data: Dict):
    """Render detailed race information panel"""
    if not race_data:
        st.warning("No race data available")
        return

    # Race header
    col1, col2 = st.columns([2,1])
    with col1:
        st.header(f"R{race_data.get('raceNumber')} {race_data.get('venueName')}")
    with col2:
        st.metric("Prize Money", f"${race_data.get('prizeMoney', 0):,}")

    # Race details tabs
    tab1, tab2, tab3 = st.tabs(["Overview", "Track Info", "Statistics"])
    
    with tab1:
        render_overview(race_data)
    
    with tab2:
        render_track_info(race_data)
        
    with tab3:
        render_statistics(race_data)

def render_overview(race_data: Dict):
    """Render race overview section"""
    cols = st.columns(3)
    
    with cols[0]:
        st.metric("Distance", f"{race_data.get('distance', 0)}m")
    with cols[1]:
        st.metric("Class", race_data.get('raceClass', 'N/A'))
    with cols[2]:
        st.metric("Runners", len(race_data.get('runners', [])))

    # Race description
    if description := race_data.get('raceDescription'):
        st.markdown(f"**Race Description:**\n{description}")

def render_track_info(race_data: Dict):
    """Render track information section"""
    cols = st.columns(2)
    
    with cols[0]:
        st.metric("Track Condition", race_data.get('trackCondition', 'N/A'))
        st.metric("Track Type", race_data.get('trackType', 'N/A'))
        
    with cols[1]:
        st.metric("Weather", race_data.get('weather', 'N/A'))
        st.metric("Rail Position", race_data.get('railPosition', 'N/A'))

    # Track bias visualization if plotly is available
    if track_bias := race_data.get('trackBias'):
        if HAS_PLOTLY:
            fig = go.Figure()
            
            # Add track bias indicators
            fig.add_trace(go.Indicator(
                mode = "gauge+number",
                value = track_bias.get('inside_advantage', 0),
                title = {'text': "Inside Advantage"},
                gauge = {
                    'axis': {'range': [-1, 1]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [-1, -0.3], 'color': 'red'},
                        {'range': [-0.3, 0.3], 'color': 'gray'},
                        {'range': [0.3, 1], 'color': 'green'}
                    ]
                }
            ))
            
            st.plotly_chart(fig)
        else:
            # Fallback to simple text display
            st.metric("Inside Advantage", 
                     f"{track_bias.get('inside_advantage', 0):.2f}",
                     help="Track bias indicator (-1 to 1)")

def render_statistics(race_data: Dict):
    """Render race statistics section"""
    # Create statistics from runners
    runners = race_data.get('runners', [])
    if not runners:
        st.warning("No runner statistics available")
        return
        
    stats_df = pd.DataFrame([{
        'Weight': float(r.get('weight', 0)),
        'Rating': float(r.get('rating', {}).get('value', 0)),
        'Last Start': r.get('lastStart', 'Unknown'),
        'Win Rate': float(r.get('statistics', {}).get('winRate', 0))
    } for r in runners])
    
    cols = st.columns(2)
    
    with cols[0]:
        st.metric("Avg Weight", f"{stats_df['Weight'].mean():.1f}kg")
        st.metric("Avg Rating", f"{stats_df['Rating'].mean():.1f}")
        
    with cols[1]:
        st.metric("Max Rating", f"{stats_df['Rating'].max():.1f}")
        st.metric("Avg Win Rate", f"{stats_df['Win Rate'].mean():.1f}%")

    # Create rating distribution chart if plotly is available
    if HAS_PLOTLY:
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=stats_df['Rating'],
            nbinsx=10,
            name='Rating Distribution'
        ))
        fig.update_layout(
            title='Runner Ratings Distribution',
            xaxis_title='Rating',
            yaxis_title='Count'
        )
        st.plotly_chart(fig)
    else:
        # Fallback to basic statistics
        st.write("Rating Distribution:")
        st.write(f"Min: {stats_df['Rating'].min():.1f}")
        st.write(f"Max: {stats_df['Rating'].max():.1f}")
        st.write(f"Mean: {stats_df['Rating'].mean():.1f}")
