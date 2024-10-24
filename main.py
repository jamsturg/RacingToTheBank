import streamlit as st
from datetime import datetime
import pytz
from typing import Dict, List
import logging
from tab_api_client import TABApiClient, RaceType
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

def initialize_client():
    """Initialize TAB API client"""
    if st.session_state.client is None:
        try:
            bearer_token = st.secrets.get("TAB_BEARER_TOKEN")
            if not bearer_token:
                bearer_token = st.text_input(
                    "Enter TAB Bearer Token",
                    type="password"
                )
                if not bearer_token:
                    st.warning("Please enter your TAB Bearer Token to continue")
                    st.stop()
            
            st.session_state.client = TABApiClient(bearer_token)
        except Exception as e:
            st.error(f"Failed to initialize client: {str(e)}")
            st.stop()

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
        col1, col2, col3 = st.columns(3)
        with col1:
            meeting_date = st.date_input(
                "Meeting Date",
                value=datetime.now(pytz.timezone('Australia/Sydney')).date()
            )
        with col2:
            jurisdiction = st.selectbox(
                "Jurisdiction",
                ["NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"]
            )
        with col3:
            race_type = st.selectbox(
                "Race Type",
                [rt.name for rt in RaceType]
            )
        
        # Fetch and display races
        try:
            meetings = st.session_state.client.get_meetings(
                meeting_date=meeting_date.strftime("%Y-%m-%d"),
                jurisdiction=jurisdiction
            )
            
            if meetings and 'meetings' in meetings:
                selected_meeting = st.selectbox(
                    "Select Meeting",
                    options=meetings['meetings'],
                    format_func=lambda x: x['venueName']
                )
                
                if selected_meeting:
                    races = st.session_state.client.get_races_in_meeting(
                        meeting_date=meeting_date.strftime("%Y-%m-%d"),
                        race_type=getattr(RaceType, race_type).value,
                        venue_mnemonic=selected_meeting['venueMnemonic'],
                        jurisdiction=jurisdiction
                    )
                    
                    if races and 'races' in races:
                        selected_race = st.selectbox(
                            "Select Race",
                            options=races['races'],
                            format_func=lambda x: f"Race {x['raceNumber']} - {x.get('raceName', '')}"
                        )
                        
                        if selected_race:
                            race_info.render_race_overview(selected_race)
                            
                            # Process race for betting opportunities
                            betting_system.process_race(selected_race)
                            
        except Exception as e:
            st.error(f"Error loading races: {str(e)}")
    
    with tabs[1]:
        # Automated betting interface
        betting_system.render_betting_interface()
    
    with tabs[2]:
        # Performance analytics
        st.header("Performance Analytics")
        betting_system.betting_system.render_dashboard()

if __name__ == "__main__":
    main()
