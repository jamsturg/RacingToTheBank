import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def render_form_guide(form_data: pd.DataFrame):
    """Render interactive form guide table with enhanced styling"""
    
    # Filter columns to display
    display_columns = [
        'Horse',
        'Barrier',
        'Weight',
        'Jockey',
        'Form',
        'Rating',
        'Fixed Odds'
    ]
    
    filtered_data = form_data[display_columns].copy()
    
    # Add sorting options
    sort_col = st.selectbox("Sort by:", display_columns)
    ascending = st.checkbox("Ascending", value=False)
    
    sorted_data = filtered_data.sort_values(by=sort_col, ascending=ascending)
    
    # Style the dataframe
    def style_dataframe(df):
        def rating_color(val):
            if pd.isna(val):
                return ''
            if val >= 80:
                return 'background-color: #90EE90; color: black'  # Green
            elif val >= 70:
                return 'background-color: #FFFFE0; color: black'  # Yellow
            else:
                return 'background-color: #FFB6C1; color: black'  # Red
        
        return df.style\
            .apply(lambda x: ['background-color: #F0F2F6' if i % 2 else '' 
                            for i in range(len(x))], axis=0)\
            .applymap(rating_color, subset=['Rating'])
    
    # Display styled dataframe
    st.dataframe(
        style_dataframe(sorted_data),
        height=400,
        use_container_width=True
    )
    
    # Add download button
    csv = sorted_data.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Download Form Guide",
        csv,
        "form_guide.csv",
        "text/csv",
        key='download-form-guide'
    )

def create_speed_map(form_data: pd.DataFrame) -> go.Figure:
    """Create interactive speed map visualization"""
    
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
