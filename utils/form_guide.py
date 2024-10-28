import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List
import logging

class FormAnalysis:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def analyze_form(self, runner_data: Dict) -> Dict:
        """Analyze runner's recent form"""
        try:
            form_string = runner_data.get('form', '')
            recent_results = []
            
            # Convert form string to list of positions
            for char in form_string:
                if char.isdigit():
                    recent_results.append(int(char))
                elif char.upper() == 'W':
                    recent_results.append(1)
                    
            if not recent_results:
                return {
                    'trend': 'Unknown',
                    'consistency': 0,
                    'average_position': 0,
                    'win_rate': 0,
                    'place_rate': 0
                }
                
            # Calculate metrics
            avg_pos = sum(recent_results) / len(recent_results)
            wins = sum(1 for pos in recent_results if pos == 1)
            places = sum(1 for pos in recent_results if pos <= 3)
            
            # Determine trend
            if len(recent_results) >= 3:
                last_three = recent_results[-3:]
                if all(x <= y for x, y in zip(last_three, last_three[1:])):
                    trend = 'Declining'
                elif all(x >= y for x, y in zip(last_three, last_three[1:])):
                    trend = 'Improving'
                else:
                    trend = 'Mixed'
            else:
                trend = 'Insufficient data'
                
            return {
                'trend': trend,
                'consistency': round(100 * (1 - pd.Series(recent_results).std() / max(recent_results)), 2),
                'average_position': round(avg_pos, 2),
                'win_rate': round(100 * wins / len(recent_results), 2),
                'place_rate': round(100 * places / len(recent_results), 2)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing form: {str(e)}")
            return {
                'trend': 'Error',
                'consistency': 0,
                'average_position': 0,
                'win_rate': 0,
                'place_rate': 0
            }
            
    def render_form_dashboard(self, runner_data: Dict):
        """Render form analysis dashboard in Streamlit"""
        try:
            # Analyze form
            analysis = self.analyze_form(runner_data)
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Win Rate",
                    f"{analysis['win_rate']}%",
                    help="Percentage of wins in recent starts"
                )
                
            with col2:
                st.metric(
                    "Place Rate",
                    f"{analysis['place_rate']}%",
                    help="Percentage of placings (top 3) in recent starts"
                )
                
            with col3:
                st.metric(
                    "Consistency",
                    f"{analysis['consistency']}%",
                    help="Measure of performance consistency"
                )
                
            # Form trend
            st.subheader("Form Trend")
            trend_color = {
                'Improving': 'green',
                'Declining': 'red',
                'Mixed': 'orange',
                'Unknown': 'grey',
                'Error': 'red',
                'Insufficient data': 'grey'
            }
            
            st.markdown(
                f"<p style='color: {trend_color[analysis['trend']]};'>"
                f"Current Trend: {analysis['trend']}</p>",
                unsafe_allow_html=True
            )
            
            # Recent performance visualization
            if 'form' in runner_data:
                st.subheader("Recent Performance")
                form_data = []
                for i, char in enumerate(reversed(runner_data['form'])):
                    if char.isdigit():
                        form_data.append({
                            'Start': len(runner_data['form']) - i,
                            'Position': int(char)
                        })
                    elif char.upper() == 'W':
                        form_data.append({
                            'Start': len(runner_data['form']) - i,
                            'Position': 1
                        })
                        
                if form_data:
                    df = pd.DataFrame(form_data)
                    st.line_chart(
                        df.set_index('Start')['Position'],
                        use_container_width=True
                    )
                    
            # Additional analysis sections can be added here
            
        except Exception as e:
            self.logger.error(f"Error rendering form dashboard: {str(e)}")
            st.error("Error displaying form analysis")
