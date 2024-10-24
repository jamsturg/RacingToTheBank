import streamlit as st
from datetime import datetime
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
if 'last_error' not in st.session_state:
    st.session_state.last_error = None

def initialize_client():
    """Initialize Punting Form API client"""
    if st.session_state.client is None:
        try:
            # Get API key from secrets
            api_key = st.secrets["punting_form"]["api_key"]
            if not api_key:
                st.error("Missing Punting Form API key")
                st.stop()
            
            st.session_state.client = PuntingFormAPI(api_key)
            st.session_state.last_error = None
        except Exception as e:
            logger.error(f"Client initialization error: {str(e)}")
            st.error(f"Failed to initialize client: {str(e)}")
            st.stop()

def format_meeting_name(meeting: Dict) -> str:
    """Format meeting name for display"""
    venue = meeting.get('venue_name', '')
    track = meeting.get('track_condition', '')
    return f"{venue} ({track})" if track else venue

def format_race_name(race: Dict) -> str:
    """Format race name for display"""
    number = race.get('number', '')
    name = race.get('name', '')
    distance = race.get('distance', '')
    return f"Race {number} - {name} ({distance}m)" if distance else f"Race {number} - {name}"

def handle_api_request(func, *args, **kwargs) -> Dict:
    """Generic API request handler with error handling"""
    try:
        response = func(*args, **kwargs)
        if isinstance(response, Dict):
            if 'error' in response:
                st.error(f"API Error: {response['error']}")
                return None
            return response
        return None
    except Exception as e:
        logger.error(f"API request failed: {str(e)}")
        st.error(f"Request failed: {str(e)}")
        return None

def format_date(date_obj) -> str:
    """Format date for API requests"""
    try:
        if isinstance(date_obj, datetime):
            return date_obj.strftime("%Y-%m-%d")
        elif isinstance(date_obj, str):
            return datetime.strptime(date_obj, "%Y-%m-%d").strftime("%Y-%m-%d")
        return date_obj.strftime("%Y-%m-%d")
    except Exception as e:
        logger.error(f"Date formatting error: {str(e)}")
        st.error("Invalid date format")
        return None

def main():
    st.title("🏇 Racing Analysis Platform")
    
    # Initialize components
    initialize_client()
    account_manager = AccountManager()
    betting_system = BettingSystemIntegration()
    race_info = RaceInformation(st.session_state.client)
    
    # Sidebar - Account Management
    account_manager.render_login()
    
    # Main navigation
    tabs = st.tabs([
        "Race Analysis",
        "Automated Betting",
        "Performance Analytics"
    ])
    
    with tabs[0]:
        # Race selection
        col1, col2 = st.columns(2)
        with col1:
            meeting_date = st.date_input(
                "Meeting Date",
                value=datetime.now(pytz.timezone('Australia/Sydney')).date(),
                min_value=datetime.now(pytz.timezone('Australia/Sydney')).date(),
                help="Select a date to view race meetings"
            )
        with col2:
            jurisdiction = st.selectbox(
                "Jurisdiction",
                ["NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"],
                help="Select a racing jurisdiction"
            )
        
        # Fetch and display races
        if meeting_date and jurisdiction:
            formatted_date = format_date(meeting_date)
            if formatted_date:
                meetings_response = handle_api_request(
                    st.session_state.client.get_meetings,
                    meeting_date=formatted_date,
                    jurisdiction=jurisdiction
                )
                
                if meetings_response and 'meetings' in meetings_response:
                    meetings = meetings_response['meetings']
                    if meetings:
                        selected_meeting = st.selectbox(
                            "Select Meeting",
                            options=meetings,
                            format_func=format_meeting_name,
                            help="Select a race meeting"
                        )
                        
                        if selected_meeting:
                            races_response = handle_api_request(
                                st.session_state.client.get_races_in_meeting,
                                meeting_date=formatted_date,
                                meeting_id=selected_meeting['id'],
                                jurisdiction=jurisdiction
                            )
                            
                            if races_response and 'races' in races_response:
                                races = races_response['races']
                                if races:
                                    selected_race = st.selectbox(
                                        "Select Race",
                                        options=races,
                                        format_func=format_race_name,
                                        help="Select a race to analyze"
                                    )
                                    
                                    if selected_race:
                                        with st.spinner("Loading race details..."):
                                            race_fields = handle_api_request(
                                                st.session_state.client.get_race_fields,
                                                race_id=selected_race['id'],
                                                include_form=True
                                            )
                                            
                                            if race_fields and not race_fields.get('error'):
                                                race_info.render_race_overview(race_fields)
                                                betting_system.process_race(race_fields)
                                else:
                                    st.info("No races available for this meeting")
                    else:
                        st.info("No meetings available for the selected date and jurisdiction")
    
    with tabs[1]:
        # Automated betting interface
        betting_system.render_betting_interface()
    
    with tabs[2]:
        # Performance analytics
        st.header("Performance Analytics")
        betting_system.betting_system.render_dashboard()

if __name__ == "__main__":
    main()
