import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal
import pandas as pd
import plotly.graph_objects as go
import logging
from tab_api_client import TABApiClient, APIError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AccountManager:
    def __init__(self):
        if 'account' not in st.session_state:
            st.session_state.account = None
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False
        if 'bearer_token' not in st.session_state:
            st.session_state.bearer_token = None

    def _validate_login(self, username: str, password: str) -> bool:
        """Validate login credentials using TAB API"""
        try:
            # Initialize API client
            bearer_token = st.secrets.get("TAB_BEARER_TOKEN")
            if not bearer_token:
                logger.error("Missing TAB bearer token")
                return False

            # Create API client with bearer token
            client = TABApiClient(bearer_token)
            
            # Verify authentication by making a test API call
            try:
                # Try to get account balance to verify credentials
                account_info = client.get_account_balance()
                if isinstance(account_info, dict) and not account_info.get('error'):
                    # Store bearer token in session state
                    st.session_state.bearer_token = bearer_token
                    return True
                else:
                    logger.error("Failed to validate account access")
                    return False
            except APIError as e:
                logger.error(f"API validation error: {str(e)}")
                return False

        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False

    def _load_account(self, username: str) -> Dict:
        """Load account details from TAB API"""
        if not st.session_state.bearer_token:
            raise ValueError("No bearer token available")
            
        try:
            client = TABApiClient(st.session_state.bearer_token)
            
            # Get account info with proper error handling
            try:
                account_info = client.get_account_balance()
                if account_info.get('error'):
                    raise APIError(f"Failed to get account balance: {account_info['error']}")

                pending_bets = client.get_pending_bets()
                if pending_bets.get('error'):
                    raise APIError(f"Failed to get pending bets: {pending_bets['error']}")

                bet_history = client.get_bet_history()
                if bet_history.get('error'):
                    raise APIError(f"Failed to get bet history: {bet_history['error']}")

                return {
                    'user_id': account_info.get('accountId', ''),
                    'username': username,
                    'balance': Decimal(str(account_info.get('balance', 0))),
                    'pending_bets': pending_bets.get('bets', []),
                    'bet_history': bet_history.get('bets', []),
                    'preferences': account_info.get('preferences', {})
                }
            except APIError as e:
                logger.error(f"API error while loading account: {str(e)}")
                raise
            
        except Exception as e:
            logger.error(f"Unexpected error loading account: {str(e)}")
            raise

    def render_login(self):
        """Render login interface with improved error handling"""
        if not st.session_state.logged_in:
            st.sidebar.title("Login")
            
            # Check if bearer token is available
            if not st.secrets.get("TAB_BEARER_TOKEN"):
                st.sidebar.error("TAB API configuration is missing. Please contact support.")
                return

            with st.sidebar.form("login_form", clear_on_submit=True):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login")
                
                if submit:
                    if username and password:
                        with st.spinner("Authenticating..."):
                            if self._validate_login(username, password):
                                try:
                                    account_data = self._load_account(username)
                                    st.session_state.logged_in = True
                                    st.session_state.account = account_data
                                    st.success("Logged in successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to load account: {str(e)}")
                            else:
                                st.error("Invalid credentials or API error")
                    else:
                        st.error("Please enter both username and password")
        else:
            self.render_account_summary()

    def render_account_summary(self):
        """Render account summary with improved error handling"""
        if not st.session_state.account:
            return
            
        st.sidebar.subheader("Account")
        
        try:
            # Refresh account data
            client = TABApiClient(st.session_state.bearer_token)
            account_info = client.get_account_balance()
            
            if account_info.get('error'):
                st.sidebar.error("Failed to refresh account data")
                balance = st.session_state.account['balance']
            else:
                balance = Decimal(str(account_info.get('balance', 0)))
                st.session_state.account['balance'] = balance

            st.sidebar.metric("Balance", f"${balance:,.2f}")
            
            # Quick stats
            cols = st.sidebar.columns(2)
            with cols[0]:
                st.metric("Pending Bets", len(st.session_state.account['pending_bets']))
            with cols[1]:
                today_pl = self._calculate_daily_pl()
                st.metric("Today's P/L", f"${today_pl:,.2f}", delta=f"{today_pl:,.2f}")
            
        except Exception as e:
            logger.error(f"Error rendering account summary: {str(e)}")
            st.sidebar.error("Failed to update account information")

        # Account actions
        if st.sidebar.button("Logout"):
            self.logout()

    def _calculate_daily_pl(self) -> float:
        """Calculate daily profit/loss with improved error handling"""
        if not st.session_state.account:
            return 0.0
            
        try:
            client = TABApiClient(st.session_state.bearer_token)
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Get today's bet history
            history = client.get_bet_history(start_date=today, end_date=today)
            if history.get('error'):
                logger.error(f"Error getting bet history: {history['error']}")
                return 0.0
                
            return sum(bet.get('profit', 0) for bet in history.get('bets', []))
            
        except Exception as e:
            logger.error(f"Error calculating P/L: {str(e)}")
            return 0.0

    def logout(self):
        """Log out current user and clear session state"""
        st.session_state.logged_in = False
        st.session_state.account = None
        st.session_state.bearer_token = None
        st.rerun()
