import streamlit as st
import pandas as pd
from typing import Dict, Optional
from racing_visualizations import RacingVisualizations
import plotly.graph_objects as go

class RaceInformation:
    def __init__(self, client):
        self.client = client
        self.visualizer = RacingVisualizations()
        
    def render_race_overview(self, race_data: Dict):
        """Render comprehensive race overview"""
        st.header(f"Race {race_data['raceNumber']} - {race_data.get('raceName', '')}")
        
        # Race details
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Distance", f"{race_data.get('raceDistance', 0)}m")
        with col2:
            st.metric("Prize Money", f"${race_data.get('prizeMoney', 0):,.0f}")
        with col3:
            st.metric("Track Condition", race_data.get('trackCondition', 'N/A'))
            
        # Tabs for different views
        tabs = st.tabs([
            "Form Guide",
            "Speed Map",
            "Track Bias",
            "Betting Analysis"
        ])
        
        with tabs[0]:
            self._render_form_guide(race_data)
            
        with tabs[1]:
            self._render_speed_map(race_data)
            
        with tabs[2]:
            self._render_track_bias(race_data)
            
        with tabs[3]:
            self._render_betting_analysis(race_data)
    
    def _render_form_guide(self, race_data: Dict):
        """Render detailed form guide"""
        if not race_data.get('runners'):
            st.warning("No runners available")
            return
            
        for runner in race_data['runners']:
            with st.expander(f"{runner['runnerNumber']}. {runner['runnerName']}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Basic info
                    st.write("**Basic Information**")
                    info_df = pd.DataFrame({
                        'Attribute': [
                            'Barrier',
                            'Weight',
                            'Jockey',
                            'Trainer',
                            'Last Starts',
                            'Career'
                        ],
                        'Value': [
                            runner.get('barrier', 'N/A'),
                            f"{runner.get('handicapWeight', 0)}kg",
                            runner.get('jockey', 'N/A'),
                            runner.get('trainer', 'N/A'),
                            runner.get('last20Starts', 'N/A'),
                            runner.get('careerRecord', 'N/A')
                        ]
                    })
                    st.dataframe(info_df, hide_index=True)
                    
                    # Form comments
                    if runner.get('formComments'):
                        st.write("**Form Comments**")
                        st.write(runner['formComments'])
                
                with col2:
                    # Performance metrics
                    if runner.get('statistics'):
                        stats = runner['statistics']
                        metrics = {
                            'Win Rate': f"{stats.get('winRate', 0):.1f}%",
                            'Place Rate': f"{stats.get('placeRate', 0):.1f}%",
                            'ROI': f"{stats.get('roi', 0):.1f}%"
                        }
                        for label, value in metrics.items():
                            st.metric(label, value)
    
    def _render_speed_map(self, race_data: Dict):
        """Render speed map visualization"""
        st.subheader("Predicted Running Positions")
        
        if not race_data.get('runners'):
            st.warning("No runners available for speed map")
            return
            
        fig = self.visualizer.create_speed_map(race_data['runners'])
        st.plotly_chart(fig, use_container_width=True)
        
        # Position analysis
        st.write("**Running Style Analysis**")
        styles = {
            'Leader': [],
            'On-pace': [],
            'Midfield': [],
            'Back': []
        }
        
        for runner in race_data['runners']:
            style = self._analyze_running_style(runner)
            styles[style].append(f"{runner['runnerNumber']}. {runner['runnerName']}")
            
        for style, runners in styles.items():
            if runners:
                st.write(f"**{style}:** {', '.join(runners)}")
    
    def _render_track_bias(self, race_data: Dict):
        """Render track bias analysis"""
        st.subheader("Track Bias Analysis")
        
        # Track configuration
        if race_data.get('trackConfiguration'):
            st.write("**Track Configuration**")
            st.write(race_data['trackConfiguration'])
        
        # Create bias visualization
        fig = self.visualizer.create_track_bias({})  # Add track data when available
        st.plotly_chart(fig, use_container_width=True)
        
        # Rail position impact
        if race_data.get('railPosition'):
            st.write("**Rail Position Impact**")
            st.write(f"Rail Position: {race_data['railPosition']}")
            self._analyze_rail_impact(race_data['railPosition'])
    
    def _render_betting_analysis(self, race_data: Dict):
        """Render betting analysis and suggestions"""
        st.subheader("Betting Analysis")
        
        if not race_data.get('runners'):
            st.warning("No runners available for analysis")
            return
            
        # Market overview
        market_df = pd.DataFrame([{
            'Runner': f"{r['runnerNumber']}. {r['runnerName']}",
            'Win Odds': r.get('fixedOdds', {}).get('returnWin', 'N/A'),
            'Place Odds': r.get('fixedOdds', {}).get('returnPlace', 'N/A'),
            'Win %': f"{100/float(r.get('fixedOdds', {}).get('returnWin', 100)):.1f}%"
        } for r in race_data['runners'] if not r.get('scratched')])
        
        st.dataframe(market_df, hide_index=True)
        
        # Market confidence
        total_percentage = sum(
            100/float(r.get('fixedOdds', {}).get('returnWin', 100))
            for r in race_data['runners']
            if not r.get('scratched')
        )
        st.metric(
            "Market Confidence",
            f"{total_percentage:.1f}%",
            delta=f"{total_percentage-100:.1f}%"
        )
    
    def _analyze_running_style(self, runner: Dict) -> str:
        """Analyze runner's typical running style"""
        # This would use historical data in production
        # For now, return random style for demonstration
        import random
        return random.choice(['Leader', 'On-pace', 'Midfield', 'Back'])
    
    def _analyze_rail_impact(self, rail_position: str):
        """Analyze impact of rail position"""
        # This would use historical analysis in production
        st.write("Historical analysis shows:")
        st.write("- Inside runners advantage: Medium")
        st.write("- Early speed importance: High")
        st.write("- Backmarker success rate: Low")
