```python
    def run(self):
        """Run the dashboard application continued"""
        # Render navigation
        self.render_navigation()
        
        # Render main content based on selected page
        if st.session_state.page == "Dashboard":
            self.render_main_dashboard()
            
        elif st.session_state.page == "Race Form":
            self.render_race_form_page()
            
        elif st.session_state.page == "Betting":
            self.render_betting_page()
            
        elif st.session_state.page == "Analysis":
            self.render_analysis_page()
            
        elif st.session_state.page == "Portfolio":
            self.render_portfolio_page()
            
        elif st.session_state.page == "Settings":
            self.render_settings_page()
        
        # Always render bet slip and alerts
        self.render_bet_slip()
        self.render_alerts()
        
        # Handle real-time updates
        if st.session_state.auto_refresh:
            self.handle_updates()

    def render_race_form_page(self):
        """Render race form analysis page"""
        st.title("Race Form Analysis")
        
        # Race selection
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_date = st.date_input(
                "Date",
                value=datetime.now().date()
            )
        
        with col2:
            venues = self.tab_client.get_venues(selected_date)
            selected_venue = st.selectbox(
                "Venue",
                options=venues
            )
        
        with col3:
            races = self.tab_client.get_races(selected_date, selected_venue)
            selected_race = st.selectbox(
                "Race",
                options=[f"Race {r['number']}" for r in races]
            )
        
        if all([selected_date, selected_venue, selected_race]):
            race_data = self.tab_client.get_race_details(
                selected_date,
                selected_venue,
                int(selected_race.split()[-1])
            )
            
            # Render race analysis tabs
            tabs = st.tabs([
                "Race Overview",
                "Speed Map",
                "Form Analysis",
                "Track Analysis",
                "Betting Analysis"
            ])
            
            with tabs[0]:
                self.render_race_overview(race_data)
                
            with tabs[1]:
                self.render_speed_map(race_data)
                
            with tabs[2]:
                self.render_form_analysis(race_data)
                
            with tabs[3]:
                self.render_track_analysis(race_data)
                
            with tabs[4]:
                self.render_betting_analysis(race_data)

    def render_race_overview(self, race_data: Dict):
        """Render race overview section"""
        # Race details
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Distance", f"{race_data['distance']}m")
            st.metric("Prize Money", f"${race_data['prizeMoney']:,}")
            
        with col2:
            st.metric("Track", race_data['track']['condition'])
            st.metric("Rail", race_data['track']['railPosition'])
            
        with col3:
            st.metric("Weather", race_data['weather']['condition'])
            st.metric("Temperature", f"{race_data['weather']['temperature']}°C")
        
        # Runners table
        st.subheader("Runners")
        
        runners_df = pd.DataFrame([
            {
                'No.': r['number'],
                'Runner': r['name'],
                'Barrier': r['barrier'],
                'Weight': r['weight'],
                'Jockey': r['jockey'],
                'Trainer': r['trainer'],
                'Odds': r['fixedOdds']['win']
            }
            for r in race_data['runners']
        ])
        
        st.dataframe(
            runners_df.style.background_gradient(
                subset=['Odds'],
                cmap='RdYlGn_r'
            ),
            use_container_width=True
        )

    def render_speed_map(self, race_data: Dict):
        """Render speed map visualization"""
        st.subheader("Speed Map")
        
        # Generate speed map
        speed_map = self.visualizer.create_speed_map(race_data['runners'])
        st.plotly_chart(speed_map, use_container_width=True)
        
        # Pace analysis
        col1, col2 = st.columns(2)
        
        with col1:
            # Early speed
            early_speed = self.historical_analysis.analyze_early_speed(
                race_data['runners']
            )
            
            st.write("**Early Speed Analysis**")
            for position, runners in early_speed.items():
                st.write(f"{position}:")
                for runner in runners:
                    st.write(f"• {runner}")
                    
        with col2:
            # Pace prediction
            pace = self.historical_analysis.predict_pace(race_data)
            
            st.write("**Pace Prediction**")
            st.write(f"Likely Scenario: {pace['scenario']}")
            st.write(f"Pressure: {pace['pressure']}")
            st.write(f"Favored Running Style: {pace['favored_style']}")

    def render_betting_page(self):
        """Render betting management page"""
        st.title("Betting Management")
        
        # Betting dashboard tabs
        tabs = st.tabs([
            "Active Bets",
            "Automated Betting",
            "Betting History",
            "Strategy Performance"
        ])
        
        with tabs[0]:
            self.render_active_bets()
            
        with tabs[1]:
            self.render_automated_betting()
            
        with tabs[2]:
            self.render_betting_history()
            
        with tabs[3]:
            self.render_strategy_performance()

    def render_active_bets(self):
        """Render active bets section"""
        active_bets = self.account_manager.get_active_bets()
        
        if not active_bets:
            st.write("No active bets")
            return
        
        # Active bets table
        st.dataframe(
            pd.DataFrame(active_bets),
            use_container_width=True
        )
        
        # Risk analysis
        col1, col2 = st.columns(2)
        
        with col1:
            # Exposure chart
            exposure_data = pd.DataFrame([
                {
                    'Race': bet['race_name'],
                    'Exposure': bet['stake'],
                    'Potential Return': bet['stake'] * bet['odds']
                }
                for bet in active_bets
            ])
            
            fig = px.bar(
                exposure_data,
                x='Race',
                y=['Exposure', 'Potential Return'],
                title='Race Exposure'
            )
            st.plotly_chart(fig)
            
        with col2:
            # Risk metrics
            total_exposure = exposure_data['Exposure'].sum()
            potential_return = exposure_data['Potential Return'].sum()
            
            st.metric(
                "Total Exposure",
                f"${total_exposure:,.2f}",
                f"{(total_exposure/self.account_manager.get_balance())*100:.1f}% of bank"
            )
            
            st.metric(
                "Potential Return",
                f"${potential_return:,.2f}",
                f"{(potential_return/total_exposure - 1)*100:,.1f}% ROI"
            )

    def render_automated_betting(self):
        """Render automated betting controls"""
        st.subheader("Automated Betting")
        
        # Strategy management
        col1, col2 = st.columns(2)
        
        with col1:
            # Active strategies
            active_strategies = self.betting_system.get_active_strategies()
            
            st.write("**Active Strategies**")
            for strategy in active_strategies:
                with st.expander(strategy['name']):
                    st.write(f"Description: {strategy['description']}")
                    st.write(f"Performance: {strategy['performance']}")
                    
                    if st.button("Disable", key=f"disable_{strategy['name']}"):
                        self.betting_system.disable_strategy(strategy['name'])
                        st.experimental_rerun()
                        
        with col2:
            # Add new strategy
            st.write("**Add Strategy**")
            
            strategy_type = st.selectbox(
                "Strategy Type",
                options=[
                    "Value Betting",
                    "Dutching",
                    "Each Way Value",
                    "ML Predictions"
                ]
            )
            
            if strategy_type:
                self.render_strategy_config(strategy_type)

    def render_analysis_page(self):
        """Render comprehensive analysis page"""
        st.title("Racing Analysis")
        
        # Analysis tools tabs
        tabs = st.tabs([
            "Track Analysis",
            "Runner Analysis",
            "Market Analysis",
            "ML Predictions"
        ])
        
        with tabs[0]:
            self.render_track_analysis_tools()
            
        with tabs[1]:
            self.render_runner_analysis_tools()
            
        with tabs[2]:
            self.render_market_analysis_tools()
            
        with tabs[3]:
            self.render_ml_predictions()

    def render_portfolio_page(self):
        """Render portfolio management page"""
        st.title("Portfolio Management")
        
        # Portfolio overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Portfolio Value",
                f"${self.account_manager.get_portfolio_value():,.2f}",
                f"{self.account_manager.get_portfolio_return():+.1f}%"
            )
            
        with col2:
            st.metric(
                "Active Positions",
                len(self.account_manager.get_active_bets()),
                f"{self.account_manager.get_active_bets_change():+d}"
            )
            
        with col3:
            st.metric(
                "Risk Score",
                f"{self.account_manager.get_risk_score():.1f}/10"
            )
        
        # Portfolio analysis tabs
        tabs = st.tabs([
            "Position Analysis",
            "Risk Management",
            "Performance Analytics",
            "Optimization"
        ])
        
        with tabs[0]:
            self.render_position_analysis()
            
        with tabs[1]:
            self.render_risk_management()
            
        with tabs[2]:
            self.render_performance_analytics()
            
        with tabs[3]:
            self.render_portfolio_optimization()

    def render_settings_page(self):
        """Render settings page"""
        st.title("Settings")
        
        # Settings sections
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Application Settings")
            
            # Theme
            st.session_state.dark_mode = st.toggle(
                "Dark Mode",
                value=st.session_state.dark_mode
            )
            
            # Auto refresh
            st.session_state.auto_refresh = st.toggle(
                "Auto Refresh",
                value=st.session_state.auto_refresh
            )
            
            if st.session_state.auto_refresh:
                st.session_state.refresh_interval = st.slider(
                    "Refresh Interval (seconds)",
                    min_value=10,
                    max_value=60,
                    value=st.session_state.refresh_interval
                )
            
        with col2:
            st.subheader("Notification Settings")
            
            notifications = {
                'price_changes': st.toggle(
                    "Price Changes",
                    value=True
                ),
                'results': st.toggle(
                    "Race Results",
                    value=True
                ),
                'bets': st.toggle(
                    "Bet Status",
                    value=True
                )
            }
            
            if st.button("Save Settings"):
                self.save_settings(notifications)
                st.success("Settings saved successfully!")

    def handle_updates(self):
        """Handle real-time updates"""
        current_time = datetime.now()
        if (current_time - st.session_state.last_update).seconds >= st.session_state.refresh_interval:
            try:
                # Update race data
                if st.session_state.active_race:
                    self.update_race_data()
                
                # Update prices
                self.update_prices()
                
                # Update bet status
                self.update_bet_status()
                
                st.session_state.last_update = current_time
                
            except Exception as e:
                logger.error(f"Update failed: {str(e)}")

def main():
    dashboard = RacingDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()
```
