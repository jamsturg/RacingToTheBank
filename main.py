import streamlit as st
from datetime import datetime, date
from typing import Dict, List, Optional
import logging
from punting_form_analyzer import PuntingFormAPI
from account_management import AccountManager
from utils.date_utils import format_date, format_countdown
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Initialize session state
if 'client' not in st.session_state:
    st.session_state.client = None
if 'selected_race' not in st.session_state:
    st.session_state.selected_race = None
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Racing"
if 'betslip' not in st.session_state:
    st.session_state.betslip = []
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def initialize_client():
    """Initialize API client with proper error handling"""
    if not st.session_state.logged_in:
        return
        
    if st.session_state.client is None:
        try:
            api_key = st.secrets["punting_form"]["api_key"]
            if not api_key:
                st.error("Missing Punting Form API key")
                st.stop()
            
            st.session_state.client = PuntingFormAPI(api_key)
            logger.info("API client initialized successfully")
        except Exception as e:
            logger.error(f"Client initialization error: {str(e)}")
            st.error("Failed to initialize client. Please check your API key.")
            st.stop()

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
    st.subheader("Next To Jump")
    
    tab1, tab2, tab3 = st.tabs(["Horses", "Greyhounds", "Harness"])
    
    with tab1:
        render_race_list("R")  # Thoroughbred races
    
    with tab2:
        render_race_list("G")  # Greyhound races
    
    with tab3:
        render_race_list("H")  # Harness races

def main():
    # Initialize account manager first
    account_manager = AccountManager()
    
    # Show login form and require login before proceeding
    account_manager.render_login()
    
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
    import streamlit.web.bootstrap as bootstrap
    # Use port 8501 which is Streamlit's default port
    import os
    os.environ['STREAMLIT_SERVER_PORT'] = '8501'
    flag_options = []
    bootstrap.run(main, "", [], flag_options)
