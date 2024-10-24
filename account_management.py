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

    def render_login(self):
        """Render login interface"""
        st.sidebar.header("Account")
        
        if not st.session_state.logged_in:
            with st.sidebar.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                
                if st.form_submit_button("Login"):
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
        
        st.sidebar.metric("Balance", f"${account.balance:,.2f}")
        
        # Quick stats
        cols = st.sidebar.columns(2)
        with cols[0]:
            st.metric(
                "Pending Bets",
                len(account.pending_bets)
            )
        with cols[1]:
            today_pl = self._calculate_daily_pl()
            st.metric(
                "Today's P/L",
                f"${today_pl:,.2f}",
                delta=f"{today_pl:,.2f}"
            )
        
        # Account actions
        if st.sidebar.button("Deposit"):
            self.render_deposit_dialog()
        if st.sidebar.button("Withdraw"):
            self.render_withdraw_dialog()
        if st.sidebar.button("Logout"):
            self.logout()

    def render_account_page(self):
        """Render full account page"""
        st.header("Account Management")
        
        tabs = st.tabs([
            "Bet History",
            "Pending Bets",
            "Statistics",
            "Preferences"
        ])
        
        with tabs[0]:
            self.render_bet_history()
        
        with tabs[1]:
            self.render_pending_bets()
        
        with tabs[2]:
            self.render_statistics()
        
        with tabs[3]:
            self.render_preferences()

    def render_bet_history(self):
        """Render bet history with analysis"""
        account = st.session_state.account
        
        if not account.bet_history:
            st.write("No bet history available")
            return
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            date_range = st.selectbox(
                "Date Range",
                ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"]
            )
        with col2:
            bet_type = st.multiselect(
                "Bet Type",
                ["Win", "Place", "Each Way", "Multi"]
            )
        with col3:
            status = st.multiselect(
                "Status",
                ["Won", "Lost", "Pending"]
            )
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(account.bet_history)
        
        # Apply filters
        if date_range != "All Time":
            days = int(date_range.split()[1])
            df = df[df['date'] >= (datetime.now() - timedelta(days=days))]
        if bet_type:
            df = df[df['bet_type'].isin(bet_type)]
        if status:
            df = df[df['status'].isin(status)]
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Bets", len(df))
        with col2:
            win_rate = len(df[df['status'] == 'Won']) / len(df) * 100
            st.metric("Win Rate", f"{win_rate:.1f}%")
        with col3:
            roi = ((df['return'].sum() - df['stake'].sum()) / df['stake'].sum()) * 100
            st.metric("ROI", f"{roi:.1f}%")
        with col4:
            avg_odds = df['odds'].mean()
            st.metric("Avg Odds", f"${avg_odds:.2f}")
        
        # Detailed history
        st.dataframe(
            df[[
                'date', 'race', 'runner', 'bet_type',
                'stake', 'odds', 'return', 'status'
            ]],
            use_container_width=True
        )
        
        # Performance charts
        col1, col2 = st.columns(2)
        with col1:
            self._plot_cumulative_pl(df)
        with col2:
            self._plot_bet_type_performance(df)

    def render_pending_bets(self):
        """Render pending bets interface"""
        account = st.session_state.account
        
        if not account.pending_bets:
            st.write("No pending bets")
            return
        
        for bet in account.pending_bets:
            with st.expander(
                f"{bet['race']} - {bet['runner']} ({bet['bet_type']})"
            ):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"Stake: ${bet['stake']:.2f}")
                    st.write(f"Odds: ${bet['odds']:.2f}")
                with col2:
                    st.write(f"Potential Return: ${bet['stake'] * bet['odds']:.2f}")
                    if st.button("Cancel Bet", key=f"cancel_{bet['id']}"):
                        self._cancel_bet(bet['id'])

    def render_statistics(self):
        """Render detailed betting statistics"""
        account = st.session_state.account
        df = pd.DataFrame(account.bet_history)
        
        # Performance by race type
        st.subheader("Performance by Race Type")
        race_type_stats = df.groupby('race_type').agg({
            'stake': 'sum',
            'return': 'sum',
            'id': 'count'
        }).round(2)
        race_type_stats['roi'] = (
            (race_type_stats['return'] - race_type_stats['stake'])
            / race_type_stats['stake'] * 100
        ).round(2)
        st.dataframe(race_type_stats)
        
        # Track performance
        st.subheader("Track Performance")
        track_stats = df.groupby('track').agg({
            'stake': 'sum',
            'return': 'sum',
            'id': 'count'
        }).round(2)
        track_stats['roi'] = ((track_stats['return'] - track_stats['stake']) / track_stats['stake'] * 100).round(2)
        st.dataframe(track_stats)
        
        # Track performance
        st.subheader("Track Performance")
        track_stats = df.groupby('track').agg({
            'stake': 'sum',
            'return': 'sum',
            'id': 'count'
        }).round(2)
        track_stats['roi'] = ((track_stats['return'] - track_stats['stake']) / track_stats['stake'] * 100).round(2)
        
        # Show top/bottom performing tracks
        col1, col2 = st.columns(2)
        with col1:
            st.write("Best Performing Tracks")
            st.dataframe(track_stats.nlargest(5, 'roi'))
        with col2:
            st.write("Worst Performing Tracks")
            st.dataframe(track_stats.nsmallest(5, 'roi'))
        
        # Odds range analysis
        st.subheader("Performance by Odds Range")
        df['odds_range'] = pd.cut(df['odds'], 
            bins=[0, 2, 5, 10, 20, float('inf')],
            labels=['Under $2', '$2-$5', '$5-$10', '$10-$20', 'Over $20']
        )
        odds_stats = df.groupby('odds_range').agg({
            'stake': 'sum',
            'return': 'sum',
            'id': 'count'
        }).round(2)
        odds_stats['roi'] = ((odds_stats['return'] - odds_stats['stake']) / odds_stats['stake'] * 100).round(2)
        st.dataframe(odds_stats)
        
        # Time-based analysis
        st.subheader("Performance by Time")
        df['month'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m')
        monthly_stats = df.groupby('month').agg({
            'stake': 'sum',
            'return': 'sum',
            'id': 'count'
        }).round(2)
        monthly_stats['roi'] = ((monthly_stats['return'] - monthly_stats['stake']) / monthly_stats['stake'] * 100).round(2)
        
        # Plot monthly performance
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=monthly_stats.index,
            y=monthly_stats['roi'],
            name='ROI %'
        ))
        fig.add_trace(go.Scatter(
            x=monthly_stats.index,
            y=monthly_stats['return'] - monthly_stats['stake'],
            name='Profit/Loss',
            yaxis='y2'
        ))
        fig.update_layout(
            title='Monthly Performance',
            yaxis_title='ROI %',
            yaxis2=dict(
                title='Profit/Loss ($)',
                overlaying='y',
                side='right'
            )
        )
        st.plotly_chart(fig)

    def render_preferences(self):
        """Render account preferences"""
        account = st.session_state.account
        
        st.subheader("Account Preferences")
        
        # Default bet settings
        st.write("Default Bet Settings")
        col1, col2 = st.columns(2)
        with col1:
            default_stake = st.number_input(
                "Default Stake ($)",
                min_value=1.0,
                value=float(account.preferences.get('default_stake', 10.0))
            )
        with col2:
            default_bet_type = st.selectbox(
                "Default Bet Type",
                options=["Win", "Place", "Each Way"],
                index=["Win", "Place", "Each Way"].index(
                    account.preferences.get('default_bet_type', 'Win')
                )
            )
        
        # Notification settings
        st.write("Notification Settings")
        notifications = {
            'price_changes': st.checkbox(
                "Price Changes",
                value=account.preferences.get('notify_price_changes', True)
            ),
            'results': st.checkbox(
                "Race Results",
                value=account.preferences.get('notify_results', True)
            ),
            'deposits': st.checkbox(
                "Deposits/Withdrawals",
                value=account.preferences.get('notify_transactions', True)
            )
        }
        
        # Display settings
        st.write("Display Settings")
        display = {
            'odds_format': st.selectbox(
                "Odds Format",
                options=["Decimal", "Fractional"],
                index=["Decimal", "Fractional"].index(
                    account.preferences.get('odds_format', 'Decimal')
                )
            ),
            'timezone': st.selectbox(
                "Timezone",
                options=["Local", "AEST"],
                index=["Local", "AEST"].index(
                    account.preferences.get('timezone', 'AEST')
                )
            )
        }
        
        # Save preferences
        if st.button("Save Preferences"):
            account.preferences.update({
                'default_stake': default_stake,
                'default_bet_type': default_bet_type,
                'notify_price_changes': notifications['price_changes'],
                'notify_results': notifications['results'],
                'notify_transactions': notifications['deposits'],
                'odds_format': display['odds_format'],
                'timezone': display['timezone']
            })
            st.success("Preferences saved successfully!")
