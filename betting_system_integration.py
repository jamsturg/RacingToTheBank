import streamlit as st
from automated_betting_system import AutomatedBettingSystem
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class BettingSystemIntegration:
    def __init__(self):
        # Initialize betting system in session state if not exists
        if 'betting_system' not in st.session_state:
            initial_bank = 1000.0  # Default starting bank
            st.session_state.betting_system = AutomatedBettingSystem(initial_bank)
        
        self.betting_system = st.session_state.betting_system

    def render_betting_interface(self):
        """Render betting system interface"""
        st.header("Automated Betting System")
        
        tabs = st.tabs([
            "Dashboard",
            "Strategy Settings",
            "Risk Management",
            "Automation Rules"
        ])
        
        with tabs[0]:
            self.betting_system.render_dashboard()
            
        with tabs[1]:
            self._render_strategy_settings()
            
        with tabs[2]:
            self._render_risk_management()
            
        with tabs[3]:
            self._render_automation_rules()

    def _render_strategy_settings(self):
        """Render strategy configuration interface"""
        st.subheader("Strategy Settings")
        
        selected_strategy = st.selectbox(
            "Select Strategy",
            options=list(self.betting_system.strategies.keys())
        )
        
        if selected_strategy:
            strategy = self.betting_system.strategies[selected_strategy]
            
            st.write(f"**Description:** {strategy.description}")
            
            col1, col2 = st.columns(2)
            with col1:
                new_min_odds = st.number_input(
                    "Minimum Odds",
                    min_value=1.0,
                    max_value=100.0,
                    value=float(strategy.min_odds)
                )
                new_max_odds = st.number_input(
                    "Maximum Odds",
                    min_value=1.0,
                    max_value=100.0,
                    value=float(strategy.max_odds)
                )
                new_stake = st.number_input(
                    "Stake Percentage",
                    min_value=0.01,
                    max_value=1.0,
                    value=float(strategy.stake_percentage)
                )
            
            with col2:
                new_min_prob = st.number_input(
                    "Minimum Probability",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(strategy.min_probability)
                )
                new_max_exposure = st.number_input(
                    "Maximum Exposure",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(strategy.max_exposure)
                )
                new_edge = st.number_input(
                    "Required Edge",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(strategy.required_edge)
                )
            
            if st.button("Update Strategy"):
                strategy.min_odds = new_min_odds
                strategy.max_odds = new_max_odds
                strategy.stake_percentage = new_stake
                strategy.min_probability = new_min_prob
                strategy.max_exposure = new_max_exposure
                strategy.required_edge = new_edge
                st.success("Strategy updated successfully!")

    def _render_risk_management(self):
        """Render risk management settings"""
        st.subheader("Risk Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_max_bet = st.number_input(
                "Maximum Bet Size (% of bank)",
                min_value=0.01,
                max_value=1.0,
                value=float(self.betting_system.risk_limits['max_bet_size'])
            )
            new_max_daily_loss = st.number_input(
                "Maximum Daily Loss (% of bank)",
                min_value=0.01,
                max_value=1.0,
                value=float(self.betting_system.risk_limits['max_daily_loss'])
            )
        
        with col2:
            new_max_exposure = st.number_input(
                "Maximum Exposure (% of bank)",
                min_value=0.01,
                max_value=1.0,
                value=float(self.betting_system.risk_limits['max_exposure'])
            )
            new_min_bank = st.number_input(
                "Minimum Bank Level (% of initial bank)",
                min_value=0.01,
                max_value=1.0,
                value=float(self.betting_system.risk_limits['min_bank'])
            )
        
        if st.button("Update Risk Limits"):
            self.betting_system.risk_limits.update({
                'max_bet_size': new_max_bet,
                'max_daily_loss': new_max_daily_loss,
                'max_exposure': new_max_exposure,
                'min_bank': new_min_bank
            })
            st.success("Risk limits updated successfully!")

    def _render_automation_rules(self):
        """Render automation rules configuration"""
        st.subheader("Automation Rules")
        
        st.write("""
        Configure automated betting rules and conditions. The system will automatically
        place bets when these conditions are met, subject to risk management rules.
        """)
        
        enable_automation = st.toggle(
            "Enable Automated Betting",
            value=getattr(self.betting_system, 'automation_enabled', False)
        )
        
        if enable_automation:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Betting Triggers**")
                min_value = st.number_input(
                    "Minimum Value Edge",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.05
                )
                min_kelly = st.number_input(
                    "Minimum Kelly Fraction",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.1
                )
            
            with col2:
                st.write("**Betting Constraints**")
                max_concurrent = st.number_input(
                    "Maximum Concurrent Bets",
                    min_value=1,
                    max_value=50,
                    value=10
                )
                bet_frequency = st.selectbox(
                    "Betting Frequency",
                    options=["High", "Medium", "Low"]
                )
        
            st.write("**Advanced Settings**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.checkbox("Apply Track Bias Adjustment", value=True)
            with col2:
                st.checkbox("Consider Weather Impact", value=True)
            with col3:
                st.checkbox("Use Historical Patterns", value=True)
                
            if st.button("Save Automation Rules"):
                self.betting_system.automation_enabled = enable_automation
                self.betting_system.automation_config = {
                    'min_value': min_value,
                    'min_kelly': min_kelly,
                    'max_concurrent': max_concurrent,
                    'bet_frequency': bet_frequency
                }
                st.success("Automation rules updated successfully!")
        else:
            st.info("Automated betting is currently disabled")

    def process_race(self, race_data: Dict):
        """Process race for betting opportunities"""
        if not getattr(self.betting_system, 'automation_enabled', False):
            return
            
        try:
            for runner in race_data.get('runners', []):
                # Evaluate betting opportunity
                for strategy_name in self.betting_system.strategies:
                    should_bet, stake, reason = self.betting_system.evaluate_bet_opportunity(
                        runner,
                        strategy_name
                    )
                    
                    if should_bet:
                        # Place bet
                        success = self.betting_system.place_bet(
                            runner,
                            strategy_name,
                            stake
                        )
                        
                        if success:
                            logger.info(
                                f"Placed automated bet: {runner['runner_name']} - ${stake:.2f}"
                            )
                        else:
                            logger.warning(
                                f"Failed to place bet on {runner['runner_name']}"
                            )
                            
        except Exception as e:
            logger.error(f"Error processing race for betting: {str(e)}")

    def update_race_results(self, race_results: Dict):
        """Update betting system with race results"""
        try:
            self.betting_system.update_bet_status(race_results)
        except Exception as e:
            logger.error(f"Error updating race results: {str(e)}")
