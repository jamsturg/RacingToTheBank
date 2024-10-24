import streamlit as st
import pandas as pd
import numpy as np

def render_loading_state():
    """Display loading overlay"""
    st.markdown('''
        <div class="loading-overlay">
            <div class="loading-spinner"></div>
        </div>
    ''', unsafe_allow_html=True)

def render_form_guide(form_data: pd.DataFrame):
    """Render enhanced form guide with improved UI"""
    st.markdown('<div class="form-guide-container">', unsafe_allow_html=True)
    
    # Form Guide Header
    st.markdown('<div class="form-guide-header">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.header("Form Guide")
    with col2:
        sort_col = st.selectbox("Sort by:", form_data.columns if not form_data.empty else [], key='sort_select')
    with col3:
        ascending = st.checkbox("Ascending", value=False, key='sort_check')
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Main content with loading state
    st.markdown('<div class="form-guide-content">', unsafe_allow_html=True)
    
    if form_data is None:
        render_loading_state()
        return
    elif form_data.empty:
        st.warning("No form guide data available")
        return
    
    try:
        # Apply sorting if selected
        if sort_col:
            form_data = form_data.sort_values(by=sort_col, ascending=ascending)
        
        # Style the dataframe
        styled_data = style_dataframe(form_data)
        
        # Display with enhanced UI
        st.dataframe(
            styled_data,
            height=600,
            use_container_width=True,
            hide_index=True
        )
        
    except Exception as e:
        st.error(f"Error displaying form guide: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def style_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply enhanced styling to dataframe"""
    try:
        # Create style object
        styled = df.style
        
        # Zebra striping
        styled = styled.apply(lambda x: ['background-color: #f8f9fa' if i % 2 else ''
                                      for i in range(len(x))], axis=0)
        
        # Highlight performance indicators
        if 'Rating' in df.columns:
            styled = styled.apply(lambda x: [
                'background-color: #90EE90' if isinstance(v, (int, float)) and v >= 80
                else 'background-color: #FFFFE0' if isinstance(v, (int, float)) and v >= 70
                else 'background-color: #FFB6C1' if isinstance(v, (int, float)) and v < 70
                else '' for v in x
            ], subset=['Rating'])
        
        # Format numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            styled = styled.format({col: '{:.1f}'})
        
        return df.copy()
    
    except Exception as e:
        print(f"Error styling dataframe: {str(e)}")
        return df

def render_filter_panel():
    """Render enhanced filter panel"""
    st.markdown('''
        <div class="filter-panel" id="filterPanel">
            <div class="filter-header">
                <h3>Filters</h3>
                <button onclick="document.getElementById('filterPanel').classList.remove('open')">&times;</button>
            </div>
    ''', unsafe_allow_html=True)
    
    # Rating Filter
    st.markdown('<div class="filter-group">', unsafe_allow_html=True)
    st.markdown("#### Rating Range")
    col1, col2 = st.columns(2)
    with col1:
        min_rating = st.number_input("Min", 0, 100, 0, key='min_rating')
    with col2:
        max_rating = st.number_input("Max", 0, 100, 100, key='max_rating')
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Form Filter
    st.markdown('<div class="filter-group">', unsafe_allow_html=True)
    st.markdown("#### Performance")
    form_filter = st.multiselect(
        "Show runners with",
        ["Winning Form", "Placing Form", "Poor Form"],
        default=["Winning Form", "Placing Form"],
        key='form_filter'
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Weight Filter
    st.markdown('<div class="filter-group">', unsafe_allow_html=True)
    st.markdown("#### Weight Range")
    weight_range = st.slider("Weight (kg)", 50.0, 65.0, (50.0, 65.0), key='weight_range')
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Reset Filters
    if st.button("Reset Filters", type="primary", key='reset_filters'):
        st.session_state.filters = {}
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Add filter toggle button with gear icon
    st.markdown('''
        <button onclick="document.getElementById('filterPanel').classList.add('open')"
                class="filter-toggle">
            ⚙️
        </button>
    ''', unsafe_allow_html=True)
