import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from account_management import AccountManager
from racing_core import RacingAPIClient
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Racing Dashboard Pro",
    page_icon="🏇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .stApp {
        background-color: #f0f2f6;
    }
    .css-1d391kg {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        border: none;
    }
    .stButton>button:hover {
        background-color: #1565C0;
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

def load_mock_data():
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    pl_data = pd.DataFrame({
        'Date': dates,
        'P/L': np.random.normal(100, 50, len(dates)).cumsum()
    })
    return pl_data

def create_pl_chart(data):
    fig = px.line(data, x='Date', y='P/L',
                  title='Profit/Loss Over Time')
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Profit/Loss ($)",
        hovermode='x unified',
        template='plotly_white'
    )
    return fig

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 'Dashboard'

# Initialize managers
account_manager = AccountManager()
racing_client = RacingAPIClient()

def main():
    # Sidebar navigation
    with st.sidebar:
        st.title("Racing Dashboard")
        
        if not st.session_state.logged_in:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login")
                
                if submit:
                    try:
                        if account_manager.login(username, password):
                            st.session_state.logged_in = True
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials")
                    except Exception as e:
                        logger.error(f"Login error: {str(e)}")
                        st.error("An error occurred during login")
        else:
            st.session_state.active_tab = st.radio(
                "Navigation",
                ["Dashboard", "Race Analysis", "Betting", "Analytics", "Settings"]
            )
            
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.rerun()

    # Main content
    if st.session_state.logged_in:
        if st.session_state.active_tab == "Dashboard":
            st.header("Racing Overview")
            
            # Metrics row
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Today's P/L", "$523.40", "12.3%")
            with col2:
                st.metric("Win Rate", "34%", "2.1%")
            with col3:
                st.metric("Active Bets", "5", "-2")
            with col4:
                st.metric("ROI", "18.5%", "5.2%")
            
            # Charts
            pl_data = load_mock_data()
            st.plotly_chart(create_pl_chart(pl_data), use_container_width=True)
            
            # Recent Activity
            with st.expander("Recent Activity", expanded=True):
                activity_data = pd.DataFrame({
                    'Time': ['10:30 AM', '10:15 AM', '10:00 AM'],
                    'Event': ['Bet Placed', 'Race Started', 'Race Analysis'],
                    'Details': ['$100 on Horse A', 'Melbourne Cup R6', 'Win probability: 65%']
                })
                st.dataframe(activity_data, use_container_width=True)

        elif st.session_state.active_tab == "Race Analysis":
            st.header("Race Analysis")
            
            col1, col2 = st.columns(2)
            with col1:
                track = st.selectbox("Select Track", ["Melbourne", "Sydney", "Brisbane"])
            with col2:
                race = st.selectbox("Select Race", [f"Race {i}" for i in range(1, 11)])
            
            # Race details
            st.subheader("Race Details")
            
            race_data = pd.DataFrame({
                'Horse': [f'Horse {i}' for i in range(1, 8)],
                'Odds': [2.4, 3.1, 5.5, 8.0, 12.0, 15.0, 20.0],
                'Form': ['1-1-2', '2-3-1', '4-2-3', '3-5-4', '6-7-5', '4-4-6', '7-8-8'],
                'Weight': [58.5, 57.0, 56.5, 56.0, 55.5, 55.0, 54.5],
                'Barrier': [4, 7, 2, 9, 1, 6, 3]
            })
            
            st.dataframe(race_data, use_container_width=True)
            
            # Race visualization
            fig = px.bar(race_data, x='Horse', y='Odds',
                        title='Current Odds by Horse')
            st.plotly_chart(fig, use_container_width=True)

        elif st.session_state.active_tab == "Betting":
            st.header("Betting Dashboard")
            
            # Betting form
            with st.form("betting_form"):
                col1, col2 = st.columns(2)
                with col1:
                    bet_amount = st.number_input("Bet Amount ($)", min_value=0.0, step=10.0)
                    horse = st.selectbox("Select Horse", [f"Horse {i}" for i in range(1, 8)])
                with col2:
                    bet_type = st.selectbox("Bet Type", ["Win", "Place", "Each Way"])
                    odds = st.number_input("Current Odds", min_value=1.0, value=2.0)
                
                submit_bet = st.form_submit_button("Place Bet")
                
                if submit_bet:
                    st.success(f"Bet placed successfully: ${bet_amount} on {horse} to {bet_type}")

        elif st.session_state.active_tab == "Analytics":
            st.header("Advanced Analytics")
            
            period = st.selectbox("Time Period", ["Last Week", "Last Month", "Last 3 Months", "Year to Date"])
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Performance Metrics")
                metrics_data = pd.DataFrame({
                    'Metric': ['Total Bets', 'Win Rate', 'Average Odds', 'ROI'],
                    'Value': ['156', '34%', '3.45', '18.5%']
                })
                st.dataframe(metrics_data, use_container_width=True)
            
            with col2:
                st.subheader("Bet Distribution")
                bet_types = ['Win', 'Place', 'Each Way']
                bet_counts = [45, 35, 20]
                fig = px.pie(values=bet_counts, names=bet_types)
                st.plotly_chart(fig)

        elif st.session_state.active_tab == "Settings":
            st.header("Settings")
            
            # User preferences
            st.subheader("User Preferences")
            notification_enabled = st.toggle("Enable Notifications", value=True)
            odds_format = st.selectbox("Odds Format", ["Decimal", "Fractional", "American"])
            default_bet = st.number_input("Default Bet Amount", min_value=0.0, step=10.0)
            
            # API Configuration
            st.subheader("API Configuration")
            api_key = st.text_input("API Key", type="password")
            
            if st.button("Save Settings"):
                st.success("Settings saved successfully!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error("An unexpected error occurred. Please try again later.")
