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
    initial_sidebar_state="expanded",
    menu_items={
        'About': 'Racing Analysis Platform'
    }
)

# Add proper DOCTYPE and meta tags
st.markdown('''
    <!DOCTYPE html>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
''', unsafe_allow_html=True)

# Initialize session state
if 'client' not in st.session_state:
    st.session_state.client = None
if 'selected_race' not in st.session_state:
    st.session_state.selected_race = None
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Racing"
if 'betslip' not in st.session_state:
    st.session_state.betslip = []
if 'cookie_consent' not in st.session_state:
    st.session_state.cookie_consent = False

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
        st.text_input("Search...", placeholder="Search races, runners...", key="search_input")
    
    with col2:
        tab1, tab2 = st.tabs(["Racing", "Sports"])
        if tab1:
            st.session_state.active_tab = "Racing"
        elif tab2:
            st.session_state.active_tab = "Sports"
    
    with col3:
        if not st.session_state.cookie_consent:
            if st.button("Accept Cookies", key="cookie_consent_button"):
                st.session_state.cookie_consent = True
                st.rerun()

def render_navigation():
    """Render sidebar navigation"""
    st.sidebar.title("Navigation")
    if st.sidebar.button("🏠 Home", key="nav_home"):
        st.session_state.page = "home"
    if st.sidebar.button("🎁 Promotions", key="nav_promotions"):
        st.session_state.page = "promotions"
    if st.sidebar.button("🏇 Today's Racing", key="nav_today"):
        st.session_state.page = "today"
    if st.sidebar.button("📅 All Racing", key="nav_all"):
        st.session_state.page = "all"

def format_date(date_obj) -> str:
    """Format date with proper timezone handling"""
    try:
        tz = pytz.timezone('Australia/Sydney')
        if isinstance(date_obj, datetime):
            return date_obj.astimezone(tz).strftime("%Y-%m-%dT%H:%M:%S%z")
        elif isinstance(date_obj, str):
            dt = datetime.strptime(date_obj, "%Y-%m-%d")
            return dt.replace(tzinfo=tz).strftime("%Y-%m-%dT%H:%M:%S%z")
        elif isinstance(date_obj, date):
            dt = datetime.combine(date_obj, datetime.min.time())
            return dt.replace(tzinfo=tz).strftime("%Y-%m-%dT%H:%M:%S%z")
        return None
    except Exception as e:
        logger.error(f"Date formatting error: {str(e)}")
        return None

def render_race_list(race_type: str):
    """Render list of upcoming races"""
    try:
        races = st.session_state.client.get_next_races(
            jurisdiction="NSW",
            limit=5
        )
        
        if races and not races.get('error'):
            for idx, race in enumerate(races.get('races', [])):
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.write(f"R{race['raceNumber']} {race['venueName']}")
                    with col2:
                        countdown = format_countdown(race.get('startTime'))
                        st.write(countdown)
                    with col3:
                        if st.button("View", key=f"view_race_{race_type}_{idx}_{race.get('id', '')}"):
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
        for idx, selection in enumerate(st.session_state.multi_selections):
            st.write(f"{selection['runner']} @ {selection['odds']}")
            if st.button("Remove", key=f"remove_multi_{idx}"):
                st.session_state.multi_selections.pop(idx)
                st.rerun()
        
        stake = st.number_input("Stake ($)", min_value=1.0, value=10.0, key="multi_stake")
        if st.button("Add to Betslip", key="add_multi_to_betslip"):
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
            
            for idx, bet in enumerate(st.session_state.betslip):
                with st.container():
                    st.write(f"{bet['runner']} - {bet['odds']}")
                    st.write(f"Stake: ${bet['stake']:.2f}")
                    if st.button("Remove", key=f"remove_bet_{idx}"):
                        st.session_state.betslip.pop(idx)
                        st.rerun()
                    
                    total_stake += bet['stake']
                    total_return += bet['stake'] * float(bet['odds'].replace('$', ''))
            
            st.write("---")
            st.write(f"Total Stake: ${total_stake:.2f}")
            st.write(f"Potential Return: ${total_return:.2f}")

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
