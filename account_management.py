import streamlit as st
import logging
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional, Union
import plotly.graph_objects as go
import plotly.express as px
from dataclasses import dataclass
import uuid
import json
from decimal import Decimal
import utils.logger as logger

@dataclass
class Transaction:
    """Represents a financial transaction"""
    id: str
    timestamp: datetime
    type: str  # 'deposit', 'withdrawal', 'bet_place', 'bet_win', 'bet_loss'
    amount: Decimal
    description: str
    balance_after: Decimal
    metadata: Dict

@dataclass
class Bet:
    """Represents a betting transaction"""
    id: str
    timestamp: datetime
    track: str
    race: str
    horse: str
    amount: Decimal
    odds: float
    bet_type: str
    status: str  # 'pending', 'won', 'lost', 'void'
    potential_return: Decimal
    actual_return: Optional[Decimal]
    metadata: Dict

class AccountManager:
    """Enhanced account management with advanced features"""
    
    def __init__(self):
        self.logger = logger.get_logger(__name__)
        self.initialize_session_state()

    def initialize_session_state(self):
        """Initialize account-related session state variables"""
        if 'account_balance' not in st.session_state:
            st.session_state.account_balance = Decimal('1000.00')
        if 'pending_bets' not in st.session_state:
            st.session_state.pending_bets = []
        if 'betting_history' not in st.session_state:
            st.session_state.betting_history = []
        if 'transactions' not in st.session_state:
            st.session_state.transactions = []
        if 'daily_pl' not in st.session_state:
            st.session_state.daily_pl = Decimal('0.00')
        if 'account_settings' not in st.session_state:
            st.session_state.account_settings = self._get_default_settings()

    def _get_default_settings(self) -> Dict:
        """Get default account settings"""
        return {
            'default_bet_amount': Decimal('50.00'),
            'max_bet_amount': Decimal('500.00'),
            'daily_loss_limit': Decimal('1000.00'),
            'email_notifications': True,
            'sms_notifications': False,
            'auto_cash_out': False,
            'cash_out_threshold': Decimal('200.00'),
            'timezone': 'UTC',
            'currency': 'AUD',
            'risk_level': 'medium'
        }

    def login(self, username: str, password: str) -> bool:
        """Authenticate user with enhanced security"""
        try:
            # For demo purposes, accept demo/demo
            if username == "demo" and password == "demo":
                self.logger.info(f"Successful login attempt for user: {username}")
                self._record_login_attempt(username, True)
                return True
            
            self.logger.warning(f"Failed login attempt for user: {username}")
            self._record_login_attempt(username, False)
            return False
            
        except Exception as e:
            self.logger.error(f"Login error: {str(e)}")
            return False

    def _record_login_attempt(self, username: str, success: bool):
        """Record login attempt for security monitoring"""
        try:
            timestamp = datetime.now()
            attempt = {
                'timestamp': timestamp,
                'username': username,
                'success': success,
                'ip_address': 'demo_ip',  # In real app, get actual IP
                'user_agent': 'demo_agent'  # In real app, get actual user agent
            }
            
            if 'login_attempts' not in st.session_state:
                st.session_state.login_attempts = []
            st.session_state.login_attempts.append(attempt)
            
        except Exception as e:
            self.logger.error(f"Error recording login attempt: {str(e)}")

    def get_balance(self) -> Decimal:
        """Get current account balance"""
        return st.session_state.account_balance

    def get_daily_pl(self) -> Decimal:
        """Get daily profit/loss"""
        return st.session_state.daily_pl

    def get_pending_bets(self) -> List[Bet]:
        """Get list of pending bets"""
        return st.session_state.pending_bets

    def get_betting_history(self) -> List[Bet]:
        """Get betting history"""
        return st.session_state.betting_history

    def place_bet(self, bet_details: Dict) -> bool:
        """Place a new bet with enhanced validation"""
        try:
            # Validate bet amount
            amount = Decimal(str(bet_details['stake']))
            if amount <= Decimal('0'):
                raise ValueError("Bet amount must be positive")
            
            if amount > st.session_state.account_settings['max_bet_amount']:
                raise ValueError(f"Bet exceeds maximum amount of ${st.session_state.account_settings['max_bet_amount']}")
            
            # Check daily loss limit
            daily_losses = self._calculate_daily_losses()
            if daily_losses + amount > st.session_state.account_settings['daily_loss_limit']:
                raise ValueError("Bet would exceed daily loss limit")
            
            # Check available balance
            if amount > st.session_state.account_balance:
                raise ValueError("Insufficient funds")
            
            # Create bet object
            bet = Bet(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                track=bet_details['track'],
                race=bet_details['race'],
                horse=bet_details['horse'],
                amount=amount,
                odds=float(bet_details['odds']),
                bet_type=bet_details['type'],
                status='pending',
                potential_return=amount * Decimal(str(bet_details['odds'])),
                actual_return=None,
                metadata=bet_details.get('metadata', {})
            )
            
            # Record transaction
            self._record_transaction(
                type='bet_place',
                amount=amount,
                description=f"Bet placed on {bet.horse} in {bet.race} at {bet.track}",
                metadata={'bet_id': bet.id}
            )
            
            # Update account state
            st.session_state.account_balance -= amount
            st.session_state.pending_bets.append(bet)
            
            self.logger.info(f"Bet placed successfully: {bet.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error placing bet: {str(e)}")
            return False

    def settle_bet(self, bet_id: str, result: str, return_amount: Optional[float] = None):
        """Settle a pending bet with enhanced handling"""
        try:
            for bet in st.session_state.pending_bets:
                if bet.id == bet_id:
                    bet.status = result
                    bet.actual_return = Decimal(str(return_amount)) if return_amount else Decimal('0')
                    
                    # Record transaction
                    if result == 'won':
                        self._record_transaction(
                            type='bet_win',
                            amount=bet.actual_return,
                            description=f"Won bet on {bet.horse} in {bet.race} at {bet.track}",
                            metadata={'bet_id': bet.id}
                        )
                        st.session_state.account_balance += bet.actual_return
                        st.session_state.daily_pl += (bet.actual_return - bet.amount)
                    else:
                        self._record_transaction(
                            type='bet_loss',
                            amount=bet.amount,
                            description=f"Lost bet on {bet.horse} in {bet.race} at {bet.track}",
                            metadata={'bet_id': bet.id}
                        )
                        st.session_state.daily_pl -= bet.amount
                    
                    # Move to history
                    st.session_state.betting_history.append(bet)
                    st.session_state.pending_bets.remove(bet)
                    
                    # Check for auto cash out
                    if st.session_state.account_settings['auto_cash_out']:
                        self._check_auto_cash_out()
                    
                    self.logger.info(f"Bet settled successfully: {bet_id}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Error settling bet: {str(e)}")

    def _record_transaction(
        self,
        type: str,
        amount: Decimal,
        description: str,
        metadata: Dict = None
    ):
        """Record a financial transaction"""
        try:
            transaction = Transaction(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                type=type,
                amount=amount,
                description=description,
                balance_after=st.session_state.account_balance,
                metadata=metadata or {}
            )
            st.session_state.transactions.append(transaction)
            
        except Exception as e:
            self.logger.error(f"Error recording transaction: {str(e)}")

    def _calculate_daily_losses(self) -> Decimal:
        """Calculate total losses for current day"""
        try:
            today = datetime.now().date()
            daily_losses = sum(
                t.amount
                for t in st.session_state.transactions
                if t.timestamp.date() == today
                and t.type == 'bet_loss'
            )
            return daily_losses
            
        except Exception as e:
            self.logger.error(f"Error calculating daily losses: {str(e)}")
            return Decimal('0')

    def _check_auto_cash_out(self):
        """Check and execute auto cash out if conditions are met"""
        try:
            if st.session_state.daily_pl >= st.session_state.account_settings['cash_out_threshold']:
                # Implement auto cash out logic here
                self.logger.info("Auto cash out triggered")
                
        except Exception as e:
            self.logger.error(f"Error checking auto cash out: {str(e)}")

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
                'total_bets': len(self.get_betting_history()),
                'average_bet_size': self._calculate_average_bet_size(),
                'profit_factor': self._calculate_profit_factor(),
                'kelly_criterion': self._calculate_kelly_criterion(),
                'sharpe_ratio': self._calculate_sharpe_ratio()
            }
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {str(e)}")
            return {}

    def get_win_rate(self) -> float:
        """Calculate win rate with enhanced accuracy"""
        try:
            total_bets = len(st.session_state.betting_history)
            if total_bets == 0:
                return 0.0
            
            wins = sum(1 for bet in st.session_state.betting_history 
                      if bet.status == 'won')
            return (wins / total_bets) * 100
            
        except Exception as e:
            self.logger.error(f"Error calculating win rate: {str(e)}")
            return 0.0

    def get_roi(self) -> float:
        """Calculate ROI with enhanced accuracy"""
        try:
            total_stakes = sum(bet.amount for bet in st.session_state.betting_history)
            if total_stakes == 0:
                return 0.0
            
            total_returns = sum(
                bet.actual_return
                for bet in st.session_state.betting_history 
                if bet.status == 'won'
            )
            
            return float((total_returns - total_stakes) / total_stakes * 100)
            
        except Exception as e:
            self.logger.error(f"Error calculating ROI: {str(e)}")
            return 0.0

    def get_daily_turnover(self) -> Decimal:
        """Get daily betting turnover"""
        try:
            today = datetime.now().date()
            daily_bets = [
                bet for bet in st.session_state.betting_history
                if bet.timestamp.date() == today
            ]
            return sum(bet.amount for bet in daily_bets)
            
        except Exception as e:
            self.logger.error(f"Error calculating daily turnover: {str(e)}")
            return Decimal('0')

    def _calculate_average_bet_size(self) -> Decimal:
        """Calculate average bet size"""
        try:
            if not st.session_state.betting_history:
                return Decimal('0')
            
            total_stakes = sum(bet.amount for bet in st.session_state.betting_history)
            return total_stakes / len(st.session_state.betting_history)
            
        except Exception as e:
            self.logger.error(f"Error calculating average bet size: {str(e)}")
            return Decimal('0')

    def _calculate_profit_factor(self) -> float:
        """Calculate profit factor (gross wins / gross losses)"""
        try:
            gross_wins = sum(
                bet.actual_return - bet.amount
                for bet in st.session_state.betting_history
                if bet.status == 'won'
            )
            
            gross_losses = sum(
                bet.amount
                for bet in st.session_state.betting_history
                if bet.status == 'lost'
            )
            
            return float(gross_wins / gross_losses) if gross_losses else 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating profit factor: {str(e)}")
            return 0.0

    def _calculate_kelly_criterion(self) -> float:
        """Calculate Kelly Criterion for optimal bet sizing"""
        try:
            win_probability = self.get_win_rate() / 100
            if win_probability == 0:
                return 0.0
            
            # Calculate average odds
            won_bets = [bet for bet in st.session_state.betting_history if bet.status == 'won']
            if not won_bets:
                return 0.0
            
            avg_odds = sum(bet.odds for bet in won_bets) / len(won_bets)
            
            # Kelly formula: f = (bp - q) / b
            # where: b = odds - 1, p = win probability, q = 1 - p
            b = avg_odds - 1
            q = 1 - win_probability
            kelly = (b * win_probability - q) / b
            
            return max(0.0, min(kelly, 0.25))  # Cap at 25%
            
        except Exception as e:
            self.logger.error(f"Error calculating Kelly Criterion: {str(e)}")
            return 0.0

    def _calculate_sharpe_ratio(self) -> float:
        """Calculate Sharpe Ratio for risk-adjusted returns"""
        try:
            if not st.session_state.betting_history:
                return 0.0
            
            # Calculate daily returns
            daily_returns = []
            current_date = None
            daily_pl = Decimal('0')
            
            for bet in sorted(st.session_state.betting_history, key=lambda x: x.timestamp):
                bet_date = bet.timestamp.date()
                
                if current_date is None:
                    current_date = bet_date
                
                if bet_date != current_date:
                    daily_returns.append(float(daily_pl))
                    daily_pl = Decimal('0')
                    current_date = bet_date
                
                if bet.status == 'won':
                    daily_pl += bet.actual_return - bet.amount
                else:
                    daily_pl -= bet.amount
            
            # Add last day
            if daily_pl != 0:
                daily_returns.append(float(daily_pl))
            
            if not daily_returns:
                return 0.0
            
            # Calculate Sharpe Ratio
            returns_array = np.array(daily_returns)
            avg_return = np.mean(returns_array)
            std_return = np.std(returns_array)
            
            risk_free_rate = 0.02 / 365  # Assuming 2% annual risk-free rate
            
            if std_return == 0:
                return 0.0
            
            sharpe = (avg_return - risk_free_rate) / std_return
            return float(sharpe * np.sqrt(365))  # Annualized
            
        except Exception as e:
            self.logger.error(f"Error calculating Sharpe Ratio: {str(e)}")
            return 0.0

    def get_performance_chart_data(self) -> pd.DataFrame:
        """Get enhanced performance chart data"""
        try:
            # Get last 30 days of data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # Create date range
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Calculate daily P/L and other metrics
            daily_metrics = []
            for date in dates:
                day_bets = [
                    bet for bet in st.session_state.betting_history
                    if bet.timestamp.date() == date.date()
                ]
                
                if day_bets:
                    pl = sum(
                        bet.actual_return - bet.amount if bet.status == 'won'
                        else -bet.amount
                        for bet in day_bets
                    )
                    
                    win_rate = sum(1 for bet in day_bets if bet.status == 'won') / len(day_bets) * 100
                    turnover = sum(bet.amount for bet in day_bets)
                    
                    daily_metrics.append({
                        'Date': date,
                        'P/L': float(pl),
                        'Win Rate': win_rate,
                        'Turnover': float(turnover),
                        'Bets': len(day_bets)
                    })
                else:
                    daily_metrics.append({
                        'Date': date,
                        'P/L': 0.0,
                        'Win Rate': 0.0,
                        'Turnover': 0.0,
                        'Bets': 0
                    })
            
            return pd.DataFrame(daily_metrics)
            
        except Exception as e:
            self.logger.error(f"Error getting performance chart data: {str(e)}")
            return pd.DataFrame()

    def logout(self):
        """Log out current user and clear session state"""
        try:
            session_vars = [
                'logged_in', 'account_balance', 'pending_bets',
                'betting_history', 'transactions', 'daily_pl',
                'account_settings', 'login_attempts'
            ]
            
            for var in session_vars:
                if var in st.session_state:
                    del st.session_state[var]
                    
            st.session_state.logged_in = False
            self.logger.info("User logged out successfully")
            
        except Exception as e:
            self.logger.error(f"Logout error: {str(e)}")

    def update_settings(self, settings: Dict) -> bool:
        """Update account settings"""
        try:
            # Validate settings
            if 'max_bet_amount' in settings:
                settings['max_bet_amount'] = Decimal(str(settings['max_bet_amount']))
                if settings['max_bet_amount'] <= Decimal('0'):
                    raise ValueError("Maximum bet amount must be positive")
            
            if 'daily_loss_limit' in settings:
                settings['daily_loss_limit'] = Decimal(str(settings['daily_loss_limit']))
                if settings['daily_loss_limit'] <= Decimal('0'):
                    raise ValueError("Daily loss limit must be positive")
            
            # Update settings
            st.session_state.account_settings.update(settings)
            self.logger.info("Account settings updated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating settings: {str(e)}")
            return False
