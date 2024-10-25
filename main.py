import streamlit as st
from datetime import datetime, date
import pytz
from typing import Dict, List
import logging
from punting_form_analyzer import PuntingFormAPI
from account_management import AccountManager
from betting_system_integration import BettingSystemIntegration
from race_information import RaceInformation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Racing Analysis Platform",
    page_icon="🏇",
    layout="wide",
    initial_sidebar_state="expanded"
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
        except Exception as e:
            logger.error(f"Client initialization error: {str(e)}")
            st.error(f"Failed to initialize client: {str(e)}")
            st.stop()

def render_header():
    """Render page header with search and Racing/Sports toggle"""
    col1, col2, col3 = st.columns([2, 6, 2])
    
    with col1:
        st.text_input("Search...", placeholder="Search races, runners...")
    
    with col2:
        tab1, tab2 = st.tabs(["Racing", "Sports"])
        if tab1:
            st.session_state.active_tab = "Racing"
        elif tab2:
            st.session_state.active_tab = "Sports"
    
    with col3:
        st.empty()  # Reserved for notifications/user menu

def render_navigation():
    """Render sidebar navigation"""
    st.sidebar.title("Navigation")
    if st.sidebar.button("🏠 Home"):
        st.session_state.page = "home"
    if st.sidebar.button("🎁 Promotions"):
        st.session_state.page = "promotions"
    if st.sidebar.button("🏇 Today's Racing"):
        st.session_state.page = "today"
    if st.sidebar.button("📅 All Racing"):
        st.session_state.page = "all"

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

def render_race_list(race_type: str):
    """Render list of upcoming races"""
    try:
        races = st.session_state.client.get_next_races(
            jurisdiction="NSW",
            limit=5
        )
        
        if races and not races.get('error'):
            for race in races.get('races', []):
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.write(f"R{race['raceNumber']} {race['venueName']}")
                    with col2:
                        countdown = format_countdown(race.get('startTime'))
                        st.write(countdown)
                    with col3:
                        if st.button("View", key=f"view_{race.get('id', '')}"):
                            st.session_state.selected_race = race
        else:
            st.info("No upcoming races")
            
    except Exception as e:
        logger.error(f"Error loading races: {str(e)}")
        st.error("Unable to load races. Please try again later.")

def format_countdown(start_time: str) -> str:
    """Format countdown timer"""
    try:
        if not start_time:
            return "N/A"
            
        race_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S%z")
        now = datetime.now(pytz.UTC)
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

def render_quick_multi():
    """Render Quick Multi section"""
    st.subheader("Quick Multi")
    
    if not st.session_state.get('multi_selections', []):
        st.write("Select runners to create a multi bet")
    else:
        for selection in st.session_state.multi_selections:
            st.write(f"{selection['runner']} @ {selection['odds']}")
        
        stake = st.number_input("Stake ($)", min_value=1.0, value=10.0)
        if st.button("Add to Betslip"):
            # Add multi bet to betslip
            pass

def render_betslip():
    """Render betslip"""
    with st.sidebar:
        st.subheader("Betslip")
        if not st.session_state.betslip:
            st.write("Your bet slip is empty")
            st.write("Make a selection from our betting markets to see them appear here")
        else:
            total_stake = 0
            total_return = 0
            
            for bet in st.session_state.betslip:
                with st.container():
                    st.write(f"{bet['runner']} - {bet['odds']}")
                    st.write(f"Stake: ${bet['stake']:.2f}")
                    if st.button("Remove", key=f"remove_{bet['id']}"):
                        st.session_state.betslip.remove(bet)
                        st.rerun()
                    
                    total_stake += bet['stake']
                    total_return += bet['stake'] * float(bet['odds'].replace('$', ''))
            
            st.write("---")
            st.write(f"Total Stake: ${total_stake:.2f}")
            st.write(f"Potential Return: ${total_return:.2f}")

def main():
    initialize_client()
    
    # Initialize components
    account_manager = AccountManager()
    
    # Render header
    render_header()
    
    # Render navigation
    render_navigation()
    
    # Render login/account
    account_manager.render_login()
    
    # Main content
    if st.session_state.active_tab == "Racing":
        col1, col2 = st.columns([7, 3])
        
        with col1:
            render_next_to_jump()
            render_quick_multi()
        
        with col2:
            render_betslip()

if __name__ == "__main__":
    main()
