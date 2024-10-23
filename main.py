import streamlit as st
import pandas as pd
from datetime import datetime
from utils.api_client import RacingAPIClient
from utils.data_processor import RaceDataProcessor
from components.form_guide import render_form_guide, create_speed_map
from components.predictions import render_predictions, create_confidence_chart

def main():
    st.set_page_config(
        page_title="To The Bank - Racing Analysis",
        page_icon="🏇",
        layout="wide"
    )

    # Full-width header
    st.markdown("""
        <h1 style='text-align: center; padding: 1rem; background-color: #FF4B4B; color: white;'>
            To The Bank
        </h1>
    """, unsafe_allow_html=True)
    
    # Initialize API client and data processor
    api_client = RacingAPIClient()
    data_processor = RaceDataProcessor()
    
    # Sidebar navigation
    st.sidebar.title("Races")
    
    # Get today's meetings
    today = datetime.now().strftime("%Y-%m-%d")
    meetings = api_client.get_meetings(today)
    
    if not meetings:
        st.error("No meetings available for today")
        return

    # Meeting selection with proper structure handling
    meeting_options = {}
    for meeting in meetings:
        if 'track' in meeting and isinstance(meeting['track'], dict):
            track_name = meeting['track'].get('name', 'Unknown Track')
        else:
            track_name = meeting.get('meetingName', 'Unknown Track')
        
        meeting_id = meeting.get('meetingId')
        if meeting_id:
            meeting_options[f"{track_name} - {meeting_id}"] = meeting_id

    if not meeting_options:
        st.error("No valid meetings found")
        return
    
    selected_meeting = st.sidebar.selectbox(
        "Select Meeting",
        options=list(meeting_options.keys())
    )
    meeting_id = meeting_options[selected_meeting]
    
    # Race number selection
    race_number = st.sidebar.number_input(
        "Race Number",
        min_value=1,
        max_value=12,
        value=1
    )
    
    # Main content area with grid layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("Form Guide")
        
        # Fetch race data
        race_data = api_client.get_race_data(meeting_id, race_number)
        
        if not race_data:
            st.error("Unable to fetch race data")
            return
        
        # Process form data
        form_data = data_processor.prepare_form_guide(race_data)
        
        # Display form guide table
        render_form_guide(form_data)
        
        # Speed map visualization
        st.subheader("Speed Map")
        speed_map = create_speed_map(form_data)
        st.plotly_chart(speed_map, use_container_width=True)
    
    with col2:
        st.subheader("Race Details")
        race_info = race_data.get('payLoad', {}).get('raceInfo', {})
        
        # Display race metrics
        st.metric("Distance", f"{race_info.get('distance', 'Unknown')}m")
        st.metric("Track Condition", race_info.get('trackCondition', 'Unknown'))
        st.metric("Prize Money", f"${race_info.get('prizeMoney', 0):,}")
        
        # AI Predictions
        st.subheader("AI Predictions")
        predictions = [
            {
                'horse': row['Horse'],
                'score': row['Rating'],
                'barrier': row['Barrier'],
                'jockey': row['Jockey']
            }
            for _, row in form_data.nlargest(3, 'Rating').iterrows()
        ]
        
        render_predictions(predictions)
        
        # Confidence chart
        confidence_chart = create_confidence_chart(predictions)
        st.plotly_chart(confidence_chart, use_container_width=True)
    
    # Add auto-refresh functionality
    if st.sidebar.button("Refresh Data"):
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "Data provided by PuntingForm API. Predictions are for entertainment purposes only."
    )

if __name__ == "__main__":
    main()
