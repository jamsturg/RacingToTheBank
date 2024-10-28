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

        # Custom CSS with blue-grey-darkblue-white color palette
        st.markdown("""
            <style>
            :root {
                --primary-blue: #1E3D59;
                --secondary-blue: #2B4F76;
                --light-blue: #E6EEF8;
                --grey-blue: #7B8FA1;
                --white: #FFFFFF;
            }
            
            /* Global text color */
            .stMarkdown, .stText, p, h1, h2, h3, label {
                color: var(--white) !important;
            }
            
            /* Main header */
            .main-header {
                background-color: var(--primary-blue);
                padding: 1.5rem;
                border-radius: 5px;
                color: var(--white) !important;
                text-align: center;
                margin-bottom: 2rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .main-header h1 {
                color: var(--white) !important;
                font-size: 2.5rem;
                font-weight: bold;
            }
            
            /* Sidebar */
            section[data-testid="stSidebar"] {
                background-color: var(--primary-blue);
                border-right: 1px solid var(--grey-blue);
            }
            
            section[data-testid="stSidebar"] .stMarkdown {
                color: var(--white) !important;
            }
            
            section[data-testid="stSidebar"] h1 {
                color: var(--white) !important;
                font-size: 1.5rem;
                padding: 1rem 0;
            }
            
            section[data-testid="stSidebar"] .stRadio label {
                color: var(--white) !important;
            }
            
            section[data-testid="stSidebar"] button {
                background-color: var(--secondary-blue);
                color: var(--white);
                border: none;
                border-radius: 5px;
                padding: 0.5rem 1rem;
                width: 100%;
                margin: 0.5rem 0;
            }
            
            section[data-testid="stSidebar"] button:hover {
                background-color: var(--grey-blue);
            }
            
            section[data-testid="stSidebar"] .stExpander {
                border: 1px solid var(--grey-blue);
                border-radius: 5px;
                margin: 1rem 0;
            }
            
            /* Metric cards */
            div[data-testid="stMetricValue"] {
                background-color: var(--light-blue);
                padding: 1rem;
                border-radius: 5px;
                color: var(--primary-blue) !important;
                font-weight: bold;
            }
            
            /* Tables */
            .stDataFrame {
                background-color: var(--white);
                border: 1px solid var(--grey-blue);
                border-radius: 5px;
            }
            
            /* Buttons */
            .stButton>button {
                background-color: var(--secondary-blue);
                color: var(--white);
                border: none;
                border-radius: 5px;
                padding: 0.5rem 1rem;
                transition: background-color 0.3s;
            }
            
            .stButton>button:hover {
                background-color: var(--grey-blue);
            }
            
            /* Forms */
            .stForm {
                background-color: var(--light-blue);
                padding: 1.5rem;
                border-radius: 5px;
            }
            
            /* Tabs */
            .stTabs [data-baseweb="tab-list"] {
                gap: 2rem;
                background-color: var(--light-blue);
                padding: 0.5rem;
                border-radius: 5px;
            }
            
            .stTabs [data-baseweb="tab"] {
                height: 4rem;
                color: var(--primary-blue);
                background-color: var(--white);
                border-radius: 5px;
            }
            
            .stTabs [data-baseweb="tab"][aria-selected="true"] {
                background-color: var(--secondary-blue);
                color: var(--white);
            }
            
            /* Footer */
            footer {
                position: fixed;
                bottom: 0;
                width: 100%;
                background-color: var(--primary-blue);
                color: var(--white);
                text-align: center;
                padding: 1rem;
                box-shadow: 0 -2px 4px rgba(0,0,0,0.1);
            }
            
            /* Input fields */
            .stTextInput>div>div>input {
                background-color: var(--white);
                color: var(--primary-blue);
                border: 1px solid var(--grey-blue);
            }
            
            /* Select boxes */
            .stSelectbox>div>div {
                background-color: var(--white);
                color: var(--primary-blue);
                border: 1px solid var(--grey-blue);
            }
            
            /* Radio buttons */
            .stRadio>label {
                color: var(--white) !important;
            }
            
            /* Expander */
            .streamlit-expanderHeader {
                background-color: var(--light-blue);
                color: var(--primary-blue);
                border-radius: 5px;
            }
            
            /* Main content background */
            .main .block-container {
                background-color: var(--primary-blue);
                padding: 2rem;
                border-radius: 10px;
            }
            
            /* Number input */
            .stNumberInput input {
                color: var(--primary-blue) !important;
                background-color: var(--white) !important;
            }
            
            /* Selectbox text */
            .stSelectbox div[data-baseweb="select"] span {
                color: var(--primary-blue) !important;
            }
            </style>
        """, unsafe_allow_html=True)

        # Initialize components
        self.initialize_session_state()
        self.initialize_components()

    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'initialized' not in st.session_state:
            st.session_state.initialized = True
            st.session_state.logged_in = False
            st.session_state.page = "Dashboard"
            st.session_state.active_race = None
            st.session_state.bet_slip = []
            st.session_state.alerts = []
            st.session_state.dark_mode = False
            st.session_state.auto_refresh = True
            st.session_state.refresh_interval = 30
            st.session_state.last_update = datetime.now()

    def initialize_components(self):
        """Initialize analysis components"""
        try:
            self.predictor = AdvancedRacingPredictor()
            self.statistics = AdvancedStatistics()
            self.form_analyzer = FormAnalysis()
            self.account_manager = AccountManager()
            self.tab_client = TABApiClient()
        except Exception as e:
            st.error(f"Failed to initialize components: {str(e)}")
            st.stop()

    def render_header(self):
        """Render page header"""
        st.markdown('<div class="main-header"><h1>To The Bank</h1></div>', unsafe_allow_html=True)

    def render_navigation(self):
        """Render navigation sidebar"""
        with st.sidebar:
            st.title("🏇 To The Bank")
            
            # Main navigation
            st.session_state.page = st.radio(
                "Navigation",
                ["Dashboard", "Race Analysis", "Form Guide", "Statistics", "Betting", "Account"]
            )
            
            # Quick actions
            with st.expander("Quick Actions"):
                track = st.selectbox("Track", ["Randwick", "Flemington", "Eagle Farm"])
                race = st.selectbox("Race", [f"Race {i}" for i in range(1, 11)])
                bet_type = st.selectbox("Bet Type", ["Win", "Place", "Each Way"])
                amount = st.number_input("Amount ($)", min_value=1.0, step=10.0)
                if st.button("Quick Bet"):
                    st.success(f"Bet placed: ${amount} {bet_type}")

    def render_login(self):
        """Render login form"""
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.subheader("Login")
            with st.form("login_form", clear_on_submit=True):
                username = st.text_input("Username (use 'demo')")
                password = st.text_input("Password (use 'demo')", type="password")
                submit = st.form_submit_button("Login")
                
                if submit:
                    if username == "demo" and password == "demo":
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Use demo/demo to login.")

    def render_dashboard(self):
        """Render main dashboard"""
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Account Balance", "$1,000.00", "12.3%")
        with col2:
            st.metric("Today's P/L", "$523.40", "5.2%")
        with col3:
            st.metric("Win Rate", "34%", "2.1%")
        with col4:
            st.metric("ROI", "15.2%", "3.4%")

        # Live races and predictions
        col1, col2 = st.columns([2,1])
        
        with col1:
            st.subheader("Live Races")
            races_df = pd.DataFrame({
                'Track': ['Randwick', 'Flemington', 'Eagle Farm'],
                'Race': [f'Race {i}' for i in range(1, 4)],
                'Time': [(datetime.now() + timedelta(minutes=i*30)).strftime('%H:%M') for i in range(3)]
            })
            st.dataframe(races_df, use_container_width=True)

        with col2:
            st.subheader("Top Predictions")
            predictions_df = pd.DataFrame({
                'Horse': ['Horse 1', 'Horse 2', 'Horse 3'],
                'Confidence': ['High', 'Medium', 'Medium'],
                'Odds': [2.40, 3.50, 5.00]
            })
            st.dataframe(predictions_df, use_container_width=True)

        # Performance chart
        st.subheader("Performance Chart")
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        performance_data = pd.DataFrame({
            'Date': dates,
            'P/L': pd.Series(index=dates, data=[100 * (i % 5 - 2) for i in range(len(dates))]).cumsum()
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=performance_data['Date'],
            y=performance_data['P/L'],
            mode='lines',
            line=dict(color='#E6EEF8', width=2),
            fill='tozeroy',
            fillcolor='rgba(230, 238, 248, 0.1)'
        ))
        fig.update_layout(
            title="Daily P/L Performance",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(
                gridcolor='rgba(255,255,255,0.2)',
                zerolinecolor='rgba(255,255,255,0.5)',
                color='white'
            ),
            xaxis=dict(
                gridcolor='rgba(255,255,255,0.2)',
                zerolinecolor='rgba(255,255,255,0.5)',
                color='white'
            ),
            font=dict(color='white')
        )
        st.plotly_chart(fig, use_container_width=True)

    def render_race_analysis(self):
        """Render race analysis page"""
        st.header("Race Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            track = st.selectbox("Select Track", ["Randwick", "Flemington", "Eagle Farm"])
        with col2:
            race = st.selectbox("Select Race", [f"Race {i}" for i in range(1, 11)])

        # Tabs for different analysis views
        tab1, tab2, tab3 = st.tabs(["Speed Map", "Form Analysis", "Statistical Analysis"])
        
        with tab1:
            st.subheader("Speed Map")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[1, 2, 3, 4, 5],
                y=[1, 2, 1, 3, 2],
                mode='lines+markers',
                name='Speed Positions',
                line=dict(color='#E6EEF8', width=2),
                marker=dict(color='#2B4F76', size=10)
            ))
            fig.update_layout(
                title="Race Speed Map",
                xaxis_title="Distance",
                yaxis_title="Position",
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(
                    gridcolor='rgba(255,255,255,0.2)',
                    zerolinecolor='rgba(255,255,255,0.5)',
                    color='white'
                ),
                xaxis=dict(
                    gridcolor='rgba(255,255,255,0.2)',
                    zerolinecolor='rgba(255,255,255,0.5)',
                    color='white'
                ),
                font=dict(color='white')
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.subheader("Form Analysis")
            runner = st.selectbox("Select Runner", [f"Horse {i}" for i in range(1, 8)])
            self.form_analyzer.render_form_dashboard({'runnerName': runner})
        
        with tab3:
            st.subheader("Statistical Analysis")
            self.statistics.render_statistical_insights({})

    def render_form_guide(self):
        """Render form guide page"""
        st.header("Form Guide")
        
        # Runner search
        runner = st.text_input("Search Runner")
        if runner:
            self.form_analyzer.render_form_dashboard({'runnerName': runner})

    def render_statistics(self):
        """Render statistics page"""
        st.header("Statistical Analysis")
        
        # Tabs for different statistical views
        tab1, tab2, tab3 = st.tabs(["Track Bias", "Market Analysis", "Historical Trends"])
        
        with tab1:
            st.subheader("Track Bias Analysis")
            track = st.selectbox("Select Track", ["Randwick", "Flemington", "Eagle Farm"])
            self.statistics.render_track_bias_analysis({})
        
        with tab2:
            st.subheader("Market Analysis")
            self.statistics.render_value_analysis({})
        
        with tab3:
            st.subheader("Historical Trends")
            self.statistics.render_historical_analysis({})

    def render_betting(self):
        """Render betting page"""
        st.header("Betting Dashboard")
        
        # Betting form
        with st.form("betting_form"):
            col1, col2 = st.columns(2)
            with col1:
                track = st.selectbox("Track", ["Randwick", "Flemington", "Eagle Farm"])
                race = st.selectbox("Race", [f"Race {i}" for i in range(1, 11)])
            with col2:
                bet_type = st.selectbox("Bet Type", ["Win", "Place", "Each Way"])
                amount = st.number_input("Amount ($)", min_value=1.0, step=10.0)
            
            if st.form_submit_button("Place Bet"):
                st.success(f"Bet placed successfully: ${amount} on Race {race} at {track}")
        
        # Active bets
        st.subheader("Active Bets")
        bets_df = pd.DataFrame({
            'Track': ['Randwick', 'Flemington'],
            'Race': ['Race 3', 'Race 5'],
            'Horse': ['Horse 1', 'Horse 4'],
            'Amount': [50, 100],
            'Type': ['Win', 'Each Way'],
            'Status': ['Active', 'Active']
        })
        st.dataframe(bets_df, use_container_width=True)

    def render_account(self):
        """Render account page"""
        st.header("Account Management")
        
        # Account tabs
        tab1, tab2, tab3 = st.tabs(["Details", "History", "Settings"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Available Balance", "$1,000.00")
                st.metric("Pending Bets", "$150.00")
            with col2:
                st.metric("Total Profit/Loss", "$2,500.00")
                st.metric("Win Rate", "34%")
        
        with tab2:
            st.subheader("Betting History")
            history_df = pd.DataFrame({
                'Date': pd.date_range(start='2024-01-01', periods=5),
                'Track': ['Randwick', 'Flemington', 'Eagle Farm', 'Randwick', 'Flemington'],
                'Horse': [f'Horse {i}' for i in range(1, 6)],
                'Amount': [50, 100, 75, 200, 150],
                'Result': ['Won', 'Lost', 'Won', 'Lost', 'Won']
            })
            st.dataframe(history_df, use_container_width=True)
        
        with tab3:
            st.subheader("Account Settings")
            with st.form("settings_form"):
                st.text_input("Email", value="user@example.com")
                st.number_input("Default Bet Amount", value=50.0, step=10.0)
                st.checkbox("Enable Email Notifications")
                st.checkbox("Enable SMS Notifications")
                if st.form_submit_button("Save Settings"):
                    st.success("Settings saved successfully")

    def render_footer(self):
        """Render page footer"""
        st.markdown("""
            <footer>
                <p>To The Bank © 2024 | Terms & Conditions | Privacy Policy</p>
            </footer>
        """, unsafe_allow_html=True)

    def run(self):
        """Run the dashboard application"""
        self.render_header()
        
        if not st.session_state.logged_in:
            self.render_login()
        else:
            self.render_navigation()
            
            if st.session_state.page == "Dashboard":
                self.render_dashboard()
            elif st.session_state.page == "Race Analysis":
                self.render_race_analysis()
            elif st.session_state.page == "Form Guide":
                self.render_form_guide()
            elif st.session_state.page == "Statistics":
                self.render_statistics()
            elif st.session_state.page == "Betting":
                self.render_betting()
            elif st.session_state.page == "Account":
                self.render_account()
            
            self.render_footer()

if __name__ == "__main__":
    dashboard = RacingDashboard()
    dashboard.run()
