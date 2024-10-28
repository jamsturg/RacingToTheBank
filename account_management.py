import streamlit as st
import logging
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List

class AccountManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.initialize_session_state()

    def initialize_session_state(self):
        """Initialize account-related session state variables"""
        if 'account_balance' not in st.session_state:
            st.session_state.account_balance = 1000.00
        if 'pending_bets' not in st.session_state:
            st.session_state.pending_bets = []
        if 'betting_history' not in st.session_state:
            st.session_state.betting_history = []
        if 'daily_pl' not in st.session_state:
            st.session_state.daily_pl = 0.0

    def login(self, username: str, password: str) -> bool:
        """Authenticate user"""
        try:
            # For demo purposes, accept demo/demo
            return username == "demo" and password == "demo"
        except Exception as e:
            self.logger.error(f"Login error: {str(e)}")
            return False

    def get_balance(self) -> float:
        """Get current account balance"""
        return st.session_state.account_balance

    def get_daily_pl(self) -> float:
        """Get daily profit/loss"""
        return st.session_state.daily_pl

    def get_pending_bets(self) -> List[Dict]:
        """Get list of pending bets"""
        return st.session_state.pending_bets

    def get_betting_history(self) -> List[Dict]:
        """Get betting history"""
        return st.session_state.betting_history

    def place_bet(self, bet_details: Dict) -> bool:
        """Place a new bet"""
        try:
            if bet_details['stake'] <= st.session_state.account_balance:
                # Deduct stake from balance
                st.session_state.account_balance -= bet_details['stake']
                
                # Add to pending bets
                bet_details['timestamp'] = datetime.now()
                bet_details['status'] = 'Pending'
                st.session_state.pending_bets.append(bet_details)
                
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error placing bet: {str(e)}")
            return False

    def settle_bet(self, bet_id: str, result: str, return_amount: float = 0.0):
        """Settle a pending bet"""
        try:
            for bet in st.session_state.pending_bets:
                if bet.get('id') == bet_id:
                    bet['status'] = result
                    bet['settled_time'] = datetime.now()
                    
                    if result == 'Won':
                        st.session_state.account_balance += return_amount
                        st.session_state.daily_pl += (return_amount - bet['stake'])
                    else:
                        st.session_state.daily_pl -= bet['stake']
                    
                    # Move to history
                    st.session_state.betting_history.append(bet)
                    st.session_state.pending_bets.remove(bet)
                    break
        except Exception as e:
            self.logger.error(f"Error settling bet: {str(e)}")

    def get_win_rate(self) -> float:
        """Calculate win rate"""
        try:
            total_bets = len(st.session_state.betting_history)
            if total_bets == 0:
                return 0.0
            
            wins = sum(1 for bet in st.session_state.betting_history 
                      if bet['status'] == 'Won')
            return (wins / total_bets) * 100
        except Exception as e:
            self.logger.error(f"Error calculating win rate: {str(e)}")
            return 0.0

    def get_roi(self) -> float:
        """Calculate ROI"""
        try:
            total_stakes = sum(bet['stake'] for bet in st.session_state.betting_history)
            if total_stakes == 0:
                return 0.0
            
            total_returns = sum(
                bet.get('return_amount', 0) 
                for bet in st.session_state.betting_history 
                if bet['status'] == 'Won'
            )
            
            return ((total_returns - total_stakes) / total_stakes) * 100
        except Exception as e:
            self.logger.error(f"Error calculating ROI: {str(e)}")
            return 0.0

    def get_daily_turnover(self) -> float:
        """Get daily betting turnover"""
        try:
            today = datetime.now().date()
            daily_bets = [
                bet for bet in st.session_state.betting_history
                if bet['timestamp'].date() == today
            ]
            return sum(bet['stake'] for bet in daily_bets)
        except Exception as e:
            self.logger.error(f"Error calculating daily turnover: {str(e)}")
            return 0.0

    def get_performance_metrics(self) -> Dict:
        """Get comprehensive performance metrics"""
        try:
            metrics = {
                'balance': self.get_balance(),
                'daily_pl': self.get_daily_pl(),
                'win_rate': self.get_win_rate(),
                'roi': self.get_roi(),
                'daily_turnover': self.get_daily_turnover(),
                'active_bets': len(self.get_pending_bets()),
                'total_bets': len(self.get_betting_history())
            }
            return metrics
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {str(e)}")
            return {}

    def logout(self):
        """Log out current user and clear session state"""
        try:
            session_vars = [
                'logged_in', 'account_balance', 'pending_bets',
                'betting_history', 'daily_pl'
            ]
            
            for var in session_vars:
                if var in st.session_state:
                    del st.session_state[var]
                    
            st.session_state.logged_in = False
        except Exception as e:
            self.logger.error(f"Logout error: {str(e)}")

    def get_performance_chart_data(self) -> pd.DataFrame:
        """Get data for performance charts"""
        try:
            # Get last 30 days of data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # Create date range
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Calculate daily P/L
            daily_pl = []
            for date in dates:
                day_bets = [
                    bet for bet in st.session_state.betting_history
                    if bet['timestamp'].date() == date.date()
                ]
                
                pl = sum(
                    bet.get('return_amount', 0) - bet['stake']
                    for bet in day_bets
                )
                daily_pl.append(pl)
            
            return pd.DataFrame({
                'Date': dates,
                'P/L': daily_pl
            })
        except Exception as e:
            self.logger.error(f"Error getting performance chart data: {str(e)}")
            return pd.DataFrame()
