import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from tab_api_client import TABApiClient, RaceType, APIError
import pytz
import json
from typing import Dict, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="TAB Racing Dashboard",
    page_icon="🏇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'client' not in st.session_state:
    st.session_state.client = None
if 'selected_race' not in st.session_state:
    st.session_state.selected_race = None
if 'bet_slip' not in st.session_state:
    st.session_state.bet_slip = []

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

def format_odds(odds: float) -> str:
    """Format odds with proper styling"""
    return f"${odds:.2f}" if odds else "N/A"

def display_next_races():
    """Display next races section"""
    st.header("Next Races")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        jurisdiction = st.selectbox(
            "Jurisdiction",
            ["NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"]
        )
    with col2:
        max_races = st.number_input(
            "Number of Races",
            min_value=1,
            max_value=20,
            value=5
        )
    with col3:
        include_fixed_odds = st.checkbox("Include Fixed Odds", value=True)
    
    try:
        next_races = st.session_state.client.get_next_to_go_races(
            jurisdiction=jurisdiction,
            max_races=max_races,
            include_fixed_odds=include_fixed_odds
        )
    except Exception as e:
        st.error(f"Failed to fetch next races: {str(e)}")
    
    for race in next_races.get("races", []):
        with st.expander(
            f"Race {race['raceNumber']} - {race['meeting']['venueName']} "
            f"({race['raceDistance']}m) - {race['raceStartTime']}"
        ):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Runners table
                runners_data = []
                for runner in race.get("runners", []):
                    fixed_odds = runner.get("fixedOdds", {}).get("returnWin")
                    runners_data.append({
                        "No.": runner["runnerNumber"],
                        "Name": runner["runnerName"],
                        "Barrier": runner.get("barrier", ""),
                        "Fixed Odds": format_odds(fixed_odds)
                    })
                
                df = pd.DataFrame(runners_data)
                st.dataframe(df, use_container_width=True)
            
            with col2:
                # Quick bet interface
                st.subheader("Place Bet")
                runner = st.selectbox(
                    "Select Runner",
                    options=[r["Name"] for r in runners_data],
                    key=f"runner_{race['raceNumber']}"
                )
                
                bet_type = st.selectbox(
                    "Bet Type",
                    ["Win", "Place", "Each Way"],
                    key=f"bet_type_{race['raceNumber']}"
                )
                
                stake = st.number_input(
                    "Stake ($)",
                    min_value=1.0,
                    max_value=1000.0,
                    value=10.0,
                    key=f"stake_{race['raceNumber']}"
                )
                
                if st.button(
                    "Add to Bet Slip",
                    key=f"add_bet_{race['raceNumber']}"
                ):
                    runner_data = next(
                        r for r in runners_data
                        if r["Name"] == runner
                    )
                    bet = {
                        "race": race["raceNumber"],
                        "venue": race["meeting"]["venueName"],
                        "runner": runner,
                        "runner_number": runner_data["No."],
                        "odds": runner_data["Fixed Odds"],
                        "bet_type": bet_type,
                        "stake": stake
                    }
                    st.session_state.bet_slip.append(bet)
                    st.success("Added to bet slip!")

def display_race_form():
    """Display race form section"""
    st.header("Race Form")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        meeting_date = st.date_input(
            "Meeting Date",
            value=datetime.now(pytz.timezone('Australia/Sydney')).date()
        )
    with col2:
        race_type = st.selectbox(
            "Race Type",
            options=[rt.name for rt in RaceType]
        )
    with col3:
        venue = st.text_input(
            "Venue Code",
            placeholder="e.g., RAN"
        ).upper()
    with col4:
        race_number = st.number_input(
            "Race Number",
            min_value=1,
            max_value=20,
            value=1
        )
    
    if all([meeting_date, race_type, venue, race_number]):
        try:
            race_form = st.session_state.client.get_race_form(
                meeting_date=meeting_date.strftime("%Y-%m-%d"),
                race_type=getattr(RaceType, race_type).value,
                venue_mnemonic=venue,
                race_number=race_number,
                jurisdiction="NSW",
                fixed_odds=True
            )
            
            if race_form:
                # Display form data
                tabs = st.tabs(["Runners", "Speed Map", "Track Info"])
                
                with tabs[0]:
                    if "runners" in race_form:
                        for runner in race_form["runners"]:
                            with st.expander(
                                f"{runner['runnerNumber']}. {runner['runnerName']}"
                            ):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write("**Basic Info**")
                                    st.write(f"Barrier: {runner.get('barrier', 'N/A')}")
                                    st.write(f"Weight: {runner.get('weight', 'N/A')}")
                                    st.write(f"Jockey: {runner.get('jockey', 'N/A')}")
                                
                                with col2:
                                    st.write("**Form**")
                                    st.write(f"Last Starts: {runner.get('last20Starts', 'N/A')}")
                                    st.write(f"Career: {runner.get('careerRecord', 'N/A')}")
                
                with tabs[1]:
                    st.write("**Predicted Running Positions**")
                    # Add speed map visualization here
                
                with tabs[2]:
                    st.write("**Track Information**")
                    if "meeting" in race_form:
                        meeting = race_form["meeting"]
                        st.write(f"Track: {meeting.get('trackName', 'N/A')}")
                        st.write(f"Condition: {meeting.get('trackCondition', 'N/A')}")
                        st.write(f"Weather: {meeting.get('weather', 'N/A')}")
                        st.write(f"Rail: {meeting.get('railPosition', 'N/A')}")
        
        except APIError as e:
            st.error(f"Failed to get race form: {str(e)}")

def display_bet_slip():
    """Display bet slip sidebar"""
    st.sidebar.header("Bet Slip")
    
    if not st.session_state.bet_slip:
        st.sidebar.write("No bets in slip")
        return
    
    total_stake = 0
    potential_return = 0
    
    for i, bet in enumerate(st.session_state.bet_slip):
        with st.sidebar.expander(
            f"{bet['venue']} R{bet['race']} - {bet['runner']}"
        ):
            st.write(f"Type: {bet['bet_type']}")
            st.write(f"Odds: {bet['odds']}")
            st.write(f"Stake: ${bet['stake']:.2f}")
            
            if st.button("Remove", key=f"remove_bet_{i}"):
                st.session_state.bet_slip.pop(i)
                st.rerun()
            
            total_stake += bet['stake']
            try:
                odds = float(bet['odds'].replace('$', ''))
                potential_return += bet['stake'] * odds
            except ValueError:
                pass
    
    st.sidebar.markdown("---")
    st.sidebar.write(f"Total Stake: ${total_stake:.2f}")
    st.sidebar.write(f"Potential Return: ${potential_return:.2f}")
    
    if st.sidebar.button("Place Bets", type="primary"):
        st.sidebar.success("Bets placed successfully!")
        st.session_state.bet_slip = []
        st.rerun()

def main():
    st.title("🏇 TAB Racing Dashboard")
    
    # Initialize client
    initialize_client()
    
    # Main navigation
    tab1, tab2 = st.tabs(["Next Races", "Race Form"])
    
    with tab1:
        display_next_races()
    
    with tab2:
        display_race_form()
    
    # Display bet slip
    display_bet_slip()

if __name__ == "__main__":
    main()
