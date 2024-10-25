import streamlit as st
from datetime import datetime, date
import pytz
from typing import Dict, List, Optional
import logging
from punting_form_analyzer import PuntingFormAPI
from account_management import AccountManager
from betting_system_integration import BettingSystemIntegration

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

def initialize_client():
    """Initialize Punting Form API client"""
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
            st.error(f"Failed to initialize client: {str(e)}")
            st.stop()

def format_date(date_obj: Optional[datetime | date | str]) -> Optional[str]:
    """Format date with proper timezone handling"""
    if not date_obj:
        return None
        
    try:
        tz = pytz.timezone('Australia/Sydney')
        
        if isinstance(date_obj, datetime):
            return date_obj.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(date_obj, str):
            try:
                dt = datetime.strptime(date_obj, "%Y-%m-%d")
                return dt.replace(tzinfo=tz).strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    dt = datetime.strptime(date_obj, "%Y-%m-%dT%H:%M:%S%z")
                    return dt.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    logger.error(f"Invalid date format: {date_obj}")
                    return None
        elif isinstance(date_obj, date):
            dt = datetime.combine(date_obj, datetime.min.time())
            return dt.replace(tzinfo=tz).strftime("%Y-%m-%d %H:%M:%S")
            
        return None
    except Exception as e:
        logger.error(f"Date formatting error: {str(e)}")
        return None

def format_countdown(start_time: Optional[str]) -> str:
    """Format countdown timer"""
    if not start_time:
        return "N/A"
        
    try:
        race_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        now = datetime.now(pytz.timezone('Australia/Sydney'))
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
    with st.spinner("Loading races..."):
        try:
            races = st.session_state.client.get_next_races(
                jurisdiction="NSW",
                limit=5
            )
            
            if isinstance(races, dict):
                if races.get('error'):
                    st.error(f"Error loading races: {races['error']}")
                    return
                    
                race_list = races.get('races', [])
                if race_list:
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
                    st.info("No upcoming races")
            else:
                st.error("Invalid response format from API")
                
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
    initialize_client()
    
    # Initialize components
    account_manager = AccountManager()
    betting_integration = BettingSystemIntegration()
    
    # Render login/account
    account_manager.render_login()
    
    # Main content
    if st.session_state.active_tab == "Racing":
        col1, col2 = st.columns([7, 3])
        
        with col1:
            render_next_to_jump()
        
        with col2:
            betting_integration.render_betting_interface()

if __name__ == "__main__":
    main()
