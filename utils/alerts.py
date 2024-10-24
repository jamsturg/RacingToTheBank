import streamlit as st
from datetime import datetime, timedelta
import time
from typing import Dict, List
import threading
import queue
import logging

# Alert categories with color-coded badges
ALERT_CATEGORIES = {
    'odds': {'label': 'Odds Change', 'color': '#1E88E5'},
    'track': {'label': 'Track Update', 'color': '#FFD700'},
    'race': {'label': 'Race Status', 'color': '#90EE90'},
    'time': {'label': 'Time Alert', 'color': '#FFB6C1'}
}

class RaceAlertSystem:
    def __init__(self):
        self.alert_queue = queue.Queue()
        self.alert_history = []
        self.last_alert_time = {}
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def add_alert(self, alert_type: str, message: str, severity: str = "info"):
        try:
            current_time = datetime.now()
            alert_key = f"{alert_type}:{message}"
            
            # Check cooldown (5 minutes)
            if alert_key in self.last_alert_time:
                if (current_time - self.last_alert_time[alert_key]).total_seconds() < 300:
                    return
                    
            alert = {
                "type": alert_type,
                "message": message,
                "severity": severity,
                "timestamp": current_time,
                "category": alert_type if alert_type in ALERT_CATEGORIES else 'time'
            }
            
            # Add to queue and history with exception handling
            try:
                self.alert_queue.put(alert)
                self.alert_history.append(alert)
                self.last_alert_time[alert_key] = current_time
                
                # Keep alert history manageable
                if len(self.alert_history) > 50:
                    self.alert_history = self.alert_history[-50:]
            except Exception as e:
                self.logger.error(f"Error managing alerts: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error adding alert: {str(e)}")
    
    def check_race_status(self, race_data) -> List[Dict]:
        alerts = []
        try:
            # Extract status based on data structure
            status = None
            if isinstance(race_data, list) and race_data:
                status = race_data[0].get('status', None)
            elif isinstance(race_data, dict):
                payload = race_data.get('payLoad', {})
                if isinstance(payload, dict):
                    status = payload.get('raceStatus')
                elif isinstance(payload, list) and payload:
                    status = payload[0].get('status')
            
            if status:
                if status == 'Late Scratching':
                    alerts.append({
                        "type": "race",
                        "message": "Late scratching reported",
                        "severity": "warning"
                    })
                elif status == 'Final Field':
                    alerts.append({
                        "type": "race",
                        "message": "Final field declared",
                        "severity": "info"
                    })
                elif status == 'Race Closed':
                    alerts.append({
                        "type": "race",
                        "message": "Race is now closed",
                        "severity": "info"
                    })
        except Exception as e:
            self.logger.error(f"Error checking race status: {str(e)}")
        return alerts
        
    def check_odds_changes(self, current_odds: Dict, previous_odds: Dict) -> List[Dict]:
        """Monitor significant odds changes with error handling"""
        alerts = []
        try:
            for horse, current in current_odds.items():
                if horse in previous_odds:
                    try:
                        prev = float(previous_odds[horse])
                        curr = float(current)
                        change = curr - prev
                        if abs(change) >= 2.0:  # Significant change threshold
                            direction = "shortened" if change < 0 else "drifted"
                            alerts.append({
                                "type": "odds",
                                "message": f"{horse} has {direction} from {prev:.1f} to {curr:.1f}",
                                "severity": "info"
                            })
                    except (ValueError, TypeError) as e:
                        self.logger.error(f"Error processing odds for {horse}: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error checking odds changes: {str(e)}")
        return alerts
        
    def check_time_alerts(self, race_time: datetime) -> List[Dict]:
        """Generate time-based alerts with error handling"""
        alerts = []
        try:
            now = datetime.now()
            time_to_race = race_time - now
            
            alert_times = [
                (timedelta(minutes=30), "Race starting in 30 minutes", "info"),
                (timedelta(minutes=10), "Race starting in 10 minutes", "warning"),
                (timedelta(minutes=5), "Race starting in 5 minutes", "warning")
            ]
            
            for time_threshold, message, severity in alert_times:
                if time_to_race <= time_threshold and time_to_race > (time_threshold - timedelta(minutes=1)):
                    alerts.append({
                        "type": "time",
                        "message": message,
                        "severity": severity
                    })
        except Exception as e:
            self.logger.error(f"Error checking time alerts: {str(e)}")
        return alerts

    def render_alerts(self):
        """Render alerts in Streamlit with enhanced styling"""
        if not self.alert_history:
            st.info("No alerts to display")
            return
            
        st.markdown('<div class="alerts-container">', unsafe_allow_html=True)
        for alert in reversed(self.alert_history[-5:]):  # Show last 5 alerts
            try:
                severity_color = {
                    'error': '#FFB6C1',
                    'warning': '#FFD700',
                    'info': '#90EE90'
                }.get(alert['severity'], '#FFFFFF')
                
                category = alert.get('category', 'time')
                category_info = ALERT_CATEGORIES.get(category, ALERT_CATEGORIES['time'])
                
                st.markdown(f'''
                    <div class="alert-card" style="border-left-color: {severity_color}">
                        <div class="alert-header">
                            <span class="alert-badge" style="background-color: {category_info['color']}">{category_info['label']}</span>
                            <small>{alert['timestamp'].strftime('%H:%M:%S')}</small>
                        </div>
                        <p class="alert-message">{alert['message']}</p>
                    </div>
                ''', unsafe_allow_html=True)
            except Exception as e:
                self.logger.error(f"Error rendering alert: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)

def create_alert_system():
    """Create or get existing alert system with error handling"""
    try:
        if 'alert_system' not in st.session_state:
            st.session_state.alert_system = RaceAlertSystem()
        return st.session_state.alert_system
    except Exception as e:
        print(f"Error creating alert system: {str(e)}")
        return RaceAlertSystem()
