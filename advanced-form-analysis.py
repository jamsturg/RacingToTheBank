```python
class FormAnalysis:
    def __init__(self):
        self.scaler = StandardScaler()
        self.weights = {
            'recent_form': 0.3,
            'class': 0.2,
            'distance': 0.15,
            'track': 0.15,
            'time': 0.2
        }

    def analyze_advanced_form(self, runner_data: Dict) -> Dict:
        """Comprehensive form analysis with predictive metrics"""
        form_data = runner_data.get('formComments', [])
        if not form_data:
            return {}

        df = pd.DataFrame(form_data)
        
        analysis = {
            'ratings': self._calculate_ratings(df),
            'patterns': self._identify_patterns(df),
            'progression': self._analyze_progression(df),
            'preferences': self._analyze_preferences(df),
            'predictive_metrics': self._calculate_predictive_metrics(df, runner_data)
        }
        
        return analysis

    def _calculate_ratings(self, df: pd.DataFrame) -> Dict:
        """Calculate comprehensive performance ratings"""
        if df.empty:
            return {}

        recent_runs = df.iloc[-5:] if len(df) >= 5 else df
        
        # Base rating
        base_ratings = []
        for _, run in recent_runs.iterrows():
            rating = 100 - (run['position'] * 2)
            
            # Class adjustment
            class_factor = self._get_class_factor(run.get('raceClass', ''))
            rating += class_factor
            
            # Distance adjustment
            distance_factor = self._get_distance_factor(
                run.get('distance', 0),
                run.get('trackCondition', '')
            )
            rating *= distance_factor
            
            # Weight adjustment
            weight_factor = self._get_weight_factor(run.get('weight', 0))
            rating *= weight_factor
            
            base_ratings.append(rating)

        return {
            'current_rating': base_ratings[-1] if base_ratings else 0,
            'peak_rating': max(base_ratings) if base_ratings else 0,
            'average_rating': np.mean(base_ratings) if base_ratings else 0,
            'rating_trend': self._calculate_trend(base_ratings),
            'consistency': np.std(base_ratings) if base_ratings else 0
        }

    def _identify_patterns(self, df: pd.DataFrame) -> Dict:
        """Identify recurring performance patterns"""
        if df.empty:
            return {}

        patterns = {
            'track_preferences': self._analyze_track_preferences(df),
            'distance_patterns': self._analyze_distance_patterns(df),
            'seasonal_performance': self._analyze_seasonal_performance(df),
            'class_patterns': self._analyze_class_patterns(df),
            'running_style': self._analyze_running_style(df)
        }
        
        return patterns

    def _analyze_progression(self, df: pd.DataFrame) -> Dict:
        """Analyze career progression and development"""
        if df.empty:
            return {}

        # Calculate progressive metrics
        metrics = {
            'career_stage': self._determine_career_stage(df),
            'class_progression': self._analyze_class_progression(df),
            'ratings_progression': self._analyze_ratings_progression(df),
            'development_indicators': self._get_development_indicators(df)
        }
        
        return metrics

    def render_form_dashboard(self, runner_data: Dict):
        """Render comprehensive form analysis dashboard"""
        st.subheader(f"Form Analysis: {runner_data['runnerName']}")
        
        analysis = self.analyze_advanced_form(runner_data)
        if not analysis:
            st.warning("No form data available")
            return

        # Performance Ratings Tab
        tabs = st.tabs([
            "Ratings Analysis",
            "Performance Patterns",
            "Career Progression",
            "Predictive Analysis",
            "Comparative Stats"
        ])

        with tabs[0]:
            self._render_ratings_analysis(analysis['ratings'])
        
        with tabs[1]:
            self._render_patterns_analysis(analysis['patterns'])
            
        with tabs[2]:
            self._render_progression_analysis(analysis['progression'])
            
        with tabs[3]:
            self._render_predictive_analysis(analysis['predictive_metrics'])
            
        with tabs[4]:
            self._render_comparative_analysis(runner_data)

    def _render_ratings_analysis(self, ratings: Dict):
        """Render ratings analysis visualization"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Ratings gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=ratings['current_rating'],
                delta={'reference': ratings['average_rating']},
                title={'text': "Current Rating"},
                gauge={
                    'axis': {'range': [None, 120]},
                    'steps': [
                        {'range': [0, 40], 'color': "lightgray"},
                        {'range': [40, 80], 'color': "gray"},
                        {'range': [80, 120], 'color': "darkblue"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': ratings['peak_rating']
                    }
                }
            ))
            
            st.plotly_chart(fig)
        
        with col2:
            # Ratings metrics
            st.metric("Peak Rating", f"{ratings['peak_rating']:.1f}")
            st.metric(
                "Rating Trend",
                ratings['rating_trend'],
                delta=f"{ratings['average_rating']:.1f}"
            )
            st.metric(
                "Consistency",
                f"{100 - ratings['consistency']:.1f}%"
            )

    def _render_patterns_analysis(self, patterns: Dict):
        """Render performance patterns analysis"""
        # Track preferences visualization
        st.subheader("Track Preferences")
        
        track_data = pd.DataFrame(patterns['track_preferences']).T
        
        fig = px.scatter(
            track_data,
            x='wins',
            y='placings',
            size='starts',
            hover_data=['win_rate'],
            text=track_data.index,
            title="Track Performance Analysis"
        )
        
        st.plotly_chart(fig)
        
        # Distance patterns
        st.subheader("Distance Patterns")
        
        distance_data = pd.DataFrame(patterns['distance_patterns']).T
        
        fig = go.Figure(data=[
            go.Scatter(
                x=list(patterns['distance_patterns'].keys()),
                y=[d['performance_rating'] for d in patterns['distance_patterns'].values()],
                mode='lines+markers',
                name='Performance Rating'
            )
        ])
        
        fig.update_layout(
            title="Performance by Distance",
            xaxis_title="Distance (m)",
            yaxis_title="Performance Rating"
        )
        
        st.plotly_chart(fig)
        
        # Running style visualization
        st.subheader("Running Style Analysis")
        
        style_data = patterns['running_style']
        
        fig = px.pie(
            values=[style_data[key] for key in style_data],
            names=list(style_data.keys()),
            title="Running Style Distribution"
        )
        
        st.plotly_chart(fig)

    def _render_progression_analysis(self, progression: Dict):
        """Render career progression analysis"""
        st.subheader("Career Development")
        
        # Career stage indicator
        stage = progression['career_stage']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Career Stage", stage['current_stage'])
            st.write(f"Age: {stage['age']}")
            st.write(f"Total Starts: {stage['total_starts']}")
        
        with col2:
            # Class progression chart
            class_prog = progression['class_progression']
            
            fig = go.Figure(data=[
                go.Scatter(
                    x=class_prog['dates'],
                    y=class_prog['class_ratings'],
                    mode='lines+markers',
                    name='Class Rating'
                )
            ])
            
            fig.update_layout(
                title="Class Progression",
                xaxis_title="Date",
                yaxis_title="Class Rating"
            )
            
            st.plotly_chart(fig)
        
        with col3:
            # Development indicators
            indicators = progression['development_indicators']
            
            for indicator, value in indicators.items():
                st.metric(
                    indicator.replace('_', ' ').title(),
                    f"{value:.1f}%"
                )

    def _render_predictive_analysis(self, predictive_metrics: Dict):
        """Render predictive analysis visualization"""
        st.subheader("Performance Predictions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Win probability gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=predictive_metrics['win_probability'] * 100,
                title={'text': "Win Probability"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'steps': [
                        {'range': [0, 30], 'color': "lightgray"},
                        {'range': [30, 70], 'color': "gray"},
                        {'range': [70, 100], 'color': "darkgreen"}
                    ]
                }
            ))
            
            st.plotly_chart(fig)
        
        with col2:
            # Performance factors
            factors = predictive_metrics['performance_factors']
            
            fig = go.Figure(data=[
                go.Bar(
                    x=list(factors.keys()),
                    y=list(factors.values()),
                    text=[f"{v:.1%}" for v in factors.values()],
                    textposition='auto'
                )
            ])
            
            fig.update_layout(
                title="Performance Factors",
                xaxis_title="Factor",
                yaxis_title="Impact"
            )
            
            st.plotly_chart(fig)

    def _render_comparative_analysis(self, runner_data: Dict):
        """Render comparative analysis against field"""
        st.subheader("Field Comparison")
        
        if 'fieldComparison' not in runner_data:
            st.warning("No comparative data available")
            return
        
        comparison = runner_data['fieldComparison']
        
        # Radar chart comparison
        categories = ['Speed', 'Class', 'Form', 'Distance', 'Track']
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=[comparison[cat.lower()] for cat in categories],
            theta=categories,
            fill='toself',
            name=runner_data['runnerName']
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=[comparison[f'field_avg_{cat.lower()}'] for cat in categories],
            theta=categories,
            fill='toself',
            name='Field Average'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            title="Field Comparison"
        )
        
        st.plotly_chart(fig)

def main():
    st.title("Racing Form Analysis Dashboard")
    
    # Initialize form analyzer
    form_analyzer = FormAnalysis()
    
    # Sample data - replace with real data in production
    runner_data = {
        'runnerName': 'Sample Runner',
        'formComments': [
            {
                'date': '2024-01-01',
                'position': 2,
                'raceClass': 'G2',
                'distance': 1200,
                'weight': 56,
                'trackCondition': 'Good'
            }
            # Add more form data here
        ]
    }
    
    # Render analysis dashboard
    form_analyzer.render_form_dashboard(runner_data)

if __name__ == "__main__":
    main()
```
