import streamlit as st
from datetime import datetime, timedelta, timezone
import time
import logging
from typing import Optional, Dict, List
from utils.alerts import create_alert_system
from utils.api_client import RacingAPIClient
from utils.data_processor import RaceDataProcessor
from components.form_guide import render_form_guide, render_filter_panel
from components.speed_map import create_speed_map
from components.track_bias import create_track_bias_chart
from components.chat_assistant import render_chat_assistant

def setup_logging():
    """Initialize logging configuration"""
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)

def validate_date(date_str: str) -> bool:
    """Validate date string format and range"""
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        max_future = datetime.now() + timedelta(days=7)
        min_date = datetime.now() - timedelta(days=1)
        return min_date <= date <= max_future
    except ValueError:
        return False

def format_date_for_api(date: datetime) -> str:
    """Format date as YYYY-MM-DD for API calls"""
    return date.strftime("%Y-%m-%d")

def format_date_display(date: datetime) -> str:
    """Format date for display with full month name"""
    return date.strftime("%A, %d %B %Y")

def get_available_dates() -> List[datetime]:
    """Get list of available dates for selection"""
    today = datetime.now()
    return [
        today + timedelta(days=i)
        for i in range(-1, 8)  # From yesterday to 7 days ahead
    ]

def initialize_session_state():
    """Initialize all session state variables"""
    if 'alert_system' not in st.session_state:
        st.session_state.alert_system = create_alert_system()
    if 'filters' not in st.session_state:
        st.session_state.filters = {}
    if 'show_chat' not in st.session_state:
        st.session_state.show_chat = False
    if 'selected_date' not in st.session_state:
        st.session_state.selected_date = datetime.now().strftime("%Y-%m-%d")
    if 'loading_meetings' not in st.session_state:
        st.session_state.loading_meetings = False
    if 'selected_meeting' not in st.session_state:
        st.session_state.selected_meeting = None
    if 'race_number' not in st.session_state:
        st.session_state.race_number = 1

def main():
    logger = setup_logging()
    
    try:
        # Configure page settings
        st.set_page_config(
            page_title="To The Bank - Racing Analysis",
            page_icon="🏇",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Initialize session state
        initialize_session_state()

        # Initialize API client and check health
        api_client = RacingAPIClient()
        with st.spinner("Checking API connection..."):
            try:
                if not api_client.check_api_health():
                    st.error("Unable to connect to racing data service. Please try again later.")
                    return
            except Exception as e:
                st.error(f"API Connection Error: {str(e)}")
                return

        # Left Sidebar Navigation
        with st.sidebar:
            st.markdown("### Race Selection")
            st.markdown("---")

            try:
                # Date selector
                available_dates = get_available_dates()
                date_options = {format_date_display(d): d for d in available_dates}
                
                selected_date_label = st.selectbox(
                    "Select Date",
                    options=list(date_options.keys()),
                    index=1,  # Default to today
                    help="Select a date to view available meetings"
                )

                if selected_date_label:
                    selected_date = format_date_for_api(date_options[selected_date_label])
                    if not validate_date(selected_date):
                        st.error("Please select a date between yesterday and 7 days from now")
                        return
                    st.session_state.selected_date = selected_date

                # Meeting selector with loading state
                with st.spinner("Loading meetings..."):
                    try:
                        st.session_state.loading_meetings = True
                        meetings = api_client.get_meetings(st.session_state.selected_date)
                        st.session_state.loading_meetings = False

                        if meetings:
                            meeting_options = []
                            for meeting in meetings:
                                if isinstance(meeting, dict):
                                    track_name = meeting.get('track', {}).get('name', '')
                                    meeting_id = meeting.get('meetingId', '')
                                    if track_name and meeting_id:
                                        meeting_options.append(f"{track_name}: {meeting_id}")

                            if meeting_options:
                                st.markdown("### Available Meetings")
                                selected_meeting = st.selectbox(
                                    "Select Meeting",
                                    options=meeting_options,
                                    help="Choose a race meeting to analyze"
                                )
                                st.session_state.selected_meeting = selected_meeting
                            else:
                                st.warning("No valid meetings found for selected date")
                                st.session_state.selected_meeting = None
                        else:
                            st.warning("No meetings available for selected date")
                            st.session_state.selected_meeting = None
                    except Exception as e:
                        logger.error(f"Error fetching meetings: {str(e)}")
                        st.error("Unable to fetch meetings. Please try again later.")
                        st.session_state.selected_meeting = None
                    finally:
                        st.session_state.loading_meetings = False

                # Race selector
                if st.session_state.selected_meeting:
                    st.markdown("### Race Options")
                    race_number = st.number_input(
                        "Race Number",
                        min_value=1,
                        max_value=12,
                        value=1,
                        help="Enter race number (1-12)"
                    )
                    
                    if race_number != st.session_state.race_number:
                        st.session_state.race_number = race_number
                        st.experimental_rerun()

            except Exception as e:
                logger.error(f"Error in sidebar: {str(e)}")
                st.error("Error loading sidebar components. Please refresh the page.")
                return

        # Main content area
        if st.session_state.selected_meeting:
            try:
                meeting_id = st.session_state.selected_meeting.split(":")[1].strip()
                
                with st.spinner("Loading race data..."):
                    try:
                        race_data = api_client.get_race_data(meeting_id, st.session_state.race_number)
                        if race_data:
                            data_processor = RaceDataProcessor()
                            form_data = data_processor.prepare_form_guide(race_data)
                            
                            if form_data is not None and not form_data.empty:
                                render_form_guide(form_data)
                                
                                # Add Speed Map and Track Bias sections
                                col1, col2 = st.columns(2)
                                with col1:
                                    with st.expander("Speed Map", expanded=False):
                                        speed_map = create_speed_map(form_data)
                                        st.plotly_chart(speed_map, use_container_width=True)
                                
                                with col2:
                                    with st.expander("Track Bias Analysis", expanded=False):
                                        track_bias_chart = create_track_bias_chart({})
                                        st.plotly_chart(track_bias_chart, use_container_width=True)
                            else:
                                st.warning("No valid form guide data available for this race")
                        else:
                            st.error("Unable to fetch race data. Please try again.")
                    except Exception as e:
                        logger.error(f"Error processing race data: {str(e)}")
                        st.error("An error occurred while processing race data")
            except Exception as e:
                logger.error(f"Error parsing meeting ID: {str(e)}")
                st.error("Invalid meeting selection. Please choose a valid meeting.")

    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        st.error("An unexpected error occurred. Please refresh the page.")

if __name__ == "__main__":
    main()
