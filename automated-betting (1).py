import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
import streamlit as st
from scipy.optimize import minimize
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class BetType(Enum):
    WIN = "WIN"
    PLACE = "PLACE"
    EACH_WAY = "EACH_WAY"
    EXACTA = "EXACTA"
    TRIFECTA = "TRIFECTA"
    QUINELLA = "QUINELLA"

@dataclass
class BettingStrategy:
    name: str
    description: str
    min_odds: float
    max_odds: float
    confidence_threshold: float
    max_exposure: float
    stop_loss: float
    position_sizing: str
    filters: Dict

@dataclass
class Bet:
    runner_id: str
    runner_name: str
    race_id: str
    bet_type: BetType
    odds: float
    stake: float
    confidence: float
    expected_value: float
    timestamp: datetime

class AutomatedBetting:
    def __init__(self, bank: float = 1000.0):
        self.bank = bank
        self.initial_bank = bank
        self.bets: List[Bet] = []
        self.active_strategies: Dict[str, BettingStrategy] = {}
        self.position_sizers = {
            'kelly': self._kelly_criterion,
            'fixed': self._fixed_fraction,
            'proportional': self._proportional_sizing,
            'dynamic': self._dynamic_sizing
        }

    def add_strategy(self, strategy: BettingStrategy):
        """Add a betting strategy to the system"""
        self.active_strategies[strategy.name] = strategy

    def analyze_betting_opportunity(
        self,
        runner_data: Dict,
        race_data: Dict,
        strategy_name: str
    ) -> Optional[Bet]:
        """Analyze potential betting opportunity"""
        strategy = self.active_strategies.get(strategy_name)
        if not strategy:
            return None

        # Apply strategy filters
        if not self._apply_filters(runner_data, race_data, strategy.filters):
            return None

        # Calculate true probability and confidence
        true_prob, confidence = self._calculate_probabilities(runner_data, race_data)

        # Check confidence threshold
        if confidence < strategy.confidence_threshold:
            return None

        # Get current odds
        odds = runner_data.get('fixedOdds', {}).get('returnWin', 0)
        if not odds or odds < strategy.min_odds or odds > strategy.max_odds:
            return None

        # Calculate expected value
        ev = self._calculate_expected_value(true_prob, odds)
        if ev <= 0:
            return None

        # Calculate optimal stake
        stake = self._calculate_stake(
            true_prob,
            odds,
            confidence,
            strategy.position_sizing
        )

        # Create bet
        return Bet(
            runner_id=runner_data['runnerId'],
            runner_name=runner_data['runnerName'],
            race_id=race_data['raceId'],
            bet_type=BetType.WIN,
            odds=odds,
            stake=stake,
            confidence=confidence,
            expected_value=ev,
            timestamp=datetime.now()
        )

    def _apply_filters(
        self,
        runner_data: Dict,
        race_data: Dict,
        filters: Dict
    ) -> bool:
        """Apply strategy filters"""
        for filter_name, filter_value in filters.items():
            if filter_name == 'min_rank' and runner_data.get('rank', 999) > filter_value:
                return False
            elif filter_name == 'max_runners' and len(race_data.get('runners', [])) > filter_value:
                return False
            elif filter_name == 'track_condition' and race_data.get('trackCondition') not in filter_value:
                return False
            elif filter_name == 'race_type' and race_data.get('raceType') not in filter_value:
                return False
        return True

    def _calculate_probabilities(
        self,
        runner_data: Dict,
        race_data: Dict
    ) -> Tuple[float, float]:
        """Calculate true probability and confidence level"""
        # Calculate base probability
        base_prob = self._calculate_base_probability(runner_data)
        
        # Adjust for race conditions
        adjusted_prob = self._adjust_probability(base_prob, runner_data, race_data)
        
        # Calculate confidence
        confidence = self._calculate_confidence(runner_data, race_data)
        
        return adjusted_prob, confidence

    def _calculate_base_probability(self, runner_data: Dict) -> float:
        """Calculate base probability from historical data"""
        if 'formComments' not in runner_data:
            return 0.0

        recent_form = runner_data['formComments'][-5:]
        if not recent_form:
            return 0.0

        # Calculate win rate
        wins = sum(1 for race in recent_form if race.get('position', 0) == 1)
        win_rate = wins / len(recent_form)

        # Adjust for class
        class_adjustment = self._get_class_adjustment(runner_data)
        
        return min(0.95, max(0.01, win_rate * class_adjustment))

    def _calculate_stake(
        self,
        probability: float,
        odds: float,
        confidence: float,
        sizing_method: str
    ) -> float:
        """Calculate optimal stake size"""
        sizer = self.position_sizers.get(sizing_method, self._fixed_fraction)
        base_stake = sizer(probability, odds)
        
        # Adjust for confidence
        adjusted_stake = base_stake * confidence
        
        # Apply risk management
        max_stake = self.bank * 0.1  # Maximum 10% of bank per bet
        return min(adjusted_stake, max_stake)

    def _kelly_criterion(self, probability: float, odds: float) -> float:
        """Calculate Kelly Criterion stake"""
        q = 1 - probability
        p = probability
        b = odds - 1
        
        if p * b > q:
            stake = ((p * b - q) / b) * self.bank
            return min(stake, self.bank * 0.05)  # Maximum 5% Kelly
        return 0

    def _fixed_fraction(self, probability: float, odds: float) -> float:
        """Fixed fraction betting"""
        return self.bank * 0.02  # 2% of bank

    def _proportional_sizing(self, probability: float, odds: float) -> float:
        """Proportional to probability and odds"""
        return self.bank * 0.02 * probability * (odds / 10)

    def _dynamic_sizing(self, probability: float, odds: float) -> float:
        """Dynamic position sizing based on edge"""
        edge = (probability * odds) - 1
        if edge <= 0:
            return 0
        return self.bank * 0.02 * edge

    def optimize_portfolio(self, opportunities: List[Bet]) -> List[Bet]:
        """Optimize bet portfolio using Mean-Variance Optimization"""
        if not opportunities:
            return []

        # Create returns matrix
        returns = np.array([bet.expected_value for bet in opportunities])
        
        # Create covariance matrix (simplified)
        n_bets = len(opportunities)
        covariance = np.eye(n_bets) * 0.1  # Assuming low correlation
        
        # Define optimization constraints
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Weights sum to 1
            {'type': 'ineq', 'fun': lambda x: x}  # Non-negative weights
        ]
        
        # Optimize
        result = minimize(
            lambda w: -np.dot(w, returns) + 0.5 * np.dot(w, np.dot(covariance, w)),
            x0=np.ones(n_bets) / n_bets,
            constraints=constraints
        )
        
        # Apply optimal weights
        if result.success:
            for bet, weight in zip(opportunities, result.x):
                bet.stake *= weight
                
        return opportunities

    def render_betting_dashboard(self):
        """Render betting strategy dashboard"""
        st.subheader("Automated Betting Dashboard")
        
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_performance_metrics()
        
        with col2:
            self._render_strategy_selector()
        
        tabs = st.tabs([
            "Active Bets",
            "Bet History",
            "Strategy Performance",
            "Risk Management"
        ])
        
        with tabs[0]:
            self._render_active_bets()
        
        with tabs[1]:
            self._render_bet_history()
            
        with tabs[2]:
            self._render_strategy_performance()
            
        with tabs[3]:
            self._render_risk_management()

    def _render_performance_metrics(self):
        """Render performance metrics"""
        roi = ((self.bank - self.initial_bank) / self.initial_bank) * 100
        
        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
        
        with metrics_col1:
            st.metric(
                "Current Bank",
                f"${self.bank:,.2f}",
                f"{roi:+.1f}%"
            )
        
        with metrics_col2:
            win_rate = self._calculate_win_rate()
            st.metric("Win Rate", f"{win_rate:.1f}%")
        
        with metrics_col3:
            avg_roi = self._calculate_average_roi()
            st.metric("Average ROI", f"{avg_roi:.1f}%")

    def _render_strategy_selector(self):
        """Render strategy selection interface"""
        st.subheader("Strategy Management")
        
        # Strategy selector
        selected_strategy = st.selectbox(
            "Select Strategy",
            options=list(self.active_strategies.keys())
        )
        
        if selected_strategy:
            strategy = self.active_strategies[selected_strategy]
            
            with st.expander("Strategy Settings"):
                # Strategy parameters
                col1, col2 = st.columns(2)
                
                with col1:
                    min_odds = st.number_input(
                        "Minimum Odds",
                        value=float(strategy.min_odds),
                        min_value=1.0
                    )
                    confidence_threshold = st.number_input(
                        "Confidence Threshold",
                        value=float(strategy.confidence_threshold),
                        min_value=0.0,
                        max_value=1.0
                    )
                
                with col2:
                    max_odds = st.number_input(
                        "Maximum Odds",
                        value=float(strategy.max_odds),
                        min_value=1.0
                    )
                    position_sizing = st.selectbox(
                        "Position Sizing",
                        options=list(self.position_sizers.keys())
                    )
                
                # Save changes
                if st.button("Update Strategy"):
                    self.active_strategies[selected_strategy] = BettingStrategy(
                        name=selected_strategy,
                        description=strategy.description,
                        min_odds=min_odds,
                        max_odds=max_odds,
                        confidence_threshold=confidence_threshold,
                        max_exposure=strategy.max_exposure,
                        stop_loss=strategy.stop_loss,
                        position_sizing=position_sizing,
                        filters=strategy.filters
                    )
                    st.success("Strategy updated successfully!")

    def _render_active_bets(self):
        """Render active bets interface"""
        active_bets = [bet for bet in self.bets if not hasattr(bet, 'result')]
        
        if not active_bets:
            st.write("No active bets")
            return
        
        # Create DataFrame
        df = pd.DataFrame([
            {
                'Runner': bet.runner_name,
                'Odds': bet.odds,
                'Stake': bet.stake,
                'Potential Return': bet.stake * bet.odds,
                'Confidence': bet.confidence,
                'EV': bet.expected_value
            }
            for bet in active_bets
        ])
        
        st.dataframe(df)
        
        # Portfolio analytics
        self._render_portfolio_analytics(active_bets)

    def _render_portfolio_analytics(self, active_bets: List[Bet]):
        """Render portfolio analytics"""
        total_exposure = sum(bet.stake for bet in active_bets)
        potential_return = sum(bet.stake * bet.odds for bet in active_bets)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Exposure", f"${total_exposure:,.2f}")
        
        with col2:
            st.metric(
                "Potential Return",
                f"${potential_return:,.2f}",
                f"{((potential_return/total_exposure)-1)*100:.1f}%"
            )
        
        with col3:
            st.metric(
                "Risk Level",
                "Moderate" if total_exposure < self.bank * 0.3 else "High"
            )
        
        # Risk distribution chart
        exposure_data = pd.DataFrame([
            {
                'Runner': bet.runner_name,
                'Exposure': bet.stake,
                'Risk Score': bet.stake * bet.odds / bet.confidence
            }
            for bet in active_bets
        ])
        
        fig = px.scatter(
            exposure_data,
            x='Exposure',
            y='Risk Score',
            size='Exposure',
            text='Runner',
            title='Risk Distribution'
        )
        
        st.plotly_chart(fig)

    def _render_bet_history(self):
        """Render betting history analysis"""
        completed_bets = [bet for bet in self.bets if hasattr(bet, 'result')]
        
        if not completed_bets:
            st.write("No completed bets")
            return
        
        # Create DataFrame
        df = pd.DataFrame([
            {
                'Date': bet.timestamp,
                'Runner': bet.runner_name,
                'Odds': bet.odds,
                'Stake': bet.stake,
                'Result': bet.result,
                'Return': bet.stake * bet.odds if bet.result == 'Won' else 0,
                'ROI': ((bet.stake * bet.odds)/bet.stake - 1) * 100 if bet.result == 'Won' else -100
            }
            for bet in completed_bets
        ])
        
        # Performance chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['ROI'].cumsum(),
            mode='lines',
            name='Cumulative ROI'
        ))
        
        st.plotly_chart(fig)
        
        # Performance metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            win_rate = len(df[df['Result'] == 'Won']) / len(df) * 100
            st.metric("Win Rate", f"{win_rate:.1f}%")
        
        with col2