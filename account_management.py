import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal
try:
    import pandas as pd
    import plotly.graph_objects as go
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False
from tab_api_client import TABApiClient, APIError
import pytz
import requests
import time
from utils.logger import frontend_logger, LoggerMixin, log_execution_time

class AccountManager(LoggerMixin):
    def __init__(self):
        super().__init__()
        # Check dependencies
        if not HAS_DEPENDENCIES:
            st.error("Required dependencies (pandas, plotly) not available. Please install them using: pip install --user pandas plotly")
            return
        # Initialize session state variables
        self._init_session_state()

    def _init_session_state(self):
        """Initialize all required session state variables"""
        session_vars = {
            'account': None,
            'logged_in': False,
            'tab_client': None,
            'account_token': None,
            'login_error': None,
            'auth_attempts': 0,
            'last_balance_check': None,
            'loading_state': False
        }
        
        for var, default in session_vars.items():
            if var not in st.session_state:
                st.session_state[var] = default

    def _validate_login(self, account_number: str, password: str) -> bool:
        try:
            if not st.session_state.tab_client:
                st.session_state.tab_client = TABApiClient()
                
            url = f"{st.session_state.tab_client.base_url}/oauth/token"
            
            # Log attempt (excluding password)
            self.logger.info(f"Attempting login for account: {account_number}")
            
            # Validate credentials before making request
            if not st.session_state.tab_client.client_id:
                self.logger.error("Missing TAB_CLIENT_ID environment variable")
                st.session_state.login_error = "System configuration error: Missing API client ID"
                return False
                
            if not st.session_state.tab_client.client_secret:
                self.logger.error("Missing TAB_CLIENT_SECRET environment variable") 
                st.session_state.login_error = "System configuration error: Missing API client secret"
                return False
                
            if not account_number or not password:
                self.logger.error("Missing account number or password")
                st.session_state.login_error = "Please enter both account number and password"
                return False
                
            data = {
                'grant_type': 'password',
                'client_id': st.session_state.tab_client.client_id,
                'client_secret': st.session_state.tab_client.client_secret,
                'username': account_number,
                'password': password
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            try:
                response = requests.post(
                    url,
                    data=data,
                    headers=headers,
                    timeout=30
                )
                
                self.logger.info(f"OAuth response status: {response.status_code}")
                self.logger.debug(f"OAuth response headers: {dict(response.headers)}")
                
                # Log full response for debugging (excluding sensitive data)
                try:
                    resp_data = response.json()
                    debug_data = {k:v for k,v in resp_data.items() if k not in ['access_token', 'refresh_token']}
                    self.logger.debug(f"OAuth response data: {debug_data}")
                except:
                    self.logger.debug("Could not parse response as JSON")
                
                if response.status_code == 200:
                    try:
                        auth_data = response.json()
                        if not auth_data.get('access_token'):
                            self.logger.error("Missing access token in response")
                            return False
                            
                        st.session_state.tab_client.bearer_token = auth_data['access_token']
                        st.session_state.tab_client.token_expiry = (
                            datetime.now(pytz.UTC) + 
                            timedelta(seconds=auth_data.get('expires_in', 3600))
                        )
                        
                        if refresh_token := auth_data.get('refresh_token'):
                            st.session_state.tab_client.refresh_token = refresh_token
                            
                        return True
                        
                    except ValueError as e:
                        self.logger.error(f"Failed to parse auth response: {str(e)}")
                        return False
                        
                elif response.status_code == 401:
                    self.logger.error("Invalid credentials")
                    st.session_state.login_error = "Invalid account number or password"
                    return False
                elif response.status_code == 400:
                    error_data = response.json()
                    error_msg = error_data.get('error_description', 'Unknown error')
                    self.logger.error(f"Bad request: {error_msg}")
                    st.session_state.login_error = f"Login error: {error_msg}"
                    return False
                else:
                    self.logger.error(f"Auth failed with status {response.status_code}")
                    st.session_state.login_error = "Authentication failed. Please try again."
                    return False
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"OAuth request failed: {str(e)}")
                st.session_state.login_error = "Connection error. Please try again later."
                return False
                
        except Exception as e:
            self.logger.error(f"Login error: {str(e)}")
            st.session_state.login_error = "An unexpected error occurred. Please try again."
            return False

    def _validate_account_data(self, account_data: Dict) -> bool:
        """Validate account data structure"""
        required_fields = ['balance', 'pending_bets', 'bet_history']
        
        try:
            if not all(field in account_data for field in required_fields):
                self.logger.error("Missing required account data fields")
                return False
                
            if not isinstance(account_data['balance'], (int, float, Decimal)):
                self.logger.error("Invalid balance data type")
                return False
                
            if not isinstance(account_data['pending_bets'], list):
                self.logger.error("Invalid pending bets data type")
                return False
                
            if not isinstance(account_data['bet_history'], list):
                self.logger.error("Invalid bet history data type")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Account data validation error: {str(e)}")
            return False

    def _load_account(self, account_number: str) -> Dict:
        """Load account details with improved error handling"""
        if not st.session_state.tab_client:
            raise ValueError("TAB API client not initialized")
            
        try:
            # Get account info with proper error handling
            try:
                st.session_state.loading_state = True
                
                account_info = st.session_state.tab_client.get_account_balance()
                pending_bets = st.session_state.tab_client.get_pending_bets()
                bet_history = st.session_state.tab_client.get_bet_history()
                
                account_data = {
                    'user_id': account_info.get('accountId', ''),
                    'account_number': account_number,
                    'balance': Decimal(str(account_info.get('balance', 0))),
                    'pending_bets': pending_bets.get('bets', []),
                    'bet_history': bet_history.get('bets', []),
                    'preferences': account_info.get('preferences', {})
                }
                
                if not self._validate_account_data(account_data):
                    raise ValueError("Invalid account data structure")
                    
                st.session_state.last_balance_check = datetime.now(pytz.UTC)
                return account_data
                
            except APIError as e:
                self.logger.error(f"API error while loading account: {str(e)}")
                raise
            finally:
                st.session_state.loading_state = False
                
        except Exception as e:
            self.logger.error(f"Unexpected error loading account: {str(e)}")
            raise

    def render_login(self):
        """Render login interface with improved error handling"""
        if not st.session_state.logged_in:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.title("🏇 Racing Analysis Platform")
                st.subheader("Login")
                
                # Show any existing error message
                if st.session_state.login_error:
                    st.error(st.session_state.login_error)
                    st.session_state.login_error = None
                
                with st.form("login_form", clear_on_submit=True):
                    account_number = st.text_input(
                        "TAB Account Number",
                        key="account_number_input",
                        autocomplete="username",
                        label_visibility="visible",
                        help="Enter your TAB account number"
                    )
                    password = st.text_input(
                        "Password", 
                        type="password",
                        key="password_input",
                        autocomplete="current-password",
                        label_visibility="visible",
                        help="Enter your account password"
                    )
                    
                    if st.form_submit_button("Login", use_container_width=True):
                        if account_number and password:
                            st.session_state.auth_attempts += 1
                            
                            # Add rate limiting
                            if st.session_state.auth_attempts > 5:
                                st.error("Too many login attempts. Please try again later.")
                                time.sleep(5)  # Add delay after multiple attempts
                            else:
                                # Show loading state instead of using spinner
                                st.session_state.loading_state = True
                                if self._validate_login(account_number, password):
                                    try:
                                        account_data = self._load_account(account_number)
                                        st.session_state.logged_in = True
                                        st.session_state.account = account_data
                                        st.session_state.auth_attempts = 0
                                        st.success("Login successful!")
                                        st.session_state.loading_state = False
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Failed to load account: {str(e)}")
                                st.session_state.loading_state = False
                        else:
                            st.error("Please enter both account number and password")
                
                # Show loading indicator
                if st.session_state.loading_state:
                    st.info("Authenticating...")
                
                # Add helper text
                st.markdown("---")
                st.markdown("""
                    Need help? [Contact TAB Support](https://tab.com.au/help)
                    
                    Having trouble logging in?
                    - Make sure your account number and password are correct
                    - Check if you have API access enabled
                    - Contact support if you continue having issues
                """)
        else:
            self.render_account_summary()

    def render_account_summary(self):
        """Render account summary with improved error handling"""
        if not st.session_state.account:
            return
            
        st.sidebar.subheader("Account")
        
        try:
            # Check if we need to refresh account data (every 5 minutes)
            if (st.session_state.last_balance_check is None or 
                datetime.now(pytz.UTC) - st.session_state.last_balance_check > timedelta(minutes=5)):
                
                # Show loading state instead of using spinner
                st.session_state.loading_state = True
                account_info = st.session_state.tab_client.get_account_balance()
                st.session_state.loading_state = False
                
                if account_info.get('error'):
                    st.sidebar.warning("Unable to refresh account data")
                    balance = st.session_state.account['balance']
                else:
                    balance = Decimal(str(account_info.get('balance', 0)))
                    st.session_state.account['balance'] = balance
                    st.session_state.last_balance_check = datetime.now(pytz.UTC)
            else:
                balance = st.session_state.account['balance']

            st.sidebar.metric("Balance", f"${balance:,.2f}")
            
            # Quick stats
            cols = st.sidebar.columns(2)
            with cols[0]:
                pending_count = len(st.session_state.account['pending_bets'])
                st.metric("Pending Bets", pending_count)
            with cols[1]:
                today_pl = self._calculate_daily_pl()
                st.metric("Today's P/L", f"${today_pl:,.2f}", 
                         delta=f"{today_pl:,.2f}", 
                         delta_color="normal")
            
        except Exception as e:
            self.logger.error(f"Error rendering account summary: {str(e)}")
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
                self.logger.error(f"Error getting bet history: {history['error']}")
                return 0.0
                
            return sum(bet.get('profit', 0) for bet in history.get('bets', []))
            
        except Exception as e:
            self.logger.error(f"Error calculating P/L: {str(e)}")
            return 0.0

    def logout(self):
        """Log out current user and clear session state"""
        session_vars = [
            'logged_in', 'account', 'tab_client', 'account_token',
            'login_error', 'auth_attempts', 'last_balance_check',
            'loading_state'
        ]
        
        for var in session_vars:
            if var in st.session_state:
                st.session_state[var] = None
                
        st.session_state.logged_in = False
        st.rerun()
