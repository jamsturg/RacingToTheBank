import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

def add_filter_controls():
    st.subheader("Filter Options")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_rating = st.number_input("Minimum Rating", 0.0, 100.0, 0.0)
        min_win_rate = st.number_input("Minimum Win Rate (%)", 0.0, 100.0, 0.0)
    
    with col2:
        weight_range = st.slider("Weight Range (kg)", 50.0, 65.0, (50.0, 65.0))
        barrier_range = st.slider("Barrier Range", 1, 24, (1, 24))
    
    with col3:
        confidence_filter = st.multiselect(
            "Confidence Level",
            ["High", "Medium", "Low"],
            default=["High", "Medium", "Low"]
        )
        trend_filter = st.multiselect(
            "Performance Trend",
            ["Improving", "Stable", "Declining"],
            default=["Improving", "Stable", "Declining"]
        )
    
    if st.button("Reset Filters"):
        st.rerun()
    
    return {
        'min_rating': min_rating,
        'min_win_rate': min_win_rate,
        'weight_range': weight_range,
        'barrier_range': barrier_range,
        'confidence': confidence_filter,
        'trend': trend_filter
    }

def render_form_guide(form_data: pd.DataFrame):
    # Add default values for missing columns
    if form_data is not None and not form_data.empty:
        default_columns = {
            'confidence': 'Medium',
            'trend': 'Stable',
            'Rating': 0.0,
            'win_rate': 0.0
        }
        for col, default in default_columns.items():
            if col not in form_data.columns:
                form_data[col] = default
    else:
        st.warning("No form guide data available for this race.")
        return
        
    # Add filter controls
    filters = add_filter_controls()
    
    # Apply filters with error handling
    try:
        filtered_data = form_data.copy()
        
        # Apply filters with column existence checks
        filter_conditions = [
            (filtered_data['Rating'] >= filters['min_rating']),
            (filtered_data['win_rate'] >= filters['min_win_rate']),
            (filtered_data['Weight'].between(*filters['weight_range'])),
            (filtered_data['Barrier'].astype(float).between(*filters['barrier_range']))
        ]
        
        # Only add confidence filter if column exists
        if 'confidence' in filtered_data.columns:
            filter_conditions.append(filtered_data['confidence'].isin(filters['confidence']))
        
        # Only add trend filter if column exists
        if 'trend' in filtered_data.columns:
            filter_conditions.append(filtered_data['trend'].isin(filters['trend']))
        
        # Combine all filter conditions
        filtered_data = filtered_data[np.logical_and.reduce(filter_conditions)]
        
        if filtered_data.empty:
            st.warning("No horses match the selected filters.")
            return
    except Exception as e:
        st.error(f"Error applying filters: {str(e)}")
        return
        
    # Add statistical predictions and confidence levels
    st.subheader("Statistical Analysis")
    for _, row in filtered_data.iterrows():
        with st.expander(f"{row['Horse']} - Advanced Analysis"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("AI Rating", f"{row.get('rating', 0):.1f}")
                st.metric("Win Rate", f"{row.get('win_rate', 0)}%")
                st.metric("Best Distance", row.get('best_distance', 'Unknown'))
                
            with col2:
                st.metric("Confidence", row.get('confidence', 'Unknown'))
                st.metric("Place Rate", f"{row.get('place_rate', 0)}%")
                st.metric("Current Trend", row.get('trend', 'Unknown'))
                
            with col3:
                st.metric("Model Agreement", row.get('model_agreement', 'Unknown'))
                st.metric("Seasonal Effect", "Yes" if row.get('seasonal_effect', False) else "No")
                st.metric("Track Suitability", row.get('preferred_condition', 'Unknown'))
    
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
    
    # Add optional columns if they exist
    if 'confidence' in filtered_data.columns:
        display_columns.append('confidence')
    if 'trend' in filtered_data.columns:
        display_columns.append('trend')
    
    try:
        filtered_data = filtered_data[display_columns].copy()
    except KeyError as e:
        st.error(f"Form guide data structure mismatch. Missing column: {str(e)}")
        return
    
    # Add sorting options
    sort_col = st.selectbox("Sort by:", filtered_data.columns)
    ascending = st.checkbox("Ascending", value=False)
    
    sorted_data = filtered_data.sort_values(by=sort_col, ascending=ascending)
    
    # Style the dataframe with error handling
    try:
        styled_data = style_dataframe(sorted_data)
        st.dataframe(styled_data, height=400, use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying data: {str(e)}")
        st.dataframe(sorted_data, height=400, use_container_width=True)
    
    # Add download button with error handling
    try:
        csv = sorted_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download Form Guide",
            csv,
            "form_guide.csv",
            "text/csv",
            key='download-form-guide'
        )
    except Exception as e:
        st.error(f"Error creating download button: {str(e)}")

def style_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Style the dataframe with error handling"""
    try:
        styled = df.style.apply(
            lambda x: ['background-color: #F0F2F6' if i % 2 else '' 
                    for i in range(len(x))], 
            axis=0
        )
        
        # Apply confidence level colors if column exists
        if 'confidence' in df.columns:
            styled = styled.apply(lambda x: [
                'background-color: #90EE90' if v == 'High'
                else 'background-color: #FFFFE0' if v == 'Medium'
                else 'background-color: #FFB6C1' if v == 'Low'
                else '' for v in x
            ], subset=['confidence'])
        
        # Apply rating colors
        if 'Rating' in df.columns:
            styled = styled.apply(lambda x: [
                'background-color: #90EE90' if isinstance(v, (int, float)) and v >= 80
                else 'background-color: #FFFFE0' if isinstance(v, (int, float)) and v >= 70
                else 'background-color: #FFB6C1' if isinstance(v, (int, float))
                else '' for v in x
            ], subset=['Rating'])
        
        return styled
    except Exception as e:
        print(f"Error styling dataframe: {str(e)}")
        return df
