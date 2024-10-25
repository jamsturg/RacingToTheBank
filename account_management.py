import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal
import pandas as pd
from dataclasses import dataclass
import plotly.graph_objects as go

@dataclass
class Account:
    user_id: str
    username: str
    balance: Decimal
    pending_bets: List[Dict]
    bet_history: List[Dict]
    preferences: Dict

class AccountManager:
    def __init__(self):
        if 'account' not in st.session_state:
            st.session_state.account = None
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False

    def _validate_login(self, username: str, password: str) -> bool:
        # For demo, use simple validation
        return username and password

    def _load_account(self, username: str) -> Account:
        """Load account data for the given username"""
        # For demo, return mock account data
        return Account(
            user_id="12345",
            username=username,
            balance=Decimal("1000.00"),
            pending_bets=[],
            bet_history=[],
            preferences={
                'default_stake': 10.0,
                'default_bet_type': 'Win',
                'odds_format': 'Decimal',
                'timezone': 'AEST'
            }
        )

    def render_login(self):
        """Render login interface"""
        if not st.session_state.logged_in:
            st.sidebar.title("Login")
            with st.sidebar.form("login_form", clear_on_submit=True):
                username = st.text_input("Username", key="login_username")
                password = st.text_input("Password", type="password", key="login_password")
                
                if st.form_submit_button("Login", key="login_submit"):
                    if self._validate_login(username, password):
                        st.session_state.logged_in = True
                        st.session_state.account = self._load_account(username)
                        st.success("Logged in successfully!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
        else:
            self.render_account_summary()

    def render_account_summary(self):
        """Render account summary"""
        account = st.session_state.account
        
        st.sidebar.subheader("Account")
        st.sidebar.metric("Balance", f"${account.balance:,.2f}", key="account_balance")
        
        # Quick stats
        cols = st.sidebar.columns(2)
        with cols[0]:
            st.metric(
                "Pending Bets",
                len(account.pending_bets),
                key="pending_bets_count"
            )
        with cols[1]:
            today_pl = self._calculate_daily_pl()
            st.metric(
                "Today's P/L",
                f"${today_pl:,.2f}",
                delta=f"{today_pl:,.2f}",
                key="daily_pl"
            )
        
        # Account actions
        if st.sidebar.button("Deposit", key="deposit_button"):
            self.render_deposit_dialog()
        if st.sidebar.button("Withdraw", key="withdraw_button"):
            self.render_withdraw_dialog()
        if st.sidebar.button("Logout", key="logout_button"):
            self.logout()

    def _calculate_daily_pl(self) -> float:
        """Calculate daily profit/loss"""
        # For demo, return mock value
        return 150.00

    def logout(self):
        """Log out current user"""
        st.session_state.logged_in = False
        st.session_state.account = None
        st.rerun()

    def render_deposit_dialog(self):
        """Render deposit interface"""
        st.sidebar.write("Deposit functionality coming soon")

    def render_withdraw_dialog(self):
        """Render withdraw interface"""
        st.sidebar.write("Withdraw functionality coming soon")
