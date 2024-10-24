```python
class AdvancedStatistics:
    def calculate_track_bias_metrics(self, race_history: List[Dict]) -> Dict:
        """Calculate comprehensive track bias metrics"""
        metrics = {
            'barrier_stats': self._analyze_barrier_performance(race_history),
            'sectional_trends': self._analyze_sectional_trends(race_history),
            'pace_bias': self._analyze_pace_bias(race_history),
            'weight_impact': self._analyze_weight_impact(race_history),
            'track_pattern': self._identify_track_pattern(race_history)
        }
        return metrics

    def _analyze_barrier_performance(self, race_history: List[Dict]) -> Dict:
        """Analyze performance by barrier positions"""
        barrier_data = defaultdict(list)
        
        for race in race_history:
            for runner in race['runners']:
                if 'barrier' in runner and 'position' in runner:
                    barrier_data[runner['barrier']].append(runner['position'])
        
        barrier_stats = {}
        for barrier, positions in barrier_data.items():
            barrier_stats[barrier] = {
                'win_rate': sum(1 for p in positions if p == 1) / len(positions),
                'place_rate': sum(1 for p in positions if p <= 3) / len(positions),
                'avg_position': np.mean(positions),
                'sample_size': len(positions)
            }
        
        return barrier_stats

    def calculate_race_shape_metrics(self, race_data: Dict) -> Dict:
        """Calculate metrics related to race shape and dynamics"""
        metrics = {
            'early_pace': self._analyze_early_pace(race_data),
            'race_shape': self._predict_race_shape(race_data),
            'sectional_predictions': self._predict_sectionals(race_data),
            'position_changes': self._analyze_position_changes(race_data)
        }
        return metrics

    def _analyze_early_pace(self, race_data: Dict) -> Dict:
        """Analyze likely early pace scenario"""
        leaders = 0
        stalkers = 0
        
        for runner in race_data['runners']:
            if 'formComments' in runner:
                early_positions = [
                    run.get('earlyPosition', 0) 
                    for run in runner['formComments'][-3:]
                ]
                avg_early_pos = np.mean(early_positions) if early_positions else 0
                
                if avg_early_pos <= 2:
                    leaders += 1
                elif 2 < avg_early_pos <= 4:
                    stalkers += 1
        
        pace_scenario = (
            'Fast' if leaders >= 3
            else 'Moderate' if leaders == 2 or (leaders == 1 and stalkers >= 2)
            else 'Slow'
        )
        
        return {
            'leaders_count': leaders,
            'stalkers_count': stalkers,
            'pace_scenario': pace_scenario,
            'pressure_rating': self._calculate_pressure_rating(leaders, stalkers)
        }

    def _calculate_pressure_rating(self, leaders: int, stalkers: int) -> float:
        """Calculate early pace pressure rating"""
        base_pressure = leaders * 2 + stalkers
        return min(10, base_pressure) / 10  # Scale from 0 to 1

    def calculate_runner_metrics(self, runner_data: Dict) -> Dict:
        """Calculate comprehensive runner metrics"""
        metrics = {
            'form_cycle': self._analyze_form_cycle(runner_data),
            'class_ratings': self._calculate_class_ratings(runner_data),
            'speed_figures': self._calculate_speed_figures(runner_data),
            'distance_profile': self._analyze_distance_profile(runner_data),
            'track_profile': self._analyze_track_profile(runner_data),
            'jockey_stats': self._analyze_jockey_performance(runner_data)
        }
        return metrics

    def _analyze_form_cycle(self, runner_data: Dict) -> Dict:
        """Analyze runner's form cycle"""
        if 'formComments' not in runner_data:
            return {}
            
        recent_form = runner_data['formComments'][-5:]
        
        positions = [run['position'] for run in recent_form]
        ratings = [self._calculate_run_rating(run) for run in recent_form]
        
        # Calculate trend
        trend = np.polyfit(range(len(ratings)), ratings, 1)[0]
        
        return {
            'current_rating': ratings[-1] if ratings else 0,
            'peak_rating': max(ratings) if ratings else 0,
            'trend': 'Improving' if trend > 0.1 
                    else 'Declining' if trend < -0.1
                    else 'Stable',
            'trend_value': trend,
            'consistency': np.std(ratings) if ratings else 0
        }

    def _calculate_run_rating(self, run: Dict) -> float:
        """Calculate rating for individual run"""
        base_rating = 100 - (run['position'] * 2)
        
        # Adjust for margin
        if 'margin' in run:
            margin_factor = -2 * float(run['margin']) if run['position'] > 1 else 0
            base_rating += margin_factor
        
        # Adjust for class
        class_factors = {
            'G1': 20,
            'G2': 15,
            'G3': 10,
            'Listed': 5
        }
        base_rating += class_factors.get(run.get('raceClass', ''), 0)
        
        # Adjust for weight carried
        if 'weight' in run:
            weight_factor = (run['weight'] - 55) * 0.5
            base_rating -= weight_factor
        
        return max(0, min(120, base_rating))

    def calculate_comparative_metrics(
        self,
        runner_data: Dict,
        field_data: List[Dict]
    ) -> Dict:
        """Calculate metrics comparing runner to field"""
        metrics = {
            'class_edge': self._calculate_class_edge(runner_data, field_data),
            'speed_edge': self._calculate_speed_edge(runner_data, field_data),
            'form_edge': self._calculate_form_edge(runner_data, field_data),
            'track_edge': self._calculate_track_edge(runner_data, field_data),
            'overall_rating': self._calculate_overall_rating(runner_data, field_data)
        }
        return metrics

    def _calculate_class_edge(
        self,
        runner: Dict,
        field: List[Dict]
    ) -> float:
        """Calculate class advantage over field"""
        runner_rating = self._get_class_rating(runner)
        field_ratings = [self._get_class_rating(r) for r in field]
        avg_rating = np.mean(field_ratings)
        
        return (runner_rating - avg_rating) / avg_rating if avg_rating else 0

    def render_statistical_insights(self, race_data: Dict):
        """Render comprehensive statistical insights"""
        st.subheader("Statistical Analysis")
        
        tabs = st.tabs([
            "Race Analysis",
            "Runner Comparisons",
            "Track Bias",
            "Form Cycles",
            "Value Analysis"
        ])
        
        with tabs[0]:
            self._render_race_analysis(race_data)
        
        with tabs[1]:
            self._render_runner_comparisons(race_data)
        
        with tabs[2]:
            self._render_track_bias_analysis(race_data)
            
        with tabs[3]:
            self._render_form_cycles(race_data)
            
        with tabs[4]:
            self._render_value_analysis(race_data)

    def _render_race_analysis(self, race_data: Dict):
        """Render race-level statistical analysis"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Pace Analysis
            st.write("**Pace Analysis**")
            pace_metrics = self._analyze_early_pace(race_data)
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=pace_metrics['pressure_rating'] * 100,
                title={'text': "Pace Pressure"},
                gauge={'axis': {'range': [0, 100]},
                      'bar': {'color': "darkblue"},
                      'steps': [
                          {'range': [0, 33], 'color': "lightgreen"},
                          {'range': [33, 66], 'color': "yellow"},
                          {'range': [66, 100], 'color': "red"}
                      ]}
            ))
            st.plotly_chart(fig)
            
            st.write(f"Pace Scenario: {pace_metrics['pace_scenario']}")
            st.write(f"Leaders: {pace_metrics['leaders_count']}")
            st.write(f"Stalkers: {pace_metrics['stalkers_count']}")
        
        with col2:
            # Class Analysis
            st.write("**Class Analysis**")
            class_distribution = self._analyze_class_distribution(race_data)
            
            fig = px.bar(
                x=list(class_distribution.keys()),
                y=list(class_distribution.values()),
                labels={'x': 'Class Rating', 'y': 'Count'},
                title='Class Distribution'
            )
            st.plotly_chart(fig)

    def _render_runner_comparisons(self, race_data: Dict):
        """Render statistical runner comparisons"""
        # Select runners to compare
        runners = [r['runnerName'] for r in race_data['runners']]
        selected_runners = st.multiselect(
            "Select Runners to Compare",
            runners,
            default=runners[:2] if len(runners) >= 2 else runners
        )
        
        if len(selected_runners) >= 2:
            selected_data = [
                r for r in race_data['runners']
                if r['runnerName'] in selected_runners
            ]
            
            # Calculate comparison metrics
            comparison_data = []
            for runner in selected_data:
                metrics = self.calculate_runner_metrics(runner)
                comparison_data.append({
                    'Runner': runner['runnerName'],
                    **metrics
                })
            
            # Create comparison visualization
            df = pd.DataFrame(comparison_data)
            
            # Radar chart comparison
            categories = ['form_cycle', 'class_ratings', 'speed_figures',
                        'distance_profile', 'track_profile']
            
            fig = go.Figure()
            
            for runner in df['Runner']:
                runner_data = df[df['Runner'] == runner].iloc[0]
                fig.add_trace(go.Scatterpolar(
                    r=[runner_data[cat] for cat in categories],
                    theta=categories,
                    fill='toself',
                    name=runner
                ))
            
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=True
            )
            
            st.plotly_chart(fig)
            
            # Detailed metrics table
            st.write("**Detailed Comparison**")
            comparison_table = df.set_index('Runner')
            st.dataframe(comparison_table)

    def _render_track_bias_analysis(self, race_data: Dict):
        """Render track bias analysis"""
        st.write("**Track Bias Analysis**")
        
        track_metrics = self.calculate_track_bias_metrics(race_data)
        
        # Barrier performance heatmap
        barrier_data = pd.DataFrame(track_metrics['barrier_stats']).T
        
        fig = px.imshow(
            barrier_data,
            labels=dict(x="Metric", y="Barrier", color="Value"),
            title="Barrier Performance Heatmap"
        )
        st.plotly_chart(fig)
        
        # Position changes visualization
        fig = go.Figure()
        for section in ['Early', 'Middle', 'Late']:
            fig.add_trace(go.Box(
                y=track_metrics['position_changes'][section],
                name=section,
                boxpoints='all'
            ))
        
        fig.update_layout(
            title="Position Changes by Race Section",
            yaxis_title="Position Change"
        )
        st.plotly_chart(fig)

    def _render_value_analysis(self, race_data: Dict):
        """Render value betting analysis"""
        st.write("**Value Analysis**")
        
        # Calculate true probabilities and compare with market odds
        value_opportunities = []
        for runner in race_data['runners']:
            true_prob = self._calculate_true_probability(runner)
            market_odds = runner.get('fixedOdds', {}).get('returnWin', 0)
            
            if market_odds > 0:
                market_prob = 1 / market_odds
                value = (true_prob * market_odds) - 1
                
                value_opportunities.append({
                    'Runner': runner['runnerName'],
                    'True Probability': true_prob,
                    'Market Probability': market_prob,
                    'Value': value
                })
        
        df = pd.DataFrame(value_opportunities)
        
        # Value comparison chart
        fig = go.Figure(data=[
            go.Bar(name='True Probability',
                  x=df['Runner'],
                  y=df['True Probability']),
            go.Bar(name='Market Probability',
                  x=df['Runner'],
                  y=df['Market Probability'])
        ])
        
        fig.update_layout(
            barmode='group',
            title='Probability Comparison'
        )
        st.plotly_chart(fig)
        
        # Value opportunities table
        st.write("**Value Opportunities**")
        value_df = df[df['Value'] > 0].sort_values('Value', ascending=False)
        st.dataframe(value_df)

    @st.cache_data
    def get_historical_performance(self, runner_data: Dict) -> pd.DataFrame:
        """Get cached historical performance data"""
        if 'formComments' not in runner_data:
            return pd.DataFrame()
            
        return pd.DataFrame(runner_data['formComments'])

    def render_form_analysis(self, runner_data: Dict):
        """Render comprehensive form analysis"""
        st.subheader(f"Form Analysis: {runner_data['runnerName']}")
        
        historical_data = self.get_historical_performance(runner_data)
        
        if not historical_data.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Performance trend
                fig = px.line(
                    historical_data,
                    x='date',
                    y='position',
                    title='Position History'
                )
                fig.update_yaxes(autorange="reversed")
                st.plotly_chart(fig)
            
            with col2:
                # Class progression
                fig = px.scatter(
                    historical_data,
                    x='date',
                    y='raceClass',
                    size='prizeMoney',
                    title='Class Progression'
                )
                st.plotly_chart(fig)
            
            # Detailed metrics
            metrics = self.calculate_runner_metrics(runner_data)
            
            st.write("**Performance Metrics**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Form Cycle", metrics['form_cycle']['trend'])
            