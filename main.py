import streamlit as st
from datetime import datetime, date
import pytz
from typing import Dict, List, Optional
import logging
from punting_form_analyzer import PuntingFormAPI
from account_management import AccountManager

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

def format_date(date_obj: Optional[datetime | date | str]) -> Optional[str]:
    """Format date with proper timezone handling"""
    if not date_obj:
        return None
        
    try:
        tz = pytz.timezone('Australia/Sydney')
        
        if isinstance(date_obj, datetime):
            return date_obj.astimezone(tz).strftime("%Y-%m-%d")
        elif isinstance(date_obj, str):
            try:
                dt = datetime.strptime(date_obj, "%Y-%m-%d")
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                logger.error(f"Invalid date format: {date_obj}")
                return None
        elif isinstance(date_obj, date):
            return date_obj.strftime("%Y-%m-%d")
            
        return None
    except Exception as e:
        logger.error(f"Date formatting error: {str(e)}")
        return None

def format_countdown(start_time: Optional[str]) -> str:
    """Format countdown timer"""
    if not start_time:
        return "N/A"
        
    try:
        tz = pytz.timezone('Australia/Sydney')
        race_time = datetime.strptime(start_time, "%Y-%m-%d")
        race_time = race_time.replace(tzinfo=tz)
        now = datetime.now(tz)
        delta = race_time - now
        
        if delta.total_seconds() < 0:
            return "Started"
        
        minutes = delta.seconds // 60
        if minutes < 60:
            return f"{minutes}m"
        else:
            hours = minutes // 60
            return f"{hours}h {minutes % 60}m"
    except Exception as e:
        logger.error(f"Error formatting countdown: {str(e)}")
        return "N/A"

def render_race_list(race_type: str):
    """Render list of upcoming races"""
    if not st.session_state.logged_in:
        return
        
    with st.spinner("Loading races..."):
        try:
            races = st.session_state.client.get_next_races(
                jurisdiction="NSW",
                limit=5
            )
            
            if isinstance(races, dict):
                if error := races.get('error'):
                    st.error(f"Error loading races: {error}")
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
                                start_time = format_date(race.get('startTime'))
                                countdown = format_countdown(start_time)
                                st.write(countdown)
                            with col3:
                                if st.button("View", key=f"view_{race_type}_{idx}"):
                                    st.session_state.selected_race = race
            else:
                st.error("Invalid API response format")
                
        except Exception as e:
            logger.error(f"Error loading races: {str(e)}")
            st.error("Unable to load races. Please try again later.")

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
    main()
