from dataclasses import dataclass
from typing import List, Dict, Optional
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

@dataclass
class RaceAnalysis:
    speed_map: Dict
    class_analysis: Dict
    track_bias: Dict
    pace_prediction: Dict
    betting_trends: Dict

class RaceInformation:
    def __init__(self, client):
        self.client = client
        self.historical_analysis = HistoricalAnalysis(client)

    def render_race_overview(self, race: Dict):
        """Render comprehensive race overview"""
        st.header(f"Race {race['raceNumber']} - {race['meeting']['venueName']}")
        
        # Race details
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Distance", f"{race['raceDistance']}m")
        with col2:
            st.metric("Prize Money", race.get('prizeMoney', 'N/A'))
        with col3:
            st.metric("Class", race.get('raceClass', 'N/A'))
        
        # Track conditions
        st.subheader("Track Information")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Condition", race['meeting'].get('trackCondition', 'N/A'))
        with col2:
            st.metric("Weather", race['meeting'].get('weather', 'N/A'))
        with col3:
            st.metric("Rail Position", race['meeting'].get('railPosition', 'N/A'))
        with col4:
            st.metric("Track Direction", race['meeting'].get('trackDirection', 'N/A'))
        
        # Race analysis
        analysis = self._analyze_race(race)
        self._render_race_analysis(analysis)
        
        # Runners
        self._render_runners(race['runners'])

    def _analyze_race(self, race: Dict) -> RaceAnalysis:
        """Perform comprehensive race analysis"""
        return RaceAnalysis(
            speed_map=self._generate_speed_map(race['runners']),
            class_analysis=self._analyze_class_levels(race),
            track_bias=self.historical_analysis.analyze_track_bias(
                race['meeting']['venueMnemonic'],
                race['meeting'].get('trackCondition')
            ),
            pace_prediction=self.historical_analysis.predict_race_pattern(race['runners']),
            betting_trends=self._analyze_betting_trends(race)
        )

    def _render_race_analysis(self, analysis: RaceAnalysis):
        """Render race analysis visualization"""
        tabs = st.tabs([
            "Speed Map",
            "Class Analysis",
            "Track Bias",
            "Pace Prediction",
            "Betting Trends"
        ])
        
        with tabs[0]:
            self._render_speed_map(analysis.speed_map)
        
        with tabs[1]:
            self._render_class_analysis(analysis.class_analysis)
            
        with tabs[2]:
            self._render_track_bias(analysis.track_bias)
            
        with tabs[3]:
            self._render_pace_prediction(analysis.pace_prediction)
            
        with tabs[4]:
            self._render_betting_trends(analysis.betting_trends)

    def _render_runners(self, runners: List[Dict]):
        """Render detailed runner information"""
        st.subheader("Runners")
        
        for runner in runners:
            with st.expander(f"{runner['runnerNumber']}. {runner['runnerName']}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Basic info
                    st.write("**Basic Information**")
                    info_cols = st.columns(3)
                    with info_cols[0]:
                        st.write(f"Barrier: {runner.get('barrier', 'N/A')}")
                        st.write(f"Weight: {runner.get('weight', 'N/A')}")
                    with info_cols[1]:
                        st.write(f"Jockey: {runner.get('jockey', 'N/A')}")
                        st.write(f"Trainer: {runner.get('trainer', 'N/A')}")
                    with info_cols[2]:
                        st.write(f"Age: {runner.get('age', 'N/A')}")
                        st.write(f"Sex: {runner.get('sex', 'N/A')}")
                    
                    # Form
                    st.write("**Recent Form**")
                    if runner.get('last20Starts'):
                        self._render_form_analysis(runner)
                    else:
                        st.write("No recent form available")
                
                with col2:
                    # Odds and betting
                    st.write("**Betting Information**")
                    if runner.get('fixedOdds'):
                        odds = runner['fixedOdds'].get('returnWin')
                        st.metric("Fixed Odds", f"${odds:.2f}")
                        
                        # Odds movement chart
                        self._render_odds_movement(runner)
                    
                    # Quick bet button
                    stake = st.number_input(
                        "Stake ($)",
                        min_value=1.0,
                        value=10.0,
                        key=f"stake_{runner['runnerNumber']}"
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Win", key=f"win_{runner['runnerNumber']}"):
                            self._place_bet(runner, "Win", stake)
                    with col2:
                        if st.button("Place", key=f"place_{runner['runnerNumber']}"):
                            self._place_bet(runner, "Place", stake)

    def _render_form_analysis(self, runner: Dict):
        """Render detailed form analysis"""
        # Create form dataframe
        form_data = []
        for start in runner.get('formComments', []):
            form_data.append({
                'Date': start.get('date'),
                'Track': start.get('track'),
                'Distance': start.get('distance'),
                'Position': start.get('position'),
                'Margin': start.get('margin'),
                'Weight': start.get('weight'),
                'Jockey': start.get('jockey'),
                'Comment': start.get('comment')
            })
        
        if form_data:
            df = pd.DataFrame(form_data)
            st.dataframe(df)
            
            # Performance trends
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['Position'],
                mode='lines+markers',
                name='Position'
            ))
            fig.update_layout(
                title='Position History',
                yaxis_title='Position',
                yaxis_autorange='reversed'
            )
            st.plotly_chart(fig)

    def _render_odds_movement(self, runner: Dict):
        """Render odds movement chart"""
        # In real implementation, fetch historical odds
        # For demo, generate sample data
        times = pd.date_range(
            start=datetime.now() - timedelta(hours=24),
            end=datetime.now(),
            freq='H'
        )
        odds = [runner['fixedOdds']['returnWin'] + np.random.uniform(-1, 1) 
               for _ in range(len(times))]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=times,
            y=odds,
            mode='lines',
            name='Fixed Odds'
        ))
        fig.update_layout(
            title='Odds Movement (24h)',
            yaxis_title='Odds ($)'
        )
        st.plotly_chart(fig)

    def _place_bet(self, runner: Dict, bet_type: str, stake: float):
        """Handle bet placement"""
        if 'account' in st.session_state and st.session_state.account:
            if stake <= st.session_state.account.balance:
                # Add bet to slip
                bet = {
                    'runner_number': runner['runnerNumber'],
                    'runner_name': runner['runnerName'],
                    'bet_type': bet_type,
                    'stake': stake,
                    'odds': runner['fixedOdds']['returnWin'],
                    'potential_return': stake * runner['fixedOdds']['returnWin']
                }
                st.session_state.bet_slip.append(bet)
                st.success(f"Added {bet_type} bet on {runner['runnerName']} to bet slip")
            else:
                st.error("Insufficient balance")
        else:
            st.warning("Please log in to place bets")