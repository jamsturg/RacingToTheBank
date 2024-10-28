import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List
import asyncio
import logging
from pathlib import Path
import json

from tab_api_client import TABApiClient
from account_management import AccountManager
from automated_betting import AutomatedBetting
from race_information import RaceInformation
from historical_analysis import HistoricalAnalysis
from visualizations import RacingVisualizations
from form_analysis import FormAnalysis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RacingDashboard:
    def __init__(self):
        # Configure page
        st.set_page_config(
            page_title="TAB Racing Dashboard",
            page_icon="🏇",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Initialize components
        self.initialize_session_state()
        self.initialize_clients()
        self.setup_websocket()

    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'initialized' not in st.session_state:
            st.session_state.initialized = True
            st.session_state.page = "Dashboard"
            st.session_state.active_race = None
            st.session_state.bet_slip = []
            st.session_state.alerts = []
            st.session_state.dark_mode = False
            st.session_state.auto_refresh = True
            st.session_state.refresh_interval = 30
            st.session_state.last_update = datetime.now()

    def initialize_clients(self):
        """Initialize API clients and components"""
        try:
            # Load credentials from secrets
            self.bearer_token = st.secrets["TAB_BEARER_TOKEN"]
            
            # Initialize clients
            self.tab_client = TABApiClient(self.bearer_token)
            self.account_manager = AccountManager()
            self.betting_system = AutomatedBetting()
            self.race_info = RaceInformation(self.tab_client)
            self.historical_analysis = HistoricalAnalysis(self.tab_client)
            self.visualizer = RacingVisualizations()
            self.form_analyzer = FormAnalysis()
            
            # Setup automated betting strategies
            self.betting_system.implement_betting_strategies()
            
        except Exception as e:
            st.error(f"Failed to initialize clients: {str(e)}")
            st.stop()

    def setup_websocket(self):
        """Setup WebSocket connection for real-time updates"""
        if 'ws_manager' not in st.session_state:
            from websocket_manager import WebSocketManager
            st.session_state.ws_manager = WebSocketManager()

    def render_navigation(self):
        """Render navigation sidebar"""
        with st.sidebar:
            st.title("🏇 TAB Racing")
            
            # Main navigation
            st.session_state.page = st.radio(
                "Navigation",
                ["Dashboard", "Race Form", "Betting", "Analysis", "Portfolio", "Settings"]
            )
            
            # Account summary
            if self.account_manager.is_logged_in():
                self.render_account_summary()
            else:
                self.render_login_form()

    def render_account_summary(self):
        """Render account summary in sidebar"""
        st.sidebar.markdown("---")
        st.sidebar.subheader("Account Summary")
        
        account = self.account_manager.get_account()
        
        # Balance
        st.sidebar.metric(
            "Balance",
            f"${account.balance:,.2f}",
            f"{account.daily_pl:+,.2f}"
        )
        
        # Quick stats
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("Active Bets", len(account.pending_bets))
        with col2:
            st.metric("Win Rate", f"{account.win_rate:.1f}%")
        
        st.sidebar.markdown("---")

    def render_main_dashboard(self):
        """Render main dashboard page"""
        st.title("Racing Dashboard")
        
        # Top row metrics
        self.render_key_metrics()
        
        # Main content
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Next races
            st.subheader("Next Races")
            self.render_next_races()
            
        with col2:
            # Featured races and highlights
            st.subheader("Featured Races")
            self.render_featured_races()
            
        # Bottom section
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            # Quick form
            st.subheader("Quick Form")
            self.render_quick_form()
            
        with col2:
            # Market movers
            st.subheader("Market Movers")
            self.render_market_movers()
            
        with col3:
            # Betting opportunities
            st.subheader("Betting Opportunities")
            self.render_betting_opportunities()

    def render_key_metrics(self):
        """Render key performance metrics"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Today's Turnover",
                f"${self.account_manager.get_daily_turnover():,.2f}",
                f"{self.account_manager.get_daily_turnover_change():+.1f}%"
            )
        
        with col2:
            st.metric(
                "Active Bets",
                len(self.account_manager.get_pending_bets()),
                f"{self.account_manager.get_pending_bets_change():+d}"
            )
        
        with col3:
            st.metric(
                "Win Strike Rate",
                f"{self.account_manager.get_win_rate():.1f}%",
                f"{self.account_manager.get_win_rate_change():+.1f}%"
            )
        
        with col4:
            st.metric(
                "ROI",
                f"{self.account_manager.get_roi():.1f}%",
                f"{self.account_manager.get_roi_change():+.1f}%"
            )

    def render_next_races(self):
        """Render next races section"""
        try:
            races = self.tab_client.get_next_to_go_races(
                jurisdiction="NSW",
                max_races=5,
                include_fixed_odds=True
            )
            
            for race in races.get('races', []):
                with st.expander(
                    f"{race['meeting']['venueName']} R{race['raceNumber']} - "
                    f"{race['raceDistance']}m ({race['raceStartTime']})",
                    expanded=True
                ):
                    self.render_race_card(race)
                    
        except Exception as e:
            st.error(f"Failed to load next races: {str(e)}")

    def render_race_card(self, race: Dict):
        """Render individual race card"""
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Runner table
            runners_df = pd.DataFrame([
                {
                    'No.': r['runnerNumber'],
                    'Runner': r['runnerName'],
                    'Barrier': r.get('barrier', ''),
                    'Weight': r.get('weight', ''),
                    'Jockey': r.get('jockey', ''),
                    'Odds': r['fixedOdds']['returnWin']
                }
                for r in race['runners']
            ])
            
            st.dataframe(
                runners_df.style.background_gradient(
                    subset=['Odds'],
                    cmap='RdYlGn_r'
                ),
                use_container_width=True
            )
        
        with col2:
            # Quick betting interface
            selected_runner = st.selectbox(
                "Select Runner",
                options=[f"{r['runnerNumber']}. {r['runnerName']}"
                        for r in race['runners']],
                key=f"runner_{race['raceNumber']}"
            )
            
            bet_type = st.selectbox(
                "Bet Type",
                options=["Win", "Place", "Each Way"],
                key=f"bet_type_{race['raceNumber']}"
            )
            
            stake = st.number_input(
                "Stake ($)",
                min_value=1.0,
                max_value=1000.0,
                value=10.0,
                key=f"stake_{race['raceNumber']}"
            )
            
            if st.button("Add to Slip", key=f"add_{race['raceNumber']}"):
                self.add_to_bet_slip(race, selected_runner, bet_type, stake)

    def render_featured_races(self):
        """Render featured races section"""
        try:
            featured = self.tab_client.get_featured_races()
            
            for race in featured:
                with st.expander(race['raceName']):
                    st.write(f"Prize Money: ${race['prizeMoney']:,}")
                    st.write(f"Distance: {race['raceDistance']}m")
                    
                    if st.button("View Analysis", key=f"analyze_{race['raceId']}"):
                        st.session_state.active_race = race['raceId']
                        st.session_state.page = "Race Form"
                        st.experimental_rerun()
                        
        except Exception as e:
            st.error(f"Failed to load featured races: {str(e)}")

    def render_quick_form(self):
        """Render quick form analysis section"""
        runner_search = st.text_input("Search Runner")
        
        if runner_search:
            try:
                runner_data = self.tab_client.search_runner(runner_search)
                if runner_data:
                    self.form_analyzer.render_quick_form_card(runner_data)
                else:
                    st.warning("No runner found")
            except Exception as e:
                st.error(f"Failed to load runner data: {str(e)}")

    def render_market_movers(self):
        """Render market movers section"""
        try:
            movers = self.tab_client.get_market_movers()
            
            # Create market movers visualization
            fig = go.Figure()
            
            for mover in movers:
                fig.add_trace(go.Scatter(
                    x=mover['times'],
                    y=mover['odds'],
                    name=mover['runnerName'],
                    mode='lines+markers'
                ))
                
            fig.update_layout(
                title="Market Moves - Last Hour",
                xaxis_title="Time",
                yaxis_title="Odds ($)",
                height=300
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Failed to load market movers: {str(e)}")

    def render_betting_opportunities(self):
        """Render betting opportunities section"""
        opportunities = self.betting_system.get_opportunities()
        
        if opportunities:
            for opp in opportunities:
                with st.expander(
                    f"{opp['runner_name']} ({opp['race_name']})"
                ):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"Strategy: {opp['strategy']}")
                        st.write(f"Confidence: {opp['confidence']:.1f}%")
                        
                    with col2:
                        st.write(f"Odds: ${opp['odds']:.2f}")
                        st.write(f"Expected Value: {opp['ev']:.1f}%")
                        
                    if st.button("Add to Slip", key=f"opp_{opp['id']}"):
                        self.add_to_bet_slip(
                            opp['race'],
                            opp['runner_name'],
                            opp['bet_type'],
                            opp['recommended_stake']
                        )
        else:
            st.write("No current opportunities")

    def render_bet_slip(self):
        """Render bet slip sidebar"""
        st.sidebar.markdown("---")
        st.sidebar.subheader("Bet Slip")
        
        if not st.session_state.bet_slip:
            st.sidebar.write("No bets in slip")
            return
            
        total_stake = 0
        total_potential_return = 0
        
        for bet in st.session_state.bet_slip:
            with st.sidebar.expander(
                f"{bet['runner']} ({bet['bet_type']})"
            ):
                st.write(f"Odds: ${bet['odds']:.2f}")
                
                # Allow stake adjustment
                new_stake = st.number_input(
                    "Stake ($)",
                    min_value=1.0,
                    value=float(bet['stake']),
                    key=f"adjust_{bet['id']}"
                )
                bet['stake'] = new_stake
                
                potential_return = bet['stake'] * bet['odds']
                st.write(f"Potential Return: ${potential_return:.2f}")
                
                if st.button("Remove", key=f"remove_{bet['id']}"):
                    st.session_state.bet_slip.remove(bet)
                    st.experimental_rerun()
                    
                total_stake += bet['stake']
                total_potential_return += potential_return
        
        st.sidebar.markdown("---")
        st.sidebar.write(f"Total Stake: ${total_stake:.2f}")
        st.sidebar.write(f"Potential Return: ${total_potential_return:.2f}")
        
        if st.sidebar.button("Place Bets"):
            self.place_bets()

    def add_to_bet_slip(
        self,
        race: Dict,
        runner: str,
        bet_type: str,
        stake: float
    ):
        """Add bet to slip"""
        bet = {
            'id': len(st.session_state.bet_slip),
            'race_id': race['raceId'],
            'race_name': f"{race['meeting']['venueName']} R{race['raceNumber']}",
            'runner': runner,
            'bet_type': bet_type,
            'odds': float(race['runners'][0]['fixedOdds']['returnWin']),
            'stake': stake
        }
        
        st.session_state.bet_slip.append(bet)
        st.success(f"Added {runner} to bet slip")

    def place_bets(self):
        """Place all bets in slip"""
        try:
            for bet in st.session_state.bet_slip:
                self.account_manager.place_bet(bet)
                
            st.success("Bets placed successfully!")
            st.session_state.bet_slip = []
            st.experimental_rerun()
            
        except Exception as e:
            st.error(f"Failed to place bets: {str(e)}")

    def run(self):
        """Run the dashboard application"""
        # Render navigation
        self.render_navigation()
        
        # Render main content based on selected page
        if st.session_state.page == "Dashboard":
            self.render_main_dashboard()
        elif st.session_state.page == "Race Form":
            self.render_race_form()
        elif st.session_state.page == "Betting":
            self.render_betting_dashboard()
        elif st.session_state.page == "Analysis":
            self.render_analysis_dashboard()
        elif st.session_state.page == "Portfolio":
            self.render_portfolio_dashboard()
        elif st.session_state.page == "Settings":
            self.render_settings()
        
        # Render bet slip
        self.render_bet_slip()

    def render_race_form(self):
        """Render race form page"""
        st.title("Race Form")
        
        # Race selection
        col1, col2 = st.columns(2)
        with col1:
            track = st.selectbox("Track", ["Randwick", "Flemington", "Eagle Farm"])
        with col2:
            race = st.selectbox("Race", [f"Race {i}" for i in range(1, 11)])
            
        # Form analysis tabs
        tab1, tab2, tab3 = st.tabs(["Speed Map", "Form Guide", "Statistics"])
        
        with tab1:
            st.subheader("Speed Map")
            self.visualizer.render_speed_map({})
            
        with tab2:
            st.subheader("Form Guide")
            self.form_analyzer.render_form_dashboard({})
            
        with tab3:
            st.subheader("Race Statistics")
            self.historical_analysis.render_race_stats({})

    def render_betting_dashboard(self):
        """Render betting dashboard"""
        st.title("Betting Dashboard")
        
        # Betting form
        with st.form("betting_form"):
            col1, col2 = st.columns(2)
            with col1:
                track = st.selectbox("Track", ["Randwick", "Flemington", "Eagle Farm"])
                race = st.selectbox("Race", [f"Race {i}" for i in range(1, 11)])
            with col2:
                bet_type = st.selectbox("Bet Type", ["Win", "Place", "Each Way"])
                amount = st.number_input("Amount ($)", min_value=1.0, step=10.0)
            
            if st.form_submit_button("Place Bet"):
                self.betting_system.place_bet({
                    'track': track,
                    'race': race,
                    'type': bet_type,
                    'amount': amount
                })
        
        # Active bets
        st.subheader("Active Bets")
        active_bets = self.account_manager.get_pending_bets()
        if active_bets:
            bets_df = pd.DataFrame(active_bets)
            st.dataframe(bets_df, use_container_width=True)
        else:
            st.info("No active bets")

    def render_analysis_dashboard(self):
        """Render analysis dashboard"""
        st.title("Analysis Dashboard")
        
        # Analysis tabs
        tab1, tab2, tab3 = st.tabs(["Track Bias", "Form Analysis", "Market Analysis"])
        
        with tab1:
            st.subheader("Track Bias Analysis")
            self.historical_analysis.render_track_bias({})
            
        with tab2:
            st.subheader("Form Analysis")
            self.form_analyzer.render_form_analysis({})
            
        with tab3:
            st.subheader("Market Analysis")
            self.historical_analysis.render_market_analysis({})

    def render_portfolio_dashboard(self):
        """Render portfolio dashboard"""
        st.title("Portfolio Dashboard")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        metrics = self.account_manager.get_performance_metrics()
        
        with col1:
            st.metric("Balance", f"${metrics['balance']:,.2f}")
        with col2:
            st.metric("Daily P/L", f"${metrics['daily_pl']:,.2f}")
        with col3:
            st.metric("Win Rate", f"{metrics['win_rate']:.1f}%")
        with col4:
            st.metric("ROI", f"{metrics['roi']:.1f}%")
        
        # Performance chart
        st.subheader("Performance Chart")
        performance_data = self.account_manager.get_performance_chart_data()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=performance_data['Date'],
            y=performance_data['P/L'],
            mode='lines',
            name='Daily P/L',
            line=dict(color='#1E3D59', width=2)
        ))
        
        fig.update_layout(
            title="Daily P/L Performance",
            xaxis_title="Date",
            yaxis_title="Profit/Loss ($)",
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Betting history
        st.subheader("Betting History")
        history = self.account_manager.get_betting_history()
        if history:
            history_df = pd.DataFrame(history)
            st.dataframe(history_df, use_container_width=True)
        else:
            st.info("No betting history")

    def render_settings(self):
        """Render settings page"""
        st.title("Settings")
        
        # Account settings
        st.subheader("Account Settings")
        with st.form("account_settings"):
            st.text_input("Email", value="user@example.com")
            st.number_input("Default Bet Amount", value=10.0, step=10.0)
            st.checkbox("Enable Email Notifications")
            st.checkbox("Enable SMS Notifications")
            
            if st.form_submit_button("Save Settings"):
                st.success("Settings saved successfully")
        
        # Betting preferences
        st.subheader("Betting Preferences")
        with st.form("betting_preferences"):
            st.number_input("Maximum Bet Size", value=100.0, step=10.0)
            st.number_input("Daily Loss Limit", value=500.0, step=50.0)
            st.multiselect(
                "Preferred Race Types",
                ["Thoroughbred", "Harness", "Greyhound"],
                default=["Thoroughbred"]
            )
            
            if st.form_submit_button("Save Preferences"):
                st.success("Preferences saved successfully")
        
        # Automated betting settings
        st.subheader("Automated Betting")
        with st.form("automated_settings"):
            st.checkbox("Enable Automated Betting")
            st.number_input("Confidence Threshold", value=80, step=5)
            st.number_input("Maximum Stakes per Day", value=5, step=1)
            
            if st.form_submit_button("Save Automation Settings"):
                st.success("Automation settings saved successfully")

if __name__ == "__main__":
    dashboard = RacingDashboard()
    dashboard.run()
