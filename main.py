import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import openai
from openai import OpenAI
from utils.api_client import RacingAPIClient
from utils.data_processor import RaceDataProcessor
from utils.statistical_predictor import StatisticalPredictor
from utils.export_utils import format_race_data, export_to_csv, export_to_json, export_to_text, export_to_pdf
from utils.alerts import create_alert_system
from components.form_guide import render_form_guide
from components.speed_map import create_speed_map
from components.track_bias import create_track_bias_chart
from components.predictions import render_predictions, create_confidence_chart
from typing import Dict
import time
import json

def extract_race_info(race_data):
    # Handle list format
    if isinstance(race_data, list):
        if race_data and isinstance(race_data[0], dict):
            return {
                'startTime': race_data[0].get('startTime', ''),
                'trackCondition': race_data[0].get('trackCondition', ''),
                'distance': race_data[0].get('distance', ''),
                'raceStatus': race_data[0].get('status', ''),
                'prizeMoney': race_data[0].get('prizeMoney', '0')
            }
        return {}
    
    # Handle dict format
    if isinstance(race_data, dict):
        if 'payLoad' in race_data:
            if isinstance(race_data['payLoad'], dict):
                return race_data['payLoad'].get('raceInfo', {})
            elif isinstance(race_data['payLoad'], list) and race_data['payLoad']:
                first_item = race_data['payLoad'][0]
                return {
                    'startTime': first_item.get('startTime', ''),
                    'trackCondition': first_item.get('trackCondition', ''),
                    'distance': first_item.get('distance', ''),
                    'raceStatus': first_item.get('status', '')
                }
    return {}

def main():
    st.set_page_config(
        page_title="To The Bank - Racing Analysis",
        page_icon="🏇",
        layout="wide"
    )

    # Initialize alert system
    alert_system = create_alert_system()

    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'show_chat' not in st.session_state:
        st.session_state.show_chat = False
    if 'previous_odds' not in st.session_state:
        st.session_state.previous_odds = {}
    if 'last_alert_time' not in st.session_state:
        st.session_state.last_alert_time = {}

    # Main header
    st.markdown('''
        <div class="header">
            <h1 style="margin:0; font-size: 2.5rem;">To The Bank</h1>
            <p style="margin:0; opacity:0.9;">Racing Analysis Platform</p>
        </div>
    ''', unsafe_allow_html=True)

    # Sidebar setup
    with st.sidebar:
        st.markdown('''
            <div style="padding: 1rem; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <h3 style="color: #1E88E5; margin-bottom: 1rem;">Race Selection</h3>
            </div>
        ''', unsafe_allow_html=True)
        
        today = datetime.now().strftime("%Y-%m-%d")
        api_client = RacingAPIClient()
        data_processor = RaceDataProcessor()
        
        meetings = api_client.get_meetings(today)
        if not meetings:
            st.error("No meetings available for today")
            return

        meeting_options = {
            f"{meeting.get('track', {}).get('name', 'Unknown Track')} - {meeting.get('meetingId')}": meeting.get('meetingId')
            for meeting in meetings if isinstance(meeting, dict) and meeting.get('meetingId')
        }

        if not meeting_options:
            st.error("No valid meetings found")
            return
        
        selected_meeting = st.selectbox(
            "Select Meeting",
            options=list(meeting_options.keys())
        )
        meeting_id = meeting_options[selected_meeting]
        
        race_number = st.number_input(
            "Race Number",
            min_value=1,
            max_value=12,
            value=1
        )

        # Auto-refresh toggle
        auto_refresh = st.checkbox("Enable Auto-refresh", value=False)
        if auto_refresh:
            st.info("Auto-refreshing every 30 seconds")
            time.sleep(30)
            st.rerun()

    # Create main columns for layout
    main_col1, main_col2 = st.columns([7, 3])

    with main_col1:
        race_data = api_client.get_race_data(meeting_id, race_number)
        if not race_data:
            st.error("Unable to fetch race data")
            return

        # Process race information with the new extraction function
        race_info = extract_race_info(race_data)
        form_data = data_processor.prepare_form_guide(race_data)

        # Add real-time alerts section
        with st.container():
            st.markdown('<div class="race-info-card">', unsafe_allow_html=True)
            st.subheader("🔔 Race Alerts")
            
            # Check for odds changes
            current_odds = {
                horse['Horse']: horse.get('fixed_odds', 0) 
                for _, horse in form_data.iterrows()
            }
            
            # Monitor odds changes with cooldown
            current_time = datetime.now()
            for horse, current in current_odds.items():
                if horse in st.session_state.previous_odds:
                    prev = st.session_state.previous_odds[horse]
                    if abs(current - prev) >= 2.0:
                        last_alert = st.session_state.last_alert_time.get(horse, datetime.min)
                        if (current_time - last_alert).total_seconds() > 300:  # 5-minute cooldown
                            direction = "shortened" if current < prev else "drifted"
                            alert_system.add_alert(
                                "odds",
                                f"{horse} has {direction} from {prev:.1f} to {current:.1f}",
                                "info"
                            )
                            st.session_state.last_alert_time[horse] = current_time
            
            # Update previous odds
            st.session_state.previous_odds = current_odds
            
            # Add time-based alerts
            race_time = race_info.get('startTime')
            if race_time:
                try:
                    race_time = datetime.strptime(race_time, "%Y-%m-%d %H:%M:%S")
                    alerts = alert_system.check_time_alerts(race_time)
                    for alert in alerts:
                        alert_system.add_alert(
                            alert['type'],
                            alert['message'],
                            alert['severity']
                        )
                except Exception as e:
                    st.warning(f"Unable to process race time alerts: {str(e)}")
            
            # Check race status alerts
            status_alerts = alert_system.check_race_status(race_data)
            for alert in status_alerts:
                alert_system.add_alert(
                    alert['type'],
                    alert['message'],
                    alert['severity']
                )
            
            # Check track condition changes
            track_condition = race_info.get('trackCondition', '')
            if 'previous_condition' not in st.session_state:
                st.session_state.previous_condition = track_condition
            elif track_condition != st.session_state.previous_condition:
                alert_system.add_alert(
                    "track",
                    f"Track condition changed from {st.session_state.previous_condition} to {track_condition}",
                    "warning"
                )
                st.session_state.previous_condition = track_condition
            
            # Render alerts in a grid layout
            with st.container():
                st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
                alert_system.render_alerts()
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Form Guide Section
        with st.container():
            st.markdown('<div class="race-info-card">', unsafe_allow_html=True)
            st.subheader("🏇 Race Form Guide")
            render_form_guide(form_data)
            st.markdown('</div>', unsafe_allow_html=True)

        # Speed Map Section
        with st.container():
            st.markdown('<div class="race-info-card">', unsafe_allow_html=True)
            st.subheader("🗺️ Speed Map")
            speed_map = create_speed_map(form_data)
            st.plotly_chart(speed_map, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    with main_col2:
        # Track Bias Section
        with st.container():
            st.markdown('<div class="race-info-card">', unsafe_allow_html=True)
            st.subheader("🎯 Track Bias Analysis")
            track_bias = {
                'barrier_bias': {},
                'style_bias': {},
                'inside_advantage': 0.0,
                'pace_bias': 'Neutral'
            }
            track_bias_chart = create_track_bias_chart(track_bias)
            st.plotly_chart(track_bias_chart, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Alerts Section
        with st.container():
            st.markdown('<div class="race-info-card">', unsafe_allow_html=True)
            st.subheader("🔔 Recent Alerts")
            alert_system.process_alerts()
            alert_system.render_alerts()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        '<p style="text-align: center; color: #666;">Data provided by PuntingForm API. '
        'Predictions are for entertainment purposes only.</p>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
