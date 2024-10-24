import streamlit as st
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import plotly.graph_objects as go
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BettingStrategy:
    name: str
    description: str
    min_odds: float
    max_odds: float
    stake_percentage: float
    min_probability: float
    max_exposure: float
    required_edge: float

class AutomatedBettingSystem:
    def __init__(self, initial_bank: float):
        self.initial_bank = initial_bank
        self.current_bank = initial_bank
        self.active_bets: List[Dict] = []
        self.bet_history: List[Dict] = []
        self.strategies = self._initialize_strategies()
        self.risk_limits = {
            'max_bet_size': 0.1,  # 10% of bank
            'max_daily_loss': 0.2,  # 20% of bank
            'max_exposure': 0.3,  # 30% of bank
            'min_bank': 0.5  # 50% of initial bank
        }

    def _initialize_strategies(self) -> Dict[str, BettingStrategy]:
        """Initialize betting strategies"""
        return {
            'value': BettingStrategy(
                name='Value Betting',
                description='Bet when true probability exceeds market probability',
                min_odds=1.5,
                max_odds=10.0,
                stake_percentage=0.02,
                min_probability=0.15,
                max_exposure=0.1,
                required_edge=0.05
            ),
            'kelly': BettingStrategy(
                name='Kelly Criterion',
                description='Optimal stake sizing based on edge',
                min_odds=1.3,
                max_odds=15.0,
                stake_percentage=0.05,
                min_probability=0.1,
                max_exposure=0.15,
                required_edge=0.03
            ),
            'dutching': BettingStrategy(
                name='Dutching',
                description='Split stakes across multiple selections',
                min_odds=2.0,
                max_odds=20.0,
                stake_percentage=0.03,
                min_probability=0.08,
                max_exposure=0.12,
                required_edge=0.04
            )
        }

    def calculate_kelly_stake(
        self,
        true_probability: float,
        odds: float,
        bank: float
    ) -> float:
        """Calculate optimal stake using Kelly Criterion"""
        if true_probability <= 0 or odds <= 1:
            return 0
            
        q = 1 - true_probability
        p = true_probability
        b = odds - 1
        
        if p * b <= q:
            return 0
            
        f = (p * b - q) / b
        stake = f * bank
        
        # Apply safety factor of 0.5
        return min(stake * 0.5, bank * self.risk_limits['max_bet_size'])

    def evaluate_bet_opportunity(
        self,
        runner_data: Dict,
        strategy: str
    ) -> Tuple[bool, float, str]:
        """Evaluate betting opportunity using selected strategy"""
        if strategy not in self.strategies:
            return False, 0, "Invalid strategy"
            
        strategy_config = self.strategies[strategy]
        
        # Get odds and calculated probability
        odds = runner_data.get('fixed_odds', {}).get('win', 0)
        true_prob = self._calculate_true_probability(runner_data)
        
        if not odds or not true_prob:
            return False, 0, "Missing odds or probability"
            
        # Check odds range
        if not (strategy_config.min_odds <= odds <= strategy_config.max_odds):
            return False, 0, "Odds outside acceptable range"
            
        # Check probability threshold
        if true_prob < strategy_config.min_probability:
            return False, 0, "Probability below threshold"
            
        # Calculate edge
        market_prob = 1 / odds
        edge = true_prob - market_prob
        
        if edge < strategy_config.required_edge:
            return False, 0, "Insufficient edge"
            
        # Calculate stake
        if strategy == 'kelly':
            stake = self.calculate_kelly_stake(true_prob, odds, self.current_bank)
        else:
            stake = self.current_bank * strategy_config.stake_percentage
            
        # Apply risk limits
        stake = min(
            stake,
            self.current_bank * self.risk_limits['max_bet_size'],
            self.current_bank - self._get_current_exposure()
        )
        
        return True, stake, f"Edge: {edge:.2%}"

    def place_bet(
        self,
        runner_data: Dict,
        strategy: str,
        stake: float
    ) -> bool:
        """Place bet with risk management checks"""
        try:
            # Perform risk checks
            if not self._validate_risk_limits(stake):
                logger.warning("Risk limits exceeded")
                return False
                
            # Create bet record
            bet = {
                'timestamp': datetime.now(),
                'runner_number': runner_data['runner_number'],
                'runner_name': runner_data['runner_name'],
                'race_number': runner_data['race_number'],
                'venue': runner_data['venue'],
                'odds': runner_data['fixed_odds']['win'],
                'stake': stake,
                'strategy': strategy,
                'status': 'PENDING'
            }
            
            # Add to active bets
            self.active_bets.append(bet)
            self.current_bank -= stake
            
            logger.info(f"Placed bet: {bet['runner_name']} - ${stake:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Error placing bet: {str(e)}")
            return False

    def _validate_risk_limits(self, stake: float) -> bool:
        """Validate bet against risk management rules"""
        # Check minimum bank level
        if self.current_bank < self.initial_bank * self.risk_limits['min_bank']:
            return False
            
        # Check maximum bet size
        if stake > self.current_bank * self.risk_limits['max_bet_size']:
            return False
            
        # Check daily loss limit
        daily_loss = sum(
            bet['stake']
            for bet in self.bet_history
            if bet['timestamp'].date() == datetime.now().date()
            and bet['status'] == 'LOST'
        )
        if daily_loss + stake > self.initial_bank * self.risk_limits['max_daily_loss']:
            return False
            
        # Check total exposure
        current_exposure = self._get_current_exposure()
        if current_exposure + stake > self.current_bank * self.risk_limits['max_exposure']:
            return False
            
        return True

    def _get_current_exposure(self) -> float:
        """Calculate current betting exposure"""
        return sum(bet['stake'] for bet in self.active_bets)

    def _calculate_true_probability(self, runner_data: Dict) -> float:
        """Calculate true winning probability using available metrics"""
        if not runner_data.get('form'):
            return 0
            
        # Calculate base rating from recent form
        recent_results = runner_data['form'].get('last_starts', [])[:5]
        if not recent_results:
            return 0
            
        base_rating = 0
        for result in recent_results:
            position = result.get('position', 0)
            if position == 0:
                continue
                
            # Convert position to rating (1st = 100, 2nd = 90, etc.)
            rating = max(0, 100 - (position - 1) * 10)
            
            # Apply recency bias
            days_ago = (datetime.now() - datetime.strptime(result['date'], '%Y-%m-%d')).days
            recency_factor = max(0.5, 1 - (days_ago / 365))
            base_rating += rating * recency_factor
            
        base_rating /= len(recent_results)
        
        # Adjust for class level
        class_factor = {
            'G1': 1.2,
            'G2': 1.15,
            'G3': 1.1,
            'Listed': 1.05
        }.get(runner_data.get('class', ''), 1.0)
        
        # Adjust for track condition
        track_stats = runner_data['form'].get('track_stats', {})
        condition_wins = track_stats.get('wins', 0)
        condition_starts = track_stats.get('starts', 1)
        track_factor = (condition_wins / condition_starts) * 0.5 + 0.75
        
        # Calculate final probability
        probability = (base_rating * class_factor * track_factor) / 100
        
        # Normalize to [0, 1]
        return min(max(probability, 0), 1)

    def update_bet_status(self, race_results: Dict):
        """Update bet status based on race results"""
        for bet in self.active_bets:
            if bet['race_number'] == race_results['race_number'] and \
               bet['venue'] == race_results['venue']:
                winner = race_results.get('winner')
                if winner:
                    if bet['runner_number'] == winner['runner_number']:
                        bet['status'] = 'WON'
                        bet['return'] = bet['stake'] * bet['odds']
                        self.current_bank += bet['return']
                    else:
                        bet['status'] = 'LOST'
                        bet['return'] = 0
                    
                    # Move to history
                    self.bet_history.append(bet)
                    self.active_bets.remove(bet)

    def get_performance_metrics(self) -> Dict:
        """Calculate performance metrics"""
        if not self.bet_history:
            return {}
            
        total_bets = len(self.bet_history)
        winning_bets = len([b for b in self.bet_history if b['status'] == 'WON'])
        total_stake = sum(b['stake'] for b in self.bet_history)
        total_returns = sum(b['return'] for b in self.bet_history)
        
        return {
            'total_bets': total_bets,
            'win_rate': winning_bets / total_bets if total_bets > 0 else 0,
            'total_stake': total_stake,
            'total_returns': total_returns,
            'profit_loss': total_returns - total_stake,
            'roi': (total_returns - total_stake) / total_stake if total_stake > 0 else 0,
            'current_bank': self.current_bank,
            'bank_growth': (self.current_bank - self.initial_bank) / self.initial_bank
        }

    def render_dashboard(self):
        """Render betting dashboard"""
        st.subheader("Automated Betting Dashboard")
        
        # Performance metrics
        metrics = self.get_performance_metrics()
        if metrics:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Bank Balance", f"${metrics['current_bank']:.2f}",
                         f"{metrics['bank_growth']:.1%}")
            with col2:
                st.metric("Win Rate", f"{metrics['win_rate']:.1%}")
            with col3:
                st.metric("Total P/L", f"${metrics['profit_loss']:.2f}")
            with col4:
                st.metric("ROI", f"{metrics['roi']:.1%}")
            
            # Performance chart
            self._render_performance_chart()
            
            # Active bets
            st.subheader("Active Bets")
            if self.active_bets:
                df = pd.DataFrame(self.active_bets)
                st.dataframe(df)
            else:
                st.write("No active bets")
            
            # Bet history
            st.subheader("Recent Bet History")
            if self.bet_history:
                df = pd.DataFrame(self.bet_history[-10:])  # Show last 10 bets
                st.dataframe(df)

    def _render_performance_chart(self):
        """Render performance charts"""
        if not self.bet_history:
            return
            
        # Create daily P/L chart
        df = pd.DataFrame(self.bet_history)
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        daily_pl = df.groupby('date').agg({
            'stake': 'sum',
            'return': 'sum'
        }).reset_index()
        daily_pl['profit'] = daily_pl['return'] - daily_pl['stake']
        daily_pl['cumulative_profit'] = daily_pl['profit'].cumsum()
        
        fig = go.Figure()
        
        # Daily P/L bars
        fig.add_trace(go.Bar(
            x=daily_pl['date'],
            y=daily_pl['profit'],
            name='Daily P/L'
        ))
        
        # Cumulative P/L line
        fig.add_trace(go.Scatter(
            x=daily_pl['date'],
            y=daily_pl['cumulative_profit'],
            name='Cumulative P/L',
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='Betting Performance',
            yaxis=dict(title='Daily P/L ($)'),
            yaxis2=dict(title='Cumulative P/L ($)', overlaying='y', side='right'),
            height=400
        )
        
        st.plotly_chart(fig)
