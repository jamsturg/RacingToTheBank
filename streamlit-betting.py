```python
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from utils.helpers import format_odds, calculate_roi
from utils.visualization import create_odds_movement_chart
from utils.betting_strategies import ValueBettingStrategy, DutchingStrategy, EachWayStrategy

def render_betting_page():
    st.title("Betting Dashboard")

    # Betting dashboard tabs
    tabs = st.tabs([
        "Active Bets",
        "Automated Betting",
        "Multi Builder",
        "Betting History",
        "Performance"
    ])

    with tabs[0]:
        render_active_bets()
    with tabs[1]:
        render_automated_betting()
    with tabs[2]:
        render_multi_builder()
    with tabs[3]:
        render_betting_history()
    with tabs[4]:
        render_performance_analysis()

def render_active_bets():
    """Render active bets section"""
    st.subheader("Active Bets")

    active_bets = st.session_state.get('active_bets', [])
    
    if not active_bets:
        st.info("No active bets")
        return

    # Create bets dataframe
    bets_df = pd.DataFrame([
        {
            'Race': f"{bet['venue']} R{bet['race_number']}",
            'Runner': bet['runner_name'],
            'Type': bet['bet_type'],
            'Odds': format_odds(bet['odds']),
            'Stake': f"${bet['stake']:.2f}",
            'Potential Return': f"${bet['stake'] * bet['odds']:.2f}"
        }
        for bet in active_bets
    ])

    st.dataframe(bets_df, use_container_width=True)

    # Risk analysis
    col1, col2 = st.columns(2)
    
    with col1:
        total_stake = sum(bet['stake'] for bet in active_bets)
        total_potential = sum(bet['stake'] * bet['odds'] for bet in active_bets)
        
        st.metric(
            "Total Exposure",
            f"${total_stake:.2f}",
            f"{(total_stake/st.session_state.balance)*100:.1f}% of bank"
        )
        
    with col2:
        st.metric(
            "Potential Return",
            f"${total_potential:.2f}",
            f"{(total_potential/total_stake - 1)*100:.1f}% ROI"
        )

def render_automated_betting():
    """Render automated betting section"""
    st.subheader("Automated Betting")

    # Strategy selection
    strategy_type = st.selectbox(
        "Select Strategy",
        ["Value Betting", "Dutching", "Each Way"]
    )

    # Strategy configuration
    col1, col2 = st.columns(2)
    
    with col1:
        if strategy_type == "Value Betting":
            min_odds = st.number_input("Minimum Odds", 2.0, 20.0, 3.0)
            max_odds = st.number_input("Maximum Odds", min_odds, 50.0, 10.0)
            edge_threshold = st.slider("Required Edge (%)", 5, 30, 15)
            
            strategy = ValueBettingStrategy(
                min_odds=min_odds,
                max_odds=max_odds,
                edge_threshold=edge_threshold/100
            )
            
        elif strategy_type == "Dutching":
            target_profit = st.number_input("Target Profit ($)", 10.0, 1000.0, 100.0)
            max_runners = st.number_input("Maximum Runners", 2, 6, 3)
            
            strategy = DutchingStrategy(
                target_profit=target_profit,
                max_runners=max_runners
            )
            
        else:  # Each Way
            min_place_odds = st.number_input("Minimum Place Odds", 1.5, 10.0, 2.0)
            max_stake = st.number_input("Maximum Stake", 10.0, 1000.0, 100.0)
            
            strategy = EachWayStrategy(
                min_place_odds=min_place_odds,
                max_stake=max_stake
            )

    with col2:
        st.write("**Risk Management**")
        max_exposure = st.slider("Maximum Exposure (%)", 1, 50, 20)
        stop_loss = st.slider("Daily Stop Loss (%)", 1, 50, 25)
        
        # Apply to strategy
        strategy.set_risk_limits(
            max_exposure=max_exposure/100,
            stop_loss=stop_loss/100
        )

    # Strategy control
    if st.button("Activate Strategy", type="primary"):
        st.session_state.active_strategy = strategy
        st.success(f"{strategy_type} strategy activated!")

    # Show active opportunities
    if hasattr(st.session_state, 'active_strategy'):
        opportunities = strategy.find_opportunities(
            st.session_state.client.get_next_races()
        )
        
        if opportunities:
            st.subheader("Current Opportunities")
            for opp in opportunities:
                with st.expander(f"{opp['runner']} @ {format_odds(opp['odds'])}"):
                    st.write(f"Race: {opp['race']}")
                    st.write(f"Expected Value: {opp['ev']:.1f}%")
                    st.write(f"Recommended Stake: ${opp['stake']:.2f}")
                    
                    if st.button("Place Bet", key=f"auto_bet_{opp['id']}"):
                        place_automated_bet(opp)
        else:
            st.info("No current opportunities match strategy criteria")

def render_multi_builder():
    """Render multi bet builder"""
    st.subheader("Multi Builder")

    # Race selection
    races = st.session_state.client.get_next_races(max_races=10)
    
    selected_bets = []
    total_odds = 1.0
    
    for race in races:
        with st.expander(f"{race['venue']} R{race['number']}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                runner = st.selectbox(
                    "Select Runner",
                    [r['name'] for r in race['runners']],
                    key=f"multi_{race['number']}"
                )
            
            with col2:
                if runner:
                    runner_data = next(
                        r for r in race['runners']
                        if r['name'] == runner
                    )
                    st.metric("Odds", format_odds(runner_data['fixed_odds']))
                    
                    if st.button("Add", key=f"add_multi_{race['number']}"):
                        selected_bets.append({
                            'race': f"{race['venue']} R{race['number']}",
                            'runner': runner,
                            'odds': runner_data['fixed_odds']
                        })
                        total_odds *= runner_data['fixed_odds']

    if selected_bets:
        st.subheader("Selected Bets")
        
        for bet in selected_bets:
            st.write(f"• {bet['race']}: {bet['runner']} @ {format_odds(bet['odds'])}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Multi Odds", format_odds(total_odds))
            stake = st.number_input("Stake ($)", 1.0, 1000.0, 10.0)
            
        with col2:
            potential_return = stake * total_odds
            st.metric(
                "Potential Return",
                f"${potential_return:.2f}",
                f"{(potential_return/stake - 1)*100:.1f}%"
            )
            
            if st.button("Place Multi", type="primary"):
                if stake <= st.session_state.balance:
                    place_multi_bet(selected_bets, stake)
                    st.success("Multi bet placed successfully!")
                else:
                    st.error("Insufficient balance!")

def render_betting_history():
    """Render betting history and analysis"""
    st.subheader("Betting History")

    # Date range selection
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("From Date")
    with col2:
        end_date = st.date_input("To Date")

    # Get filtered bet history
    bets = get_filtered_bets(start_date, end_date)
    
    if not bets:
        st.info("No bets found for selected period")
        return

    # Performance metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_bets = len(bets)
        st.metric("Total Bets", total_bets)
        
    with col2:
        winners = len([b for b in bets if b['result'] == 'Won'])
        win_rate = (winners / total_bets) * 100 if total_bets > 0 else 0
        st.metric("Win Rate", f"{win_rate:.1f}%")
        
    with col3:
        total_stake = sum(b['stake'] for b in bets)
        total_return = sum(
            b['return_amount'] for b in bets
            if b.get('return_amount')
        )
        profit = total_return - total_stake
        st.metric(
            "Profit/Loss",
            f"${profit:.2f}",
            f"{(profit/total_stake)*100:.1f}% ROI" if total_stake > 0 else "0%"
        )
        
    with col4:
        avg_odds = sum(b['odds'] for b in bets) / len(bets)
        st.metric("Average Odds", format_odds(avg_odds))

    # Performance chart
    fig = create_performance_chart(bets)
    st.plotly_chart(fig, use_container_width=True)

    # Detailed history
    st.subheader("Bet Details")
    history_df = pd.DataFrame([
        {
            'Date': b['placed_at'].strftime('%Y-%m-%d %H:%M'),
            'Race': b['race'],
            'Runner': b['runner'],
            'Type': b['bet_type'],
            'Odds': format_odds(b['odds']),
            'Stake': f"${b['stake']:.2f}",
            'Result': b['result'],
            'Return': f"${b.get('return_amount', 0):.2f}"
        }
        for b in bets
    ])
    
    st.dataframe(history_df, use_container_width=True)

def render_performance_analysis():
    """Render detailed performance analysis"""
    st.subheader("Performance Analysis")

    # Get complete bet history
    bets = st.session_state.get('bet_history', [])
    
    if not bets:
        st.info("No betting history available")
        return

    # Analysis tabs
    tabs = st.tabs([
        "Overview",
        "Bet Type Analysis",
        "Odds Analysis",
        "Time Analysis",
        "ROI Analysis"
    ])

    with tabs[0]:
        render_performance_overview(bets)
    with tabs[1]:
        render_bet_type_analysis(bets)
    with tabs[2]:
        render_odds_analysis(bets)
    with tabs[3]:
        render_time_analysis(bets)
    with tabs[4]:
        render_roi_analysis(bets)

def place_automated_bet(opportunity):
    """Place bet from automated strategy"""
    if opportunity['stake'] <= st.session_state.balance:
        bet = {
            'id': str(len(st.session_state.get('active_bets', []))),
            'race': opportunity['race'],
            'runner': opportunity['runner'],
            'odds': opportunity['odds'],
            'stake': opportunity['stake'],
            'bet_type': 'Win',
            'placed_at': datetime.now()
        }
        
        st.session_state.active_bets = st.session_state.get('active_bets', []) + [bet]
        st.session_state.balance -= opportunity['stake']
        st.success("Bet placed successfully!")
        st.rerun()
    else:
        st.error("Insufficient balance!")

def place_multi_bet(bets, stake):
    """Place multi bet"""
    multi_odds = 1.0
    for bet in bets:
        multi_odds *= bet['odds']

    bet = {
        'id': str(len(st.session_state.get('active_bets', []))),
        'bets': bets,
        'odds': multi_odds,
        'stake': stake,
        'bet_type': 'Multi',
        'placed_at': datetime.now()
    }
    
    st.session_state.active_bets = st.session_state.get('active_bets', []) + [bet]
    st.session_state.balance -= stake
    st.rerun()

def get_filtered_bets(start_date, end_date):
    """Get filtered betting history"""
    bets = st.session_state.get('bet_history', [])
    
    return [
        bet for bet in bets
        if start_date <= bet['placed_at'].date() <= end_date
    ]

def create_performance_chart(bets):
    """Create performance chart"""
    fig = go.Figure()

    # Calculate cumulative P/L
    cumulative_pl = []
    running_pl = 0
    
    for bet in sorted(bets, key=lambda x: x['placed_at']):
        if bet['result'] == 'Won':
            pl = bet.get('return_amount', 0) - bet['stake']
        else:
            pl = -bet['stake']
            
        running_pl += pl
        cumulative_pl.append(running_pl)

    fig.add_trace(go.Scatter(
        x=[bet['placed_at'] for bet in bets],
        y=cumulative_pl,
        mode='lines+markers',
        name='Cumulative P/L'
    ))

    fig.update_layout(
        title="Performance Over Time",
        xaxis_title="Date",
        yaxis_title="Profit/Loss ($)"
    )

    return fig

if __name__ == "__main__":
    st.set_page_config(
        page_title="Betting Dashboard",
        page_icon="🎲",
        layout="wide"
    )
    render_betting_page()
```

Would you like me to continue with:
1. Account management page
2. Visualization utilities
3. Betting strategies implementation
4. Helper functions
5. Additional components

Let me know which part you'd like to see next!