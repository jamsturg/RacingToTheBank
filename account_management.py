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
        if 'tab_client' not in st.session_state:
            st.session_state.tab_client = None
        if 'account_token' not in st.session_state:
            st.session_state.account_token = None

    def _validate_login(self, account_number: str, password: str) -> bool:
        """Validate login credentials using TAB API"""
        try:
            # Initialize API client with OAuth credentials
            if not st.session_state.tab_client:
                st.session_state.tab_client = TABApiClient()
            
            # Make authentication request to TAB API
            response = st.session_state.tab_client.session.post(
                f"{st.session_state.tab_client.base_url}/v1/account/login",
                json={
                    'accountNumber': account_number,
                    'password': password
                }
            )
            
            if response.status_code == 200:
                auth_data = response.json()
                st.session_state.account_token = auth_data.get('token')
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False

    def _load_account(self, account_number: str) -> Dict:
        """Load account details from TAB API"""
        if not st.session_state.tab_client:
            raise ValueError("TAB API client not initialized")
            
        try:
            # Get account info with proper error handling
            try:
                account_info = st.session_state.tab_client.get_account_balance()
                if account_info.get('error'):
                    raise APIError(f"Failed to get account balance: {account_info['error']}")

                pending_bets = st.session_state.tab_client.get_pending_bets()
                if pending_bets.get('error'):
                    raise APIError(f"Failed to get pending bets: {pending_bets['error']}")

                bet_history = st.session_state.tab_client.get_bet_history()
                if bet_history.get('error'):
                    raise APIError(f"Failed to get bet history: {bet_history['error']}")

                return {
                    'user_id': account_info.get('accountId', ''),
                    'account_number': account_number,
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
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.title("🏇 Racing Analysis Platform")
                st.subheader("Login")
                
                with st.form("login_form", clear_on_submit=True):
                    account_number = st.text_input("TAB Account Number", key="login_account")
                    password = st.text_input("Password", type="password", key="login_password")
                    
                    if st.form_submit_button("Login", use_container_width=True):
                        if account_number and password:
                            with st.spinner("Authenticating..."):
                                if self._validate_login(account_number, password):
                                    try:
                                        account_data = self._load_account(account_number)
                                        st.session_state.logged_in = True
                                        st.session_state.account = account_data
                                        st.success("Login successful!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Failed to load account: {str(e)}")
                                else:
                                    st.error("Invalid account number or password")
                        else:
                            st.error("Please enter both account number and password")
                
                # Add some helper text
                st.markdown("---")
                st.markdown("Need help? [Contact TAB Support](https://tab.com.au/help)")
        else:
            self.render_account_summary()

    def render_account_summary(self):
        """Render account summary with improved error handling"""
        if not st.session_state.account:
            return
            
        st.sidebar.subheader("Account")
        
        try:
            # Refresh account data
            account_info = st.session_state.tab_client.get_account_balance()
            
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
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Get today's bet history
            history = st.session_state.tab_client.get_bet_history(start_date=today, end_date=today)
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
        st.session_state.tab_client = None
        st.session_state.account_token = None
        st.rerun()
