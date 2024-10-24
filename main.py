import streamlit as st
import pandas as pd
from datetime import datetime
import openai
from openai import OpenAI
from utils.api_client import RacingAPIClient
from utils.data_processor import RaceDataProcessor
from utils.statistical_predictor import StatisticalPredictor
from components.form_guide import render_form_guide, create_speed_map
from components.predictions import render_predictions, create_confidence_chart
from typing import Dict

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
                
        elif isinstance(race_data, list) and race_data:
            first_runner = race_data[0]
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

def main():
    st.set_page_config(
        page_title="To The Bank - Racing Analysis",
        page_icon="🏇",
        layout="wide"
    )

    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'show_chat' not in st.session_state:
        st.session_state.show_chat = False

    st.markdown("""
        <h1 style='text-align: center; padding: 1rem; background-color: #FF4B4B; color: white;'>
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
    
    if st.session_state.show_chat:
        col1, col2, col3 = st.columns([3, 1, 1])
    else:
        col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("Form Guide")
        race_data = api_client.get_race_data(meeting_id, race_number)

        if not race_data:
            st.error("Unable to fetch race data")
            return

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

        render_form_guide(form_data)
        st.subheader("Speed Map")
        speed_map = create_speed_map(form_data)
        st.plotly_chart(speed_map, use_container_width=True)

        if track_bias:
            st.subheader("Track Bias Analysis")
            col_bias1, col_bias2 = st.columns(2)
            with col_bias1:
                st.metric("Inside Barrier Advantage", 
                         f"{track_bias['inside_advantage']:.2f}")
            with col_bias2:
                st.metric("Pace Bias", track_bias['pace_bias'])
    
    with col2:
        st.subheader("Race Details")
        race_info = extract_race_details(race_data)
        
        try:
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
        
        st.subheader("AI Predictions")
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
            st.subheader("Race Assistant")
            
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