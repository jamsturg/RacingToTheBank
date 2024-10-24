import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def render_form_guide(form_data: pd.DataFrame):
    if form_data.empty:
        st.warning("No form guide data available for this race.")
        return
        
    # Add historical performance metrics
    st.subheader("Historical Performance")
    for _, row in form_data.iterrows():
        with st.expander(f"{row['Horse']} - Historical Analysis"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Win Rate", f"{row.get('win_rate', 0)}%")
                st.metric("Best Distance", row.get('best_distance', 'Unknown'))
                
            with col2:
                st.metric("Place Rate", f"{row.get('place_rate', 0)}%")
                st.metric("Current Trend", row.get('trend', 'Unknown'))
                
            with col3:
                st.metric("Avg Position", row.get('avg_position', 0))
                st.metric("Preferred Track", row.get('preferred_condition', 'Unknown'))
        
    # Filter columns to display
    display_columns = [
        'Number',
        'Horse',
        'Barrier', 
        'Weight',
        'Jockey',
        'Form',
        'Rating'
    ]
    
    try:
        filtered_data = form_data[display_columns].copy()
    except KeyError:
        st.error("Form guide data structure mismatch. Please try another race.")
        return
    
    # Add sorting options
    sort_col = st.selectbox("Sort by:", filtered_data.columns)
    ascending = st.checkbox("Ascending", value=False)
    
    sorted_data = filtered_data.sort_values(by=sort_col, ascending=ascending)
    
    # Style the dataframe with error handling
    def style_dataframe(df):
        try:
            styled = df.style.apply(
                lambda x: ['background-color: #F0F2F6' if i % 2 else '' 
                        for i in range(len(x))], 
                axis=0
            )
            
            # Apply rating colors only if Rating column exists
            if 'Rating' in df.columns:
                styled = styled.apply(lambda x: [
                    'background-color: #90EE90' if isinstance(v, (int, float)) and v >= 80
                    else 'background-color: #FFFFE0' if isinstance(v, (int, float)) and v >= 70
                    else 'background-color: #FFB6C1' if isinstance(v, (int, float))
                    else '' for v in x
                ], subset=['Rating'])
            
            return styled
        except Exception as e:
            st.error(f"Error styling data: {str(e)}")
            return df
    
    st.subheader("Form Guide")
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
    # Create figure
    fig = go.Figure()
    
    # Handle empty data case
    if form_data.empty:
        fig.add_annotation(
            text="No data available for speed map",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        fig.update_layout(
            xaxis_title="Barrier",
            yaxis_title="",
            yaxis_showticklabels=False,
            plot_bgcolor='white',
            showlegend=False,
            height=400
        )
        return fig
    
    # Ensure required columns exist
    required_columns = ['Horse', 'Barrier', 'Rating', 'Jockey']
    if not all(col in form_data.columns for col in required_columns):
        fig.add_annotation(
            text="Missing required data for speed map",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        return fig
    
    # Convert barriers to numeric, handling any non-numeric values
    data = form_data.copy()
    data['Barrier'] = pd.to_numeric(data['Barrier'], errors='coerce')
    data = data.dropna(subset=['Barrier'])
    
    if data.empty:
        fig.add_annotation(
            text="No valid barrier data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        return fig
    
    # Sort by barrier
    data = data.sort_values('Barrier')
    
    # Ensure Rating is numeric
    data['Rating'] = pd.to_numeric(data['Rating'], errors='coerce').fillna(0)
    
    # Calculate marker colors
    colors = ['#90EE90' if r >= 80 else '#FFFFE0' if r >= 70 else '#FFB6C1' 
              for r in data['Rating']]
    
    # Add horses to their barriers with error handling
    try:
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
            customdata=list(zip(
                data['Rating'].round(1),
                data['Jockey'].fillna('Unknown')
            ))
        ))
    except Exception as e:
        print(f"Error creating speed map trace: {str(e)}")
        return fig
    
    # Update layout with safe barrier range
    try:
        max_barrier = int(data['Barrier'].max())
        fig.update_layout(
            xaxis_title="Barrier",
            yaxis_title="",
            yaxis_showticklabels=False,
            plot_bgcolor='white',
            showlegend=False,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        fig.update_xaxes(
            gridcolor='lightgrey',
            gridwidth=1,
            range=[0, max_barrier + 1]
        )
    except Exception as e:
        print(f"Error updating speed map layout: {str(e)}")
    
    return fig
