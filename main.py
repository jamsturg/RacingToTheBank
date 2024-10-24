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
from components.form_guide import render_form_guide, create_speed_map
from components.predictions import render_predictions, create_confidence_chart
from typing import Dict
import time
import json

client = OpenAI()

def extract_race_details(race_data) -> Dict:
    try:
        race_info = {}
        
        if isinstance(race_data, dict):
            payload = race_data.get('payLoad', {})
            if isinstance(payload, dict):
                race_info = payload.get('raceInfo', {})
                if not race_info and 'runners' in payload and payload['runners']:
                    first_runner = payload['runners'][0]
                    race_info = {
                        'distance': first_runner.get('distance', ''),
                        'trackCondition': first_runner.get('trackCondition', ''),
                        'prizeMoney': first_runner.get('prizeMoney', 0),
                        'raceType': first_runner.get('raceType', ''),
                        'raceTime': first_runner.get('raceTime', '')
                    }
            elif isinstance(payload, list) and payload:
                first_runner = payload[0]
                race_info = {
                    'distance': first_runner.get('distance', ''),
                    'trackCondition': first_runner.get('trackCondition', ''),
                    'prizeMoney': first_runner.get('prizeMoney', 0),
                    'raceType': first_runner.get('raceType', ''),
                    'raceTime': first_runner.get('raceTime', '')
                }
                
        return race_info
    except Exception as e:
        print(f"Error extracting race details: {str(e)}")
        return {}

def get_ai_response(prompt: str, race_context: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a horse racing expert assistant. Current race context: {race_context}"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"I apologize, I'm having trouble processing your request: {str(e)}"

def extract_odds(race_data) -> Dict:
    """Extract current odds from race data"""
    odds = {}
    try:
        if isinstance(race_data, dict):
            payload = race_data.get('payLoad', {})
            runners = payload.get('runners', []) if isinstance(payload, dict) else payload
            
            for runner in runners:
                if isinstance(runner, dict):
                    horse_name = runner.get('name', runner.get('horseName', ''))
                    fixed_odds = runner.get('fixedOdds', {})
                    if isinstance(fixed_odds, dict):
                        current_price = float(fixed_odds.get('currentPrice', 0))
                        odds[horse_name] = current_price
    except Exception as e:
        print(f"Error extracting odds: {str(e)}")
    return odds

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

    st.markdown("""
        <h1 style='text-align: center; padding: 1rem; background-color: #1E88E5; color: white;'>
            To The Bank
        </h1>
    """, unsafe_allow_html=True)
    
    api_client = RacingAPIClient()
    data_processor = RaceDataProcessor()
    statistical_predictor = StatisticalPredictor()
    
    st.sidebar.title("Races")
    st.session_state.show_chat = st.sidebar.checkbox("Show Chat Assistant", value=st.session_state.show_chat)
    
    today = datetime.now().strftime("%Y-%m-%d")
    meetings = api_client.get_meetings(today)
    
    if not meetings:
        st.error("No meetings available for today")
        return

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
    
    race_number = st.sidebar.number_input(
        "Race Number",
        min_value=1,
        max_value=12,
        value=1
    )

    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Enable Auto-refresh", value=False)
    if auto_refresh:
        st.sidebar.info("Auto-refreshing every 30 seconds")
        time.sleep(30)
        st.experimental_rerun()
    
    if st.session_state.show_chat:
        col1, col2, col3 = st.columns([2, 1, 1])
    else:
        col1, col2 = st.columns([2, 1])
    
    with col1:
        race_data = api_client.get_race_data(meeting_id, race_number)

        if not race_data:
            st.error("Unable to fetch race data")
            return

        # Process alerts
        current_odds = extract_odds(race_data)
        
        # Check for odds changes
        if st.session_state.previous_odds:
            odds_alerts = alert_system.check_odds_changes(current_odds, st.session_state.previous_odds)
            for alert in odds_alerts:
                alert_system.add_alert(alert["type"], alert["message"], alert["severity"])
        
        st.session_state.previous_odds = current_odds
        
        # Check race status
        status_alerts = alert_system.check_race_status(race_data)
        for alert in status_alerts:
            alert_system.add_alert(alert["type"], alert["message"], alert["severity"])
        
        # Check time alerts
        race_info = extract_race_details(race_data)
        if race_info.get('raceTime'):
            try:
                race_time = datetime.strptime(race_info['raceTime'], "%Y-%m-%d %H:%M:%S")
                time_alerts = alert_system.check_time_alerts(race_time)
                for alert in time_alerts:
                    alert_system.add_alert(alert["type"], alert["message"], alert["severity"])
            except Exception as e:
                print(f"Error processing time alerts: {str(e)}")

        # Process and display alerts
        alert_system.process_alerts()
        alert_system.render_alerts()

        form_data = data_processor.prepare_form_guide(race_data)
        
        if not form_data.empty:
            recent_results = []
            track_bias = statistical_predictor.calculate_track_bias(recent_results)
            
            predictions = []
            for _, horse in form_data.iterrows():
                horse_dict = horse.to_dict()
                prediction = statistical_predictor.predict_performance(
                    horse_dict, track_bias, recent_results
                )
                seasonal_patterns = statistical_predictor.analyze_seasonal_patterns(
                    horse_dict.get('performance_history', [])
                )
                predictions.append({
                    'horse': horse_dict['Horse'],
                    'rating': prediction.get('rating', 0),
                    'confidence': prediction.get('model_agreement', 'Unknown'),
                    'trend': seasonal_patterns.get('trend', 'Unknown'),
                    'seasonal_effect': seasonal_patterns.get('seasonal_effect', False)
                })
            
            prediction_df = pd.DataFrame(predictions)
            form_data = form_data.merge(
                prediction_df, left_on='Horse', right_on='horse', how='left'
            )

            # Export options
            with st.expander("Export Options", expanded=False):
                col_export1, col_export2, col_export3, col_export4 = st.columns(4)
                
                with col_export1:
                    csv_data = export_to_csv(form_data)
                    st.download_button(
                        "Download CSV",
                        csv_data,
                        "form_guide.csv",
                        "text/csv",
                        key='download-csv'
                    )
                
                with col_export2:
                    export_data = format_race_data(form_data, predictions, race_info)
                    json_data = export_to_json(export_data)
                    st.download_button(
                        "Download JSON",
                        json_data,
                        "race_analysis.json",
                        "application/json",
                        key='download-json'
                    )
                
                with col_export3:
                    text_report = export_to_text(export_data)
                    st.download_button(
                        "Download TXT",
                        text_report,
                        "race_analysis.txt",
                        "text/plain",
                        key='download-txt'
                    )
                    
                with col_export4:
                    pdf_data = export_to_pdf(export_data)
                    if pdf_data:
                        st.download_button(
                            "Download PDF",
                            pdf_data,
                            "race_analysis.pdf",
                            "application/pdf",
                            key='download-pdf'
                        )

            with st.expander("Form Guide", expanded=True):
                render_form_guide(form_data)
            
            with st.expander("Speed Map", expanded=False):
                st.subheader("Speed Map")
                speed_map = create_speed_map(form_data)
                st.plotly_chart(speed_map, use_container_width=True)

            if track_bias:
                with st.expander("Track Bias Analysis", expanded=False):
                    col_bias1, col_bias2 = st.columns(2)
                    with col_bias1:
                        st.metric("Inside Barrier Advantage", 
                                f"{track_bias['inside_advantage']:.2f}")
                    with col_bias2:
                        st.metric("Pace Bias", track_bias['pace_bias'])
    
    with col2:
        with st.expander("Race Details", expanded=True):
            try:
                race_info = extract_race_details(race_data)
                
                distance = race_info.get('distance', '')
                if isinstance(distance, (int, float)):
                    st.metric("Distance", f"{distance}m")
                elif isinstance(distance, str) and distance:
                    st.metric("Distance", distance)
                else:
                    st.metric("Distance", "Not available")
                    
                track_condition = race_info.get('trackCondition', '')
                st.metric("Track Condition", 
                         track_condition if track_condition else "Not available")
                
                prize_money = race_info.get('prizeMoney', 0)
                if isinstance(prize_money, (int, float)):
                    st.metric("Prize Money", f"${prize_money:,.2f}")
                else:
                    st.metric("Prize Money", "Not available")
                    
                race_type = race_info.get('raceType', '')
                if race_type:
                    st.metric("Race Type", race_type)
                    
                race_time = race_info.get('raceTime', '')
                if race_time:
                    st.metric("Race Time", race_time)
                    
            except Exception as e:
                st.error(f"Error displaying race details: {str(e)}")
        
        with st.expander("AI Predictions", expanded=True):
            try:
                if not form_data.empty and 'Horse' in form_data.columns and 'Rating' in form_data.columns:
                    predictions = [
                        {
                            'horse': str(row['Horse']),
                            'score': float(row['Rating']) if pd.notnull(row['Rating']) else 0,
                            'barrier': str(row['Barrier']) if 'Barrier' in form_data.columns else 'Unknown',
                            'jockey': str(row['Jockey']) if 'Jockey' in form_data.columns else 'Unknown'
                        }
                        for _, row in form_data.nlargest(3, 'Rating').iterrows()
                    ]
                    
                    if predictions:
                        render_predictions(predictions)
                        confidence_chart = create_confidence_chart(predictions)
                        st.plotly_chart(confidence_chart, use_container_width=True)
                    else:
                        st.warning("No valid predictions available")
                else:
                    st.warning("Insufficient data for predictions")
            except Exception as e:
                st.error(f"Error generating predictions: {str(e)}")
    
    if st.session_state.show_chat:
        with col3:
            with st.expander("Race Assistant", expanded=True):
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
                
                if prompt := st.chat_input("Ask about the race..."):
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    
                    race_context = f"Race at {selected_meeting.split(' - ')[0]}, Race {race_number}. "
                    if not form_data.empty:
                        top_horses = form_data.nlargest(3, 'Rating')['Horse'].tolist()
                        race_context += f"Top 3 rated horses: {', '.join(top_horses)}"
                    
                    response = get_ai_response(prompt, race_context)
                    st.session_state.messages.append({"role": "assistant", "content": response})
    
    if st.sidebar.button("Refresh Data"):
        st.rerun()
    
    st.markdown("---")
    st.markdown(
        "Data provided by PuntingForm API. Predictions are for entertainment purposes only."
    )

if __name__ == "__main__":
    main()
