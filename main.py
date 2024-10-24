import streamlit as st
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, List
from utils.alerts import create_alert_system
from utils.api_client import RacingAPIClient
from utils.data_processor import RaceDataProcessor
from components.form_guide import render_form_guide
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
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        max_future = datetime.now().date() + timedelta(days=7)
        min_date = datetime.now().date() - timedelta(days=1)
        return min_date <= date <= max_future
    except ValueError:
        return False

def format_date_display(date_str: str) -> str:
    """Format date for display"""
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        return date.strftime("%A, %d %B %Y")
    except ValueError:
        return date_str

def initialize_session_state():
    """Initialize all session state variables"""
    if 'alert_system' not in st.session_state:
        st.session_state.alert_system = create_alert_system()
    if 'filters' not in st.session_state:
        st.session_state.filters = {}
    if 'selected_date' not in st.session_state:
        st.session_state.selected_date = datetime.now().strftime("%Y-%m-%d")
    if 'selected_meeting' not in st.session_state:
        st.session_state.selected_meeting = None
    if 'race_number' not in st.session_state:
        st.session_state.race_number = 1
    if 'api_client' not in st.session_state:
        st.session_state.api_client = RacingAPIClient()
    if 'data_processor' not in st.session_state:
        st.session_state.data_processor = RaceDataProcessor()

def get_available_dates() -> List[str]:
    """Get list of available dates"""
    today = datetime.now().date()
    dates = [(today + timedelta(days=i)) for i in range(-1, 8)]
    return [d.strftime("%Y-%m-%d") for d in dates]

def main():
    logger = setup_logging()
    
    try:
        # Configure page settings
        st.set_page_config(
            page_title="Racing Analysis Platform",
            page_icon="🏇",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Initialize session state
        initialize_session_state()

        # Check API health
        with st.spinner("Checking API connection..."):
            try:
                if not st.session_state.api_client.check_api_health():
                    st.error("Unable to connect to racing data service. Please try again later.")
                    return
            except Exception as e:
                st.error(f"API Connection Error: {str(e)}")
                return

        # Sidebar Navigation
        with st.sidebar:
            st.markdown("### Race Selection")
            st.markdown("---")

            try:
                # Date selector with improved formatting
                available_dates = get_available_dates()
                date_options = {format_date_display(d): d for d in available_dates}
                
                selected_date_display = st.selectbox(
                    "Select Date",
                    options=list(date_options.keys()),
                    index=1  # Default to today
                )

                if selected_date_display:
                    selected_date = date_options[selected_date_display]
                    if validate_date(selected_date):
                        st.session_state.selected_date = selected_date
                    else:
                        st.error("Invalid date selection")
                        return

                # Meeting selector with loading state
                try:
                    with st.spinner("Loading meetings..."):
                        meetings = st.session_state.api_client.get_meetings(st.session_state.selected_date)
                        
                        if meetings:
                            meeting_options = []
                            for meeting in meetings:
                                if isinstance(meeting, dict):
                                    track = meeting.get('track', {})
                                    track_name = track.get('name', '')
                                    meeting_id = meeting.get('meetingId', '')
                                    
                                    if track_name and meeting_id:
                                        meeting_options.append({
                                            'label': f"{track_name}",
                                            'value': f"{track_name}:{meeting_id}"
                                        })

                            if meeting_options:
                                meeting_labels = [m['label'] for m in meeting_options]
                                meeting_values = [m['value'] for m in meeting_options]
                                
                                selected_index = 0
                                if st.session_state.selected_meeting:
                                    try:
                                        selected_index = meeting_values.index(st.session_state.selected_meeting)
                                    except ValueError:
                                        selected_index = 0

                                selected_meeting_label = st.selectbox(
                                    "Select Meeting",
                                    options=meeting_labels,
                                    index=selected_index
                                )

                                selected_idx = meeting_labels.index(selected_meeting_label)
                                st.session_state.selected_meeting = meeting_values[selected_idx]
                            else:
                                st.warning("No meetings available")
                                st.session_state.selected_meeting = None
                        else:
                            st.warning("No meetings found for selected date")
                            st.session_state.selected_meeting = None

                except Exception as e:
                    logger.error(f"Error loading meetings: {str(e)}")
                    st.error("Unable to load meetings. Please try again.")
                    st.session_state.selected_meeting = None

                # Race selector
                if st.session_state.selected_meeting:
                    st.markdown("### Race Details")
                    race_number = st.number_input(
                        "Race Number",
                        min_value=1,
                        max_value=12,
                        value=st.session_state.race_number
                    )
                    
                    if race_number != st.session_state.race_number:
                        st.session_state.race_number = race_number
                        st.rerun()

            except Exception as e:
                logger.error(f"Error in sidebar: {str(e)}")
                st.error("Error loading sidebar components")
                return

        # Main content area
        if st.session_state.selected_meeting:
            try:
                meeting_id = st.session_state.selected_meeting.split(":")[1].strip()
                
                with st.spinner("Loading race data..."):
                    try:
                        race_data = st.session_state.api_client.get_race_data(
                            meeting_id, 
                            st.session_state.race_number
                        )
                        
                        if race_data:
                            form_data = st.session_state.data_processor.prepare_form_guide(race_data)
                            
                            if form_data is not None and not form_data.empty:
                                render_form_guide(form_data)
                                
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
                                st.warning("No form guide data available")
                        else:
                            st.error("Unable to fetch race data")
                    except Exception as e:
                        logger.error(f"Error processing race data: {str(e)}")
                        st.error("Error processing race data")
            except Exception as e:
                logger.error(f"Error parsing meeting ID: {str(e)}")
                st.error("Invalid meeting selection")

    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        st.error("An unexpected error occurred")

if __name__ == "__main__":
    main()
