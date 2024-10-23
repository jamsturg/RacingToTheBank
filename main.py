import streamlit as st
import pandas as pd
from datetime import datetime
from utils.api_client import RacingAPIClient
from utils.data_processor import RaceDataProcessor
from components.form_guide import render_form_guide, create_speed_map
from components.predictions import render_predictions, create_confidence_chart
import requests

def get_tab_odds(meeting_id: str, race_number: int):
    """Fetch odds data from TAB API"""
    try:
        url = f"https://api.beta.tab.com.au/v1/tab-info-service/racing/dates/2024-10-23/meetings/{meeting_id}/races/{race_number}/win"
        headers = {
            "Accept": "application/json",
            "User-Agent": "RacingAnalysisPlatform/1.0"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching odds: {str(e)}")
        return None

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
    
    # Meeting selection with reverted code
    meeting_options = {
        f"{m['venueName']} - {m['meetingId']}": m['meetingId']
        for m in meetings
    }
    
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
    
    # Main content with responsive layout
    st.title("Racing Analysis Platform")
    
    # Fetch race data
    race_data = api_client.get_race_data(meeting_id, race_number)
    odds_data = get_tab_odds(meeting_id, race_number)
    
    if not race_data:
        st.error("Unable to fetch race data")
        return
    
    # Display race information in a responsive grid
    st.markdown("""
        <style>
        .race-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns([1,1,1,1])
    
    race_info = race_data.get('payLoad', {}).get('raceInfo', {})
    with col1:
        distance = race_info.get('distance', 'Unknown')
        st.metric("Distance", f"{distance}m" if distance != 'Unknown' else distance)
    with col2:
        st.metric("Track Condition", race_info.get('trackCondition', 'Unknown'))
    with col3:
        prize_money = race_info.get('prizeMoney', 0)
        st.metric("Prize Money", f"${prize_money:,}" if prize_money else "Unknown")
    with col4:
        rail_position = race_info.get('railPosition', 'Unknown')
        st.metric("Rail Position", rail_position)
    
    # Create tabs for different views
    form_tab, speed_tab, predictions_tab = st.tabs(["Form Guide", "Speed Map", "Predictions"])
    
    # Process form data with odds integration
    form_data = data_processor.prepare_form_guide(race_data)
    if odds_data:
        # Add odds data to form guide
        runners_odds = {
            runner['tab_no']: runner['price_win']
            for runner in odds_data.get('runners', [])
        }
        form_data['Fixed Odds'] = form_data['Number'].map(runners_odds)
    
    # Display content in tabs
    with form_tab:
        render_form_guide(form_data)
    
    with speed_tab:
        speed_map = create_speed_map(form_data)
        st.plotly_chart(speed_map, use_container_width=True)
    
    with predictions_tab:
        # Generate and display predictions
        predictions = [
            {
                'horse': row['Horse'],
                'score': row['Rating'],
                'barrier': row['Barrier'],
                'jockey': row['Jockey'],
                'odds': row.get('Fixed Odds', 'N/A')
            }
            for _, row in form_data.nlargest(3, 'Rating').iterrows()
        ]
        
        render_predictions(predictions)
        confidence_chart = create_confidence_chart(predictions)
        st.plotly_chart(confidence_chart, use_container_width=True)
    
    # Add auto-refresh functionality
    if st.sidebar.button("Refresh Data"):
        st.experimental_rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "Data provided by PuntingForm API. Predictions are for entertainment purposes only."
    )

if __name__ == "__main__":
    main()
