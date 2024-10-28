    def _render_bet_history(self):
        """Render betting history analysis continued"""
        completed_bets = [bet for bet in self.bets if hasattr(bet, 'result')]
        df = pd.DataFrame([
            {
                'Date': bet.timestamp,
                'Runner': bet.runner_name,
                'Odds': bet.odds,
                'Stake': bet.stake,
                'Result': bet.result,
                'Return': bet.stake * bet.odds if bet.result == 'Won' else 0,
                'ROI': ((bet.stake * bet.odds)/bet.stake - 1) * 100 if bet.result == 'Won' else -100,
                'Strategy': bet.strategy_name
            }
            for bet in completed_bets
        ])
        
        with col2:
            total_roi = df['ROI'].mean()
            st.metric("Average ROI", f"{total_roi:.1f}%")
        
        with col3:
            profit = df['Return'].sum() - df['Stake'].sum()
            st.metric("Total Profit", f"${profit:,.2f}")
        
        # Strategy performance breakdown
        st.subheader("Strategy Performance")
        
        strategy_metrics = df.groupby('Strategy').agg({
            'Stake': 'sum',
            'Return': 'sum',
            'ROI': 'mean',
            'Result': lambda x: (x == 'Won').mean() * 100
        }).round(2)
        
        strategy_metrics.columns = ['Total Stake', 'Total Return', 'Avg ROI%', 'Win Rate%']
        st.dataframe(strategy_metrics)
        
        # Performance visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            # ROI distribution
            fig = px.histogram(
                df,
                x='ROI',
                nbins=20,
                title='ROI Distribution'
            )
            st.plotly_chart(fig)
        
        with col2:
            # Odds vs ROI scatter
            fig = px.scatter(
                df,
                x='Odds',
                y='ROI',
                color='Result',
                title='Odds vs ROI Analysis'
            )
            st.plotly_chart(fig)

    def _render_risk_management(self):
        """Render risk management dashboard"""
        st.subheader("Risk Management")
        
        # Bank management
        col1, col2 = st.columns(2)
        
        with col1:
            # Bank growth chart
            bank_history = self._calculate_bank_history()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=bank_history['Date'],
                y=bank_history['Balance'],
                mode='lines',
                name='Bank Balance'
            ))
            
            # Add drawdown overlay
            drawdown = self._calculate_drawdown(bank_history['Balance'])
            fig.add_trace(go.Scatter(
                x=bank_history['Date'],
                y=drawdown,
                mode='lines',
                name='Drawdown',
                line=dict(dash='dash')
            ))
            
            fig.update_layout(title='Bank Growth & Drawdown')
            st.plotly_chart(fig)
        
        with col2:
            # Risk metrics
            metrics = self._calculate_risk_metrics()
            
            st.metric("Max Drawdown", f"{metrics['max_drawdown']:.1f}%")
            st.metric("Sharpe Ratio", f"{metrics['sharpe_ratio']:.2f}")
            st.metric("Risk-Adjusted ROI", f"{metrics['risk_adjusted_roi']:.1f}%")
            
            # Risk settings
            st.subheader("Risk Settings")
            
            max_exposure = st.slider(
                "Maximum Exposure (%)",
                min_value=1,
                max_value=50,
                value=20
            )
            
            stop_loss = st.slider(
                "Stop Loss (%)",
                min_value=1,
                max_value=50,
                value=25
            )
            
            if st.button("Update Risk Settings"):
                self._update_risk_settings(max_exposure, stop_loss)
                st.success("Risk settings updated!")

    def _calculate_risk_metrics(self) -> Dict:
        """Calculate comprehensive risk metrics"""
        completed_bets = [bet for bet in self.bets if hasattr(bet, 'result')]
        if not completed_bets:
            return {
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'risk_adjusted_roi': 0
            }
        
        # Calculate returns
        returns = [
            (bet.stake * bet.odds - bet.stake) / bet.stake 
            if bet.result == 'Won' else -1
            for bet in completed_bets
        ]
        
        # Calculate metrics
        return {
            'max_drawdown': self._calculate_max_drawdown(returns),
            'sharpe_ratio': self._calculate_sharpe_ratio(returns),
            'risk_adjusted_roi': self._calculate_risk_adjusted_roi(returns)
        }

    def _calculate_max_drawdown(self, returns: List[float]) -> float:
        """Calculate maximum drawdown percentage"""
        cumulative = np.cumprod(np.array(returns) + 1)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (running_max - cumulative) / running_max
        return float(np.max(drawdown) * 100)

    def _calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio"""
        if not returns:
            return 0
        return np.mean(returns) / (np.std(returns) + 1e-6)

    def _calculate_risk_adjusted_roi(self, returns: List[float]) -> float:
        """Calculate risk-adjusted ROI"""
        if not returns:
            return 0
        roi = (np.prod(np.array(returns) + 1) - 1) * 100
        vol = np.std(returns) * 100
        return roi / (vol + 1e-6)

    def implement_betting_strategies(self):
        """Implement automated betting strategies"""
        # Value betting strategy
        self.add_strategy(BettingStrategy(
            name="Value Betting",
            description="Bet when true probability exceeds implied odds probability",
            min_odds=2.0,
            max_odds=10.0,
            confidence_threshold=0.6,
            max_exposure=0.1,
            stop_loss=0.25,
            position_sizing='kelly',
            filters={
                'min_rank': 5,
                'max_runners': 12,
                'track_condition': ['Good', 'Soft']
            }
        ))
        
        # Dutching strategy
        self.add_strategy(BettingStrategy(
            name="Dutching",
            description="Spread bets across multiple runners for guaranteed return",
            min_odds=1.5,
            max_odds=5.0,
            confidence_threshold=0.7,
            max_exposure=0.15,
            stop_loss=0.2,
            position_sizing='proportional',
            filters={
                'min_rank': 3,
                'max_runners': 8,
                'track_condition': ['Good']
            }
        ))
        
        # Each-way value strategy
        self.add_strategy(BettingStrategy(
            name="Each-Way Value",
            description="Place each-way bets on value opportunities",
            min_odds=4.0,
            max_odds=20.0,
            confidence_threshold=0.5,
            max_exposure=0.05,
            stop_loss=0.3,
            position_sizing='fixed',
            filters={
                'min_rank': 4,
                'max_runners': 16,
                'track_condition': ['Good', 'Soft', 'Heavy']
            }
        ))

    def auto_bet(self, race_data: Dict):
        """Automated betting based on active strategies"""
        opportunities = []
        
        for strategy_name, strategy in self.active_strategies.items():
            # Check risk limits
            if self._check_risk_limits(strategy):
                continue
                
            for runner in race_data['runners']:
                bet = self.analyze_betting_opportunity(
                    runner,
                    race_data,
                    strategy_name
                )
                
                if bet:
                    opportunities.append(bet)
        
        if opportunities:
            # Optimize portfolio
            optimized_bets = self.optimize_portfolio(opportunities)
            
            # Place bets
            for bet in optimized_bets:
                if self._validate_bet(bet):
                    self.place_bet(bet)

    def _check_risk_limits(self, strategy: BettingStrategy) -> bool:
        """Check if strategy has exceeded risk limits"""
        # Calculate strategy exposure
        active_bets = [
            bet for bet in self.bets
            if not hasattr(bet, 'result') and bet.strategy_name == strategy.name
        ]
        
        exposure = sum(bet.stake for bet in active_bets)
        exposure_pct = exposure / self.bank
        
        # Check maximum exposure
        if exposure_pct >= strategy.max_exposure:
            return True
        
        # Check stop loss
        strategy_bets = [
            bet for bet in self.bets
            if hasattr(bet, 'result') and bet.strategy_name == strategy.name
        ]
        
        if strategy_bets:
            roi = self._calculate_strategy_roi(strategy_bets)
            if roi <= -strategy.stop_loss:
                return True
        
        return False

    def _validate_bet(self, bet: Bet) -> bool:
        """Validate bet before placement"""
        # Check bank
        if bet.stake > self.bank:
            return False
        
        # Check exposure limits
        total_exposure = sum(
            b.stake for b in self.bets
            if not hasattr(b, 'result')
        )
        if (total_exposure + bet.stake) / self.bank > 0.5:  # Max 50% total exposure
            return False
        
        # Check odds movement
        if self._check_odds_movement(bet):
            return False
        
        return True

    def place_bet(self, bet: Bet):
        """Place validated bet"""
        self.bets.append(bet)
        self.bank -= bet.stake
        logger.info(f"Placed {bet.bet_type.value} bet on {bet.runner_name}")

def main():
    st.title("Automated Betting System")
    
    # Initialize betting system
    betting_system = AutomatedBetting()
    betting_system.implement_betting_strategies()
    
    # Main interface
    betting_system.render_betting_dashboard()
    
    # Auto-betting controls
    st.sidebar.subheader("Auto-Betting Controls")
    
    if st.sidebar.button("Start Auto-Betting"):
        st.sidebar.success("Auto-betting activated!")
        
        # In production, this would connect to live race data
        # For demo, we'll use sample data
        race_data = {
            'raceId': '123',
            'runners': [
                {
                    'runnerId': '1',
                    'runnerName': 'Sample Runner',
                    'fixedOdds': {'returnWin': 4.5},
                    'rank': 2
                }
                # Add more runners
            ],
            'trackCondition': 'Good',
            'raceType': 'Thoroughbred'
        }
        
        betting_system.auto_bet(race_data)

if __name__ == "__main__":
    main()