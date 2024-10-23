import streamlit as st
import pandas as pd
from typing import Dict
import plotly.graph_objects as go

def render_form_guide(form_data: pd.DataFrame):
    """Render interactive form guide table with enhanced styling"""
    
    st.subheader("Form Guide")
    
    # Add filters
    col1, col2 = st.columns([2, 1])
    with col1:
        sort_col = st.selectbox("Sort by:", form_data.columns)
    with col2:
        ascending = st.checkbox("Ascending", value=False)
    
    # Filter options
    filter_cols = st.multiselect(
        "Filter columns to display:",
        options=form_data.columns,
        default=form_data.columns
    )
    
    sorted_data = form_data.sort_values(by=sort_col, ascending=ascending)
    filtered_data = sorted_data[filter_cols]
    
    # Create color conditions for ratings and odds
    def style_dataframe(df):
        styles = []
        
        # Rating color scale
        def color_rating(val):
            if pd.isna(val):
                return ''
            if val >= 80:
                return 'background-color: #90EE90; color: black'
            elif val >= 70:
                return 'background-color: #FFFFE0; color: black'
            elif val >= 60:
                return 'background-color: #FFB6C1; color: black'
            return ''
        
        # Odds color scale
        def color_odds(val):
            if pd.isna(val) or val == 'N/A':
                return ''
            try:
                odds = float(val)
                if odds <= 3:
                    return 'background-color: #98FB98; color: black'
                elif odds <= 6:
                    return 'background-color: #F0E68C; color: black'
                return ''
            except:
                return ''
        
        # Apply styles
        styles.append(df.style
            .apply(lambda x: ['background-color: #F0F2F6' if i % 2 else '' 
                            for i in range(len(x))], axis=0)
            .applymap(color_rating, subset=['Rating'])
            .applymap(color_odds, subset=['Fixed Odds'] if 'Fixed Odds' in df.columns else [])
        )
        
        return styles[0]
    
    # Apply styling and display
    styled_df = style_dataframe(filtered_data)
    st.dataframe(
        styled_df,
        height=400,
        use_container_width=True
    )
    
    # Add download button
    csv = filtered_data.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Download Form Guide",
        csv,
        "form_guide.csv",
        "text/csv",
        key='download-form-guide'
    )

def create_speed_map(form_data: pd.DataFrame) -> go.Figure:
    """Create enhanced interactive speed map visualization"""
    
    # Sort by barrier
    data = form_data.sort_values('Barrier')
    
    fig = go.Figure()
    
    # Calculate marker colors based on ratings
    colors = ['#90EE90' if r >= 80 else '#FFFFE0' if r >= 70 else '#FFB6C1' 
              for r in data['Rating']]
    
    # Add horses to their barriers
    fig.add_trace(go.Scatter(
        x=data['Barrier'],
        y=[1] * len(data),
        mode='markers+text',
        text=data['Horse'],
        textposition='top center',
        marker=dict(
            size=30,
            symbol='square',
            color=colors,
            line=dict(color='black', width=1)
        ),
        name='Runners',
        hovertemplate="<br>".join([
            "Horse: %{text}",
            "Barrier: %{x}",
            "Rating: %{customdata[0]}",
            "Jockey: %{customdata[1]}"
        ]),
        customdata=list(zip(data['Rating'], data['Jockey']))
    ))
    
    # Customize layout
    fig.update_layout(
        title="Speed Map",
        xaxis_title="Barrier",
        yaxis_title="",
        yaxis_showticklabels=False,
        plot_bgcolor='white',
        showlegend=False,
        margin=dict(t=50, b=50, l=50, r=50)
    )
    
    # Add grid
    fig.update_xaxes(
        gridcolor='lightgrey',
        gridwidth=1,
        range=[0, max(data['Barrier']) + 1]
    )
    
    return fig
