import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List
import asyncio
import logging
from pathlib import Path
import json
import time
from sklearn.preprocessing import StandardScaler

# Import custom components
from advanced_racing_predictor import AdvancedRacingPredictor
from advanced_analytics import AdvancedStatistics
from advanced_form_analysis import FormAnalysis
from account_management import AccountManager
from tab_api_client import TABApiClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RacingDashboard:
    def __init__(self):
        # Configure page
        st.set_page_config(
            page_title="To The Bank",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Custom CSS with improved styling and mobile responsiveness
        st.markdown("""
            <style>
            /* Global styles */
            .stApp {
                background-color: #1E3D59;
                color: white;
            }
            
            /* Main header */
            .main-header {
                background-color: #2B4F76;
                padding: 2rem;
                border-radius: 10px;
                margin-bottom: 2rem;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            
            .main-header h1 {
                color: white !important;
                font-size: 2.5rem;
                font-weight: bold;
                margin: 0;
            }
            
            /* Sidebar */
            [data-testid="stSidebar"] {
                background-color: #2B4F76;
                border-right: 1px solid rgba(255,255,255,0.1);
            }
            
            [data-testid="stSidebar"] [data-testid="stMarkdown"] {
                color: white;
            }
            
            /* Navigation */
            .stRadio > label {
                color: white !important;
                font-weight: 500;
            }
            
            .stRadio > div {
                color: white !important;
            }
            
            /* Metric cards */
            [data-testid="stMetricValue"] {
                background-color: #2B4F76;
                padding: 1rem;
                border-radius: 10px;
                color: white !important;
                font-weight: bold;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            [data-testid="stMetricDelta"] {
                color: #4CAF50 !important;
            }
            
            /* Tables */
            .stDataFrame {
                background-color: #2B4F76 !important;
            }
            
            .stDataFrame [data-testid="stTable"] {
                color: white !important;
            }
            
            /* Buttons */
            .stButton > button {
                background-color: #4CAF50 !important;
                color: white !important;
                border: none !important;
                padding: 0.5rem 1rem !important;
                border-radius: 5px !important;
                font-weight: 500 !important;
                transition: all 0.3s ease !important;
            }
            
            .stButton > button:hover {
                background-color: #45a049 !important;
                transform: translateY(-1px);
            }
            
            /* Forms */
            .stForm {
                background-color: #2B4F76;
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            
            /* Inputs */
            .stTextInput > div > div > input,
            .stNumberInput > div > div > input {
                background-color: rgba(255,255,255,0.1) !important;
                color: white !important;
                border: 1px solid rgba(255,255,255,0.2) !important;
            }
            
            /* Select boxes */
            .stSelectbox > div > div {
                background-color: rgba(255,255,255,0.1) !important;
                color: white !important;
                border: 1px solid rgba(255,255,255,0.2) !important;
            }
            
            /* Tabs */
            .stTabs [data-baseweb="tab-list"] {
                background-color: #2B4F76 !important;
                padding: 0.5rem !important;
                border-radius: 10px !important;
                gap: 0.5rem !important;
            }
            
            .stTabs [data-baseweb="tab"] {
                background-color: transparent !important;
                color: white !important;
                border: 1px solid rgba(255,255,255,0.2) !important;
                border-radius: 5px !important;
                padding: 0.5rem 1rem !important;
            }
            
            .stTabs [data-baseweb="tab"][aria-selected="true"] {
                background-color: #4CAF50 !important;
                border-color: #4CAF50 !important;
            }
            
            /* Charts */
            .js-plotly-plot {
                background-color: #2B4F76 !important;
                border-radius: 10px !important;
                padding: 1rem !important;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
            }
            
            /* Expander */
            .streamlit-expanderHeader {
                background-color: #2B4F76 !important;
                color: white !important;
                border-radius: 5px !important;
            }
            
            /* Footer */
            footer {
                background-color: #2B4F76;
                color: white;
                text-align: center;
                padding: 1rem;
                position: fixed;
                bottom: 0;
                width: 100%;
                box-shadow: 0 -4px 6px rgba(0,0,0,0.1);
            }
            
            footer a {
                color: #4CAF50 !important;
                text-decoration: none;
            }
            
            /* Headings */
            h1, h2, h3, h4, h5, h6 {
                color: white !important;
            }
            
            /* Text */
            p, span, label {
                color: white !important;
            }
            
            /* Success messages */
            .stSuccess {
                background-color: #4CAF50 !important;
                color: white !important;
            }
            
            /* Error messages */
            .stError {
                background-color: #f44336 !important;
                color: white !important;
            }
            
            /* Mobile Responsiveness */
            @media (max-width: 768px) {
                .main-header h1 {
                    font-size: 1.8rem;
                }
                
                [data-testid="stMetricValue"] {
                    font-size: 1.2rem !important;
                    padding: 0.5rem !important;
                }
                
                .stTabs [data-baseweb="tab"] {
                    padding: 0.3rem 0.6rem !important;
                    font-size: 0.9rem !important;
                }
                
                .stDataFrame {
                    font-size: 0.9rem !important;
                }
                
                /* Improve touch targets */
                .stSelectbox > div > div,
                .stButton > button,
                .streamlit-expanderHeader {
                    min-height: 44px !important;
                }
                
                /* Better spacing for mobile */
                .stForm {
                    padding: 1rem !important;
                }
                
                /* Adjust chart sizes */
                .js-plotly-plot {
                    height: 300px !important;
                }
            }
            
            /* Interactive Form Guide Enhancements */
            .form-guide-card {
                background-color: #2B4F76;
                border-radius: 10px;
                padding: 1rem;
                margin-bottom: 1rem;
                transition: transform 0.2s;
                cursor: pointer;
            }
            
            .form-guide-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            
            /* Interactive Tooltips */
            .tooltip {
                position: relative;
                display: inline-block;
            }
            
            .tooltip .tooltiptext {
                visibility: hidden;
                background-color: #2B4F76;
                color: white;
                text-align: center;
                padding: 5px;
                border-radius: 6px;
                position: absolute;
                z-index: 1;
                bottom: 125%;
                left: 50%;
                transform: translateX(-50%);
                opacity: 0;
                transition: opacity 0.3s;
            }
            
            .tooltip:hover .tooltiptext {
                visibility: visible;
                opacity: 1;
            }
            
            /* Interactive Filters */
            .filter-container {
                background-color: #2B4F76;
                padding: 1rem;
                border-radius: 10px;
                margin-bottom: 1rem;
            }
            
            /* Enhanced Tables */
            .interactive-table {
                border-collapse: collapse;
                width: 100%;
            }
            
            .interactive-table th,
            .interactive-table td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
            
            .interactive-table tr:hover {
                background-color: rgba(255,255,255,0.05);
            }
            
            /* Loading Animations */
            .loading-spinner {
                border: 4px solid rgba(255,255,255,0.1);
                border-left: 4px solid #4CAF50;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            /* Progress Indicators */
            .progress-bar {
                background-color: rgba(255,255,255,0.1);
                border-radius: 5px;
                padding: 3px;
            }
            
            .progress-bar-fill {
                background-color: #4CAF50;
                height: 20px;
                border-radius: 5px;
                transition: width 0.5s ease-in-out;
            }
            </style>
            
            <script>
            // Add mobile gesture support
            document.addEventListener('DOMContentLoaded', function() {
                let touchstartX = 0;
                let touchendX = 0;
                
                document.addEventListener('touchstart', e => {
                    touchstartX = e.changedTouches[0].screenX;
                });
                
                document.addEventListener('touchend', e => {
                    touchendX = e.changedTouches[0].screenX;
                    handleGesture();
                });
                
                function handleGesture() {
                    if (touchendX < touchstartX) {
                        // Swipe left - show sidebar
                        document.querySelector('[data-testid="stSidebar"]').style.transform = 'translateX(0)';
                    }
                    if (touchendX > touchstartX) {
                        // Swipe right - hide sidebar
                        document.querySelector('[data-testid="stSidebar"]').style.transform = 'translateX(-100%)';
                    }
                }
            });
            </script>
        """, unsafe_allow_html=True)

        # Initialize components
        self.initialize_session_state()
        self.initialize_components()

[Previous methods remain the same until render_form_guide]

    def render_form_guide(self):
        """Render enhanced interactive form guide"""
        st.header("Form Guide")
        
        # Advanced filters
        with st.expander("Advanced Filters", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                track_filter = st.multiselect(
                    "Track",
                    ["Randwick", "Flemington", "Eagle Farm"],
                    default=["Randwick"]
                )
            with col2:
                distance_filter = st.slider(
                    "Distance (m)",
                    1000, 3200, (1000, 3200)
                )
            with col3:
                class_filter = st.multiselect(
                    "Class",
                    ["Group 1", "Group 2", "Group 3", "Listed"],
                    default=["Group 1"]
                )
        
        # Interactive search with autocomplete
        runner = st.text_input(
            "Search Runner",
            help="Type to search for horses, trainers, or jockeys"
        )
        
        if runner:
            # Show loading animation
            with st.spinner('Loading form data...'):
                # Simulated delay for loading animation
                time.sleep(1)
                
                # Runner details card
                st.markdown("""
                    <div class="form-guide-card">
                        <h3>{}</h3>
                        <div class="tooltip">
                            Last 5 starts: 1-2-1-3-2
                            <span class="tooltiptext">Click for detailed history</span>
                        </div>
                    </div>
                """.format(runner), unsafe_allow_html=True)
                
                # Performance metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Win Rate",
                        "34%",
                        "5%",
                        help="Win rate over last 12 months"
                    )
                with col2:
                    st.metric(
                        "Place Rate",
                        "67%",
                        "3%",
                        help="Place rate over last 12 months"
                    )
                with col3:
                    st.metric(
                        "ROI",
                        "15.2%",
                        "-2.1%",
                        help="Return on Investment"
                    )
                
                # Interactive performance chart
                st.subheader("Performance History")
                
                # Add chart type selector
                chart_type = st.radio(
                    "Chart Type",
                    ["Performance", "Speed Ratings", "Weight Carried"],
                    horizontal=True
                )
                
                # Generate chart based on selection
                fig = go.Figure()
                
                if chart_type == "Performance":
                    fig.add_trace(go.Scatter(
                        x=pd.date_range(end=pd.Timestamp.now(), periods=10),
                        y=[1, 3, 2, 1, 4, 2, 1, 3, 2, 1],
                        mode='lines+markers',
                        name='Finish Position',
                        line=dict(color='#4CAF50', width=2),
                        marker=dict(size=10)
                    ))
                    fig.update_yaxes(autorange="reversed")
                
                fig.update_layout(
                    title=f"{chart_type} Chart",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=400,
                    yaxis=dict(
                        gridcolor='rgba(255,255,255,0.1)',
                        zerolinecolor='rgba(255,255,255,0.2)',
                        color='white'
                    ),
                    xaxis=dict(
                        gridcolor='rgba(255,255,255,0.1)',
                        zerolinecolor='rgba(255,255,255,0.2)',
                        color='white'
                    ),
                    font=dict(color='white')
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Detailed statistics tabs
                tab1, tab2, tab3 = st.tabs(["Track Stats", "Distance Stats", "Jockey Stats"])
                
                with tab1:
                    st.markdown("""
                        <div class="interactive-table">
                            <table>
                                <tr>
                                    <th>Track</th>
                                    <th>Runs</th>
                                    <th>Wins</th>
                                    <th>Places</th>
                                    <th>Win%</th>
                                </tr>
                                <tr>
                                    <td>Randwick</td>
                                    <td>8</td>
                                    <td>3</td>
                                    <td>6</td>
                                    <td>37.5%</td>
                                </tr>
                            </table>
                        </div>
                    """, unsafe_allow_html=True)
                
                with tab2:
                    distance_data = pd.DataFrame({
                        'Distance': ['1200m', '1400m', '1600m'],
                        'Runs': [5, 3, 2],
                        'Wins': [2, 1, 1],
                        'Places': [4, 2, 1],
                        'Win%': ['40%', '33%', '50%']
                    })
                    st.dataframe(distance_data, use_container_width=True)
                
                with tab3:
                    st.markdown("### Recent Jockey Performance")
                    for jockey in ['J. McDonald', 'K. McEvoy']:
                        st.markdown(f"""
                            <div class="form-guide-card">
                                <h4>{jockey}</h4>
                                <div class="progress-bar">
                                    <div class="progress-bar-fill" style="width: 75%;"></div>
                                </div>
                                <small>75% win rate with this horse</small>
                            </div>
                        """, unsafe_allow_html=True)

[Rest of the previous methods remain the same]

if __name__ == "__main__":
    dashboard = RacingDashboard()
    dashboard.run()
