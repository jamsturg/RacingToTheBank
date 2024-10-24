import streamlit as st
from datetime import datetime
import time
from utils.alerts import create_alert_system
from utils.api_client import RacingAPIClient
from utils.data_processor import RaceDataProcessor
from components.form_guide import render_form_guide, render_filter_panel
from components.speed_map import create_speed_map
from components.track_bias import create_track_bias_chart
from components.chat_assistant import render_chat_assistant

def main():
    # Initialize form_data and session state
    form_data = None
    
    st.set_page_config(
        page_title="To The Bank - Racing Analysis",
        page_icon="🏇",
        layout="wide"
    )

    # Initialize session state
    if 'alert_system' not in st.session_state:
        st.session_state.alert_system = create_alert_system()
    if 'filters' not in st.session_state:
        st.session_state.filters = {}
    if 'show_chat' not in st.session_state:
        st.session_state.show_chat = False

    # Left Sidebar Navigation
    st.sidebar.markdown("### Quick Navigation")
    st.sidebar.markdown("---")

    # Initialize API client and fetch meetings
    api_client = RacingAPIClient()
    with st.sidebar:
        with st.spinner("Loading meetings..."):
            try:
                meetings = api_client.get_meetings()
                if meetings:
                    # Create meeting options with proper error handling
                    meeting_options = []
                    for meeting in meetings:
                        if isinstance(meeting, dict):
                            track_name = meeting.get('track', {}).get('name', '')
                            meeting_id = meeting.get('meetingId', '')
                            if track_name and meeting_id:
                                meeting_options.append(f"{track_name}: {meeting_id}")
                    
                    if meeting_options:
                        selected_meeting = st.selectbox(
                            "Select Meeting",
                            meeting_options
                        )
                    else:
                        st.error("No valid meetings found")
                        selected_meeting = None
                else:
                    st.error("No meetings available")
                    selected_meeting = None
            except Exception as e:
                st.error(f"Error loading meetings: {str(e)}")
                selected_meeting = None

        race_number = st.number_input("Race Number", min_value=1, max_value=12, value=1)
        auto_refresh = st.checkbox("Auto Refresh", value=False)
        
        # Chat Assistant Toggle
        st.markdown("---")
        chat_toggle = st.checkbox("Show Chat Assistant", value=st.session_state.show_chat)

    # Main header
    st.markdown('''
        <div style="text-align: center; padding: 1rem; background: linear-gradient(90deg, #1E88E5 0%, #64B5F6 100%); 
                    color: white; border-radius: 10px; margin-bottom: 1rem;">
            <h1 style="margin:0;">To The Bank</h1>
            <p style="margin:0.5rem 0 0 0;">Racing Analysis Platform</p>
        </div>
    ''', unsafe_allow_html=True)

    # Main Content Area
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # Form Guide (Centerpiece)
    if selected_meeting and selected_meeting != "No meetings available":
        with st.spinner("Loading race data..."):
            try:
                data_processor = RaceDataProcessor()
                meeting_id = selected_meeting.split(":")[1].strip()
                race_data = api_client.get_race_data(meeting_id, race_number)
                
                if race_data:
                    form_data = data_processor.prepare_form_guide(race_data)
                    if not form_data.empty:
                        render_form_guide(form_data)
                    else:
                        st.warning("No form guide data available for this race")
                else:
                    st.error("Unable to fetch race data")
            except Exception as e:
                st.error(f"Error processing race data: {str(e)}")
    else:
        st.info("Please select a meeting to view the form guide")

    # Collapsible Sections
    if form_data is not None and not form_data.empty:
        with st.expander("Speed Map", expanded=False):
            speed_map = create_speed_map(form_data)
            st.plotly_chart(speed_map, use_container_width=True)

        with st.expander("Track Bias Analysis", expanded=False):
            track_bias_chart = create_track_bias_chart({})
            st.plotly_chart(track_bias_chart, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Chat Assistant
    if chat_toggle:
        st.session_state.show_chat = True
        with st.sidebar:
            st.markdown("### Chat Assistant")
            st.text_input("Ask about race analysis:", key="chat_input")
            if st.button("Send"):
                if st.session_state.chat_input:
                    st.write(f"You: {st.session_state.chat_input}")
    else:
        st.session_state.show_chat = False

    # Render Filter Panel
    render_filter_panel()

    # Auto-refresh
    if auto_refresh:
        time.sleep(30)
        st.rerun()

if __name__ == "__main__":
    main()
