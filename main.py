import streamlit as st
from datetime import datetime, date
from typing import Dict, List, Optional, Union
import logging
import json
from pathlib import Path
import sys

# Local imports
from punting_form_analyzer import PuntingFormAPI
from account_management import AccountManager
from utils.date_utils import format_date, format_countdown
from utils.race_details import render_race_details
from utils.logger import setup_logger

# Optional imports with fallback
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# Configure logging
logger = setup_logger(
    "main",
    Path("logs/main.log"),
    level=logging.INFO
)

# Page config
st.set_page_config(
    page_title="Racing Analysis Platform",
    page_icon="🏇",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': 'Racing Analysis Platform'
    }
)

def initialize_session_state():
    """Initialize and validate session state variables"""
    session_vars = {
        'client': None,
        'selected_race': None,
        'active_tab': "Racing",
        'betslip': [],
        'logged_in': False,
        'webgl_context_lost': False,
        'connection_error': False,
        'last_refresh': None,
        'error_count': 0,
        'notifications': [],
        'dark_mode': False,
        'preferences': {}
    }
    
    # Initialize missing variables
    for var, default in session_vars.items():
        if var not in st.session_state:
            st.session_state[var] = default
            
    # Validate existing variables
    for var in st.session_state:
        if var in session_vars and not isinstance(st.session_state[var], type(session_vars[var])):
            logger.warning(f"Invalid type for session variable {var}, resetting to default")
            st.session_state[var] = session_vars[var]
            
    # Clear old variables
    for var in list(st.session_state):
        if var not in session_vars:
            del st.session_state[var]

def initialize_client() -> Optional[PuntingFormAPI]:
    """Initialize API client with proper error handling"""
    if not st.session_state.logged_in:
        return None
        
    if st.session_state.client is None:
        try:
            # Check for API key in multiple locations
            api_key = (
                st.secrets.get("punting_form", {}).get("api_key") or
                os.environ.get("PUNTING_FORM_API_KEY")
            )
            
            if not api_key:
                logger.error("API key not found in secrets or environment")
                st.error("Missing Punting Form API key. Please check configuration.")
                st.stop()
            
            client = PuntingFormAPI(api_key)
            
            # Test API connection
            if not client.verify_credentials():
                logger.error("API credentials verification failed")
                st.error("Invalid API credentials. Please check your API key.")
                st.stop()
                
            st.session_state.client = client
            logger.info("API client initialized and verified successfully")
            
        except Exception as e:
            logger.error(f"Client initialization error: {str(e)}", exc_info=True)
            st.error(
                "Failed to initialize client. Please check your API key and network connection."
            )
            st.stop()
            
    return st.session_state.client

def handle_api_response(response: Dict) -> Optional[Dict]:
    """Handle API response with proper error handling"""
    if isinstance(response, dict):
        if error := response.get('error'):
            error_msg = error if isinstance(error, str) else json.dumps(error)
            st.error(f"API Error: {error_msg}")
            logger.error(f"API Error: {error_msg}")
            return None
        return response
    else:
        st.error("Invalid API response format")
        logger.error(f"Invalid API response format: {type(response)}")
        return None

def render_race_list(race_type: str):
    """Render list of upcoming races with improved error handling"""
    if not st.session_state.logged_in:
        return
        
    with st.spinner("Loading races..."):
        try:
            races = st.session_state.client.get_next_races(
                jurisdiction="NSW",
                limit=5
            )
            
            races = handle_api_response(races)
            if not races:
                return
                
            if not (race_list := races.get('races', [])):
                st.info("No upcoming races found")
                return
                
            for idx, race in enumerate(race_list):
                if race.get('raceType') == race_type:
                    with st.container():
                        col1, col2, col3 = st.columns([3, 2, 1])
                        with col1:
                            st.write(f"R{race.get('raceNumber')} {race.get('venueName', 'Unknown')}")
                        with col2:
                            start_time = format_date(race.get('startTime'), include_time=True)
                            countdown = format_countdown(start_time)
                            st.write(countdown)
                        with col3:
                            if st.button("View", key=f"view_{race_type}_{idx}"):
                                st.session_state.selected_race = race
                
        except Exception as e:
            logger.error(f"Error loading races: {str(e)}")
            st.error("Unable to load races. Please try again later.")
            if st.session_state.client:
                # Attempt to reinitialize client on error
                st.session_state.client = None
                initialize_client()

def render_next_to_jump():
    """Render Next To Jump section with tabs"""
    col1, col2 = st.columns([2,3])
    
    with col1:
        st.subheader("Next To Jump")
        tab1, tab2, tab3 = st.tabs(["Horses", "Greyhounds", "Harness"])
        
        with tab1:
            render_race_list("R")  # Thoroughbred races
        
        with tab2:
            render_race_list("G")  # Greyhound races
        
        with tab3:
            render_race_list("H")  # Harness races
            
    with col2:
        if st.session_state.selected_race:
            from utils.race_details import render_race_details
            render_race_details(st.session_state.selected_race)

def main():
    try:
        # Initialize account manager first
        account_manager = AccountManager()
        
        # Show login form and require login before proceeding
        account_manager.render_login()
    except ImportError as e:
        st.error(f"Failed to initialize: {str(e)}")
        st.info("Please install required dependencies using: pip install --user pandas plotly streamlit")
    
    # Only proceed with API initialization and content if logged in
    if st.session_state.logged_in:
        initialize_client()
        
        # Main content
        st.title("🏇 Racing Analysis Platform")
        
        if st.session_state.active_tab == "Racing":
            render_next_to_jump()
    else:
        st.info("Please log in to access racing information")

if __name__ == "__main__":
    main()
