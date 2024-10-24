```python
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from utils.helpers import format_odds, calculate_roi
from utils.visualization import create_roi_chart, create_bankroll_chart

def render_account_page():
    st.title("Account Management")

    # Account dashboard tabs
    tabs = st.tabs([
        "Overview",
        "Banking",
        "Betting History",
        "Statistics",
        "Settings"
    ])

    with tabs[0]:
        render_account_overview()
    with tabs[1]:
        render_banking()
    with tabs[2]:
        render_detailed_history()
    with tabs[3]:
        render_statistics()
    with tabs[4]:
        render_account_settings()

def render_account_overview():
    """Render account overview section"""
    # Account metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Balance",
            f"${st.session_state.balance:.2f}",
            f"{get_daily_pl():+.2f}"
        )
        
    with col2:
        pending_returns = sum(
            bet['stake'] * bet['odds']
            for bet in st.session_state.get('active_bets', [])
        )
        st.metric(
            "Pending Returns",
            f"${pending_returns:.2f}",
            f"{len(st.session_state.get('active_bets', []))} bets"
        )
        
    with col3:
        win_rate = calculate_win_rate()
        st.metric(
            "Win Rate",
            f"{win_rate:.1f}%",
            f"{calculate_win_rate_change():+.1f}%"
        )
        
    with col4:
        roi = calculate_roi()
        st.metric(
            "ROI",
            f"{roi:.1f}%",
            f"{calculate_roi_change():+.1f}%"
        )

    # Bankroll chart
    st.subheader("Bankroll History")
    fig = create_bankroll_chart(
        st.session_state.get('balance_history', [])
    )
    st.plotly_chart(fig, use_container_width=True)

    # Recent activity
    st.subheader("Recent Activity")
    render_recent_activity()

def render_banking():
    """Render banking section"""
    st.subheader("Banking")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Deposit**")
        deposit_amount = st.number_input(
            "Deposit Amount ($)",
            min_value=10.0,
            max_value=10000.0,
            value=100.0,
            key="deposit"
        )
        
        if st.button("Make Deposit"):
            make_deposit(deposit_amount)
            st.success(f"Deposited ${deposit_amount:.2f}")
            st.rerun()

    with col2:
        st.write("**Withdrawal**")
        max_withdrawal = st.session_state.balance
        withdrawal_amount = st.number_input(
            "Withdrawal Amount ($)",
            min_value=10.0,
            max_value=max_withdrawal,
            value=min(100.0, max_withdrawal),
            key="withdrawal"
        )
        
        if st.button("Make Withdrawal"):
            if withdrawal_amount <= st.session_state.balance:
                make_withdrawal(withdrawal_amount)
                st.success(f"Withdrawn ${withdrawal_amount:.2f}")
                st.rerun()
            else:
                st.error("Insufficient funds")

    # Transaction history
    st.subheader("Transaction History")
    transactions = st.session_state.get('transactions', [])
    
    if transactions:
        df = pd.DataFrame([
            {
                'Date': t['timestamp'].strftime('%Y-%m-%d %H:%M'),
                'Type': t['type'],
                'Amount': f"${t['amount']:.2f}",
                'Balance': f"${t['balance']:.2f}",
                'Status': t['status']
            }
            for t in transactions
        ])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No transactions found")

def render_detailed_history():
    """Render detailed betting history"""
    st.subheader("Betting History")

    # Filters
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

    # Get filtered bets
    bets = filter_bets(date_range, bet_type, status)
    
    if bets:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Bets", len(bets))
        
        with col2:
            total_stake = sum(bet['stake'] for bet in bets)
            st.metric("Total Stake", f"${total_stake:.2f}")
        
        with col3:
            total_return = sum(
                bet.get('return_amount', 0) for bet in bets
            )
            st.metric(
                "Total Return",
                f"${total_return:.2f}",
                f"{(total_return/total_stake - 1)*100:.1f}% ROI"
            )
        
        with col4:
            winners = len([b for b in bets if b['result'] == 'Won'])
            st.metric(
                "Win Rate",
                f"{(winners/len(bets))*100:.1f}%"
            )

        # Detailed history
        st.subheader("Bet Details")
        details_df = pd.DataFrame([
            {
                'Date': bet['placed_at'].strftime('%Y-%m-%d %H:%M'),
                'Race': bet['race'],
                'Runner': bet['runner'],
                'Type': bet['bet_type'],
                'Odds': format_odds(bet['odds']),
                'Stake': f"${bet['stake']:.2f}",
                'Result': bet['result'],
                'Return': f"${bet.get('return_amount', 0):.2f}"
            }
            for bet in bets
        ])
        st.dataframe(details_df, use_container_width=True)

        # Performance chart
        st.subheader("Performance Chart")
        fig = create_roi_chart(bets)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No bets found matching the selected filters")

def render_statistics():
    """Render detailed statistics"""
    st.subheader("Betting Statistics")

    # Analysis tabs
    tabs = st.tabs([
        "Performance Metrics",
        "Bet Type Analysis",
        "Track Analysis",
        "Time Analysis"
    ])

    with tabs[0]:
        render_performance_metrics()
    with tabs[1]:
        render_bet_type_stats()
    with tabs[2]:
        render_track_stats()
    with tabs[3]:
        render_time_stats()

def render_account_settings():
    """Render account settings"""
    st.subheader("Account Settings")

    # Betting limits
    st.write("**Betting Limits**")
    col1, col2 = st.columns(2)
    
    with col1:
        max_stake = st.number_input(
            "Maximum Stake ($)",
            min_value=1.0,
            max_value=st.session_state.balance,
            value=float(st.session_state.get('max_stake', 100.0))
        )
    
    with col2:
        daily_limit = st.number_input(
            "Daily Betting Limit ($)",
            min_value=1.0,
            value=float(st.session_state.get('daily_limit', 500.0))
        )

    # Notification settings
    st.write("**Notifications**")
    notifications = {
        'price_changes': st.toggle(
            "Price Changes",
            value=st.session_state.get('notify_price_changes', True)
        ),
        'results': st.toggle(
            "Race Results",
            value=st.session_state.get('notify_results', True)
        ),
        'deposits': st.toggle(
            "Deposits/Withdrawals",
            value=st.session_state.get('notify_transactions', True)
        )
    }

    # Save settings
    if st.button("Save Settings"):
        save_account_settings(
            max_stake=max_stake,
            daily_limit=daily_limit,
            notifications=notifications
        )
        st.success("Settings saved successfully!")

def render_recent_activity():
    """Render recent account activity"""
    activities = get_recent_activities()
    
    if activities:
        for activity in activities:
            with st.expander(
                f"{activity['type']} - {activity['timestamp'].strftime('%Y-%m-%d %H:%M')}"
            ):
                st.write(f"**Details:** {activity['details']}")
                if 'amount' in activity:
                    st.write(f"**Amount:** ${activity['amount']:.2f}")
                st.write(f"**Status:** {activity['status']}")
    else:
        st.info("No recent activity")

def filter_bets(date_range: str, bet_types: List[str], statuses: List[str]) -> List[Dict]:
    """Filter bets based on criteria"""
    bets = st.session_state.get('bet_history', [])
    
    # Date filter
    if date_range == "Last 7 Days":
        cutoff = datetime.now() - timedelta(days=7)
    elif date_range == "Last 30 Days":
        cutoff = datetime.now() - timedelta(days=30)
    elif date_range == "Last 90 Days":
        cutoff = datetime.now() - timedelta(days=90)
    else:
        cutoff = datetime.min
    
    filtered = [
        bet for bet in bets
        if bet['placed_at'] >= cutoff
        and (not bet_types or bet['bet_type'] in bet_types)
        and (not statuses or bet['result'] in statuses)
    ]
    
    return filtered

def make_deposit(amount: float):
    """Process deposit"""
    transaction = {
        'type': 'Deposit',
        'amount': amount,
        'timestamp': datetime.now(),
        'status': 'Completed',
        'balance': st.session_state.balance + amount
    }
    
    st.session_state.balance += amount
    st.session_state.transactions = st.session_state.get('transactions', []) + [transaction]
    add_activity("Deposit", f"Deposited ${amount:.2f}", amount)

def make_withdrawal(amount: float):
    """Process withdrawal"""
    transaction = {
        'type': 'Withdrawal',
        'amount': amount,
        'timestamp': datetime.now(),
        'status': 'Completed',
        'balance': st.session_state.balance - amount
    }
    
    st.session_state.balance -= amount
    st.session_state.transactions = st.session_state.get('transactions', []) + [transaction]
    add_activity("Withdrawal", f"Withdrawn ${amount:.2f}", amount)

def save_account_settings(max_stake: float, daily_limit: float, notifications: Dict):
    """Save account settings"""
    st.session_state.max_stake = max_stake
    st.session_state.daily_limit = daily_limit
    st.session_state.notify_price_changes = notifications['price_changes']
    st.session_state.notify_results = notifications['results']
    st.session_state.notify_transactions = notifications['deposits']

def add_activity(activity_type: str, details: str, amount: Optional[float] = None):
    """Add activity to recent activity log"""
    activity = {
        'type': activity_type,
        'details': details,
        'timestamp': datetime.now(),
        'status': 'Completed'
    }
    
    if amount is not None:
        activity['amount'] = amount
    
    st.session_state.activities = st.session_state.get('activities', []) + [activity]

if __name__ == "__main__":
    st.set_page_config(
        page_title="Account Management",
        page_icon="👤",
        layout="wide"
    )
    render_account_page()
```

Let me continue with visualization utilities. Would you like me to:
1. Add visualization utilities next?
2. Continue with betting strategies?
3. Add helper functions?
4. Add more components?

Let me know which part you'd like to see next!