import streamlit as st
import pandas as pd
from datetime import datetime
from utils.api_client import RacingAPIClient
from utils.data_processor import RaceDataProcessor
from components.form_guide import render_form_guide, create_speed_map
from components.predictions import render_predictions, create_confidence_chart

def main():
    st.set_page_config(
        page_title="Racing Analysis Platform",
        page_icon="🏇",
        layout="wide"
    )
    
    # Initialize API client and data processor
    api_client = RacingAPIClient()
    data_processor = RaceDataProcessor()
    
    # Sidebar navigation
    st.sidebar.title("Race Selection")
    
    # Get today's meetings
    today = datetime.now().strftime("%Y-%m-%d")
    meetings = api_client.get_meetings(today)
    
    if not meetings:
        st.error("No meetings available for today")
        return
    
    try:
        # Meeting selection with proper error handling
        meeting_options = {}
        if isinstance(meetings, list):
            for m in meetings:
                if isinstance(m, dict):
                    venue_name = m.get('venueName', 'Unknown Track')
                    meeting_id = m.get('meetingId', '')
                    if meeting_id:
                        meeting_options[f"{venue_name} - {meeting_id}"] = meeting_id
                else:
                    st.error("Invalid meeting data structure")
        else:
            st.error("No meetings data available")
        
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
        
        # Main content
        st.title("Racing Analysis Platform")
        
        # Fetch race data
        race_data = api_client.get_race_data(meeting_id, race_number)
        
        if not race_data:
            st.error("Unable to fetch race data")
            return
        
        # Display race information with proper error handling
        race_info = race_data.get('payLoad', {}).get('raceInfo', {})
        col1, col2, col3 = st.columns(3)
        
        with col1:
            distance = race_info.get('distance', 'Unknown')
            st.metric("Distance", f"{distance}m" if distance != 'Unknown' else distance)
        with col2:
            st.metric("Track Condition", race_info.get('trackCondition', 'Unknown'))
        with col3:
            prize_money = race_info.get('prizeMoney', 0)
            st.metric("Prize Money", f"${prize_money:,}" if prize_money else "Unknown")
        
        # Process and display form guide
        form_data = data_processor.prepare_form_guide(race_data)
        render_form_guide(form_data)
        
        # Create and display speed map
        st.subheader("Speed Map")
        speed_map = create_speed_map(form_data)
        st.plotly_chart(speed_map)
        
        # Generate and display predictions
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
        
        # Display confidence chart
        confidence_chart = create_confidence_chart(predictions)
        st.plotly_chart(confidence_chart)
        
        # Add auto-refresh functionality
        st.sidebar.button("Refresh Data")
        
        # Footer
        st.markdown("---")
        st.markdown(
            "Data provided by PuntingForm API. Predictions are for entertainment purposes only."
        )
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
