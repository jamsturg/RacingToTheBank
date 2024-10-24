import streamlit as st
from datetime import datetime, timedelta
import time
from typing import Dict, List
import threading
import queue
import logging

class RaceAlertSystem:
    def __init__(self):
        self.alert_queue = queue.Queue()
        self.alert_history = []
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def add_alert(self, alert_type: str, message: str, severity: str = "info"):
        """Add a new alert to the queue"""
        alert = {
            "type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now()
        }
        self.alert_queue.put(alert)
        self.alert_history.append(alert)
        
    def check_race_status(self, race_data: Dict) -> List[Dict]:
        """Monitor race status changes"""
        alerts = []
        try:
            status = race_data.get('payLoad', {}).get('raceStatus', 'Unknown')
            if status == 'Late Scratching':
                alerts.append({
                    "type": "status",
                    "message": "Late scratching reported",
                    "severity": "warning"
                })
            elif status == 'Final Field':
                alerts.append({
                    "type": "status",
                    "message": "Final field declared",
                    "severity": "info"
                })
            elif status == 'Race Closed':
                alerts.append({
                    "type": "status",
                    "message": "Race is now closed",
                    "severity": "info"
                })
        except Exception as e:
            self.logger.error(f"Error checking race status: {str(e)}")
        return alerts
        
    def check_odds_changes(self, current_odds: Dict, previous_odds: Dict) -> List[Dict]:
        """Monitor significant odds changes"""
        alerts = []
        try:
            for horse, current in current_odds.items():
                if horse in previous_odds:
                    prev = previous_odds[horse]
                    change = current - prev
                    if abs(change) >= 2.0:  # Significant change threshold
                        direction = "shortened" if change < 0 else "drifted"
                        alerts.append({
                            "type": "odds",
                            "message": f"{horse} has {direction} from {prev:.1f} to {current:.1f}",
                            "severity": "info"
                        })
        except Exception as e:
            self.logger.error(f"Error checking odds changes: {str(e)}")
        return alerts
        
    def check_time_alerts(self, race_time: datetime) -> List[Dict]:
        """Generate time-based alerts"""
        alerts = []
        try:
            now = datetime.now()
            time_to_race = race_time - now
            
            if time_to_race <= timedelta(minutes=30) and time_to_race > timedelta(minutes=29):
                alerts.append({
                    "type": "time",
                    "message": "Race starting in 30 minutes",
                    "severity": "info"
                })
            elif time_to_race <= timedelta(minutes=10) and time_to_race > timedelta(minutes=9):
                alerts.append({
                    "type": "time",
                    "message": "Race starting in 10 minutes",
                    "severity": "warning"
                })
            elif time_to_race <= timedelta(minutes=5) and time_to_race > timedelta(minutes=4):
                alerts.append({
                    "type": "time",
                    "message": "Race starting in 5 minutes",
                    "severity": "warning"
                })
        except Exception as e:
            self.logger.error(f"Error checking time alerts: {str(e)}")
        return alerts

    def render_alerts(self):
        """Render alerts in Streamlit"""
        with st.expander("Race Alerts", expanded=True):
            if not self.alert_history:
                st.info("No alerts to display")
                return
                
            for alert in reversed(self.alert_history[-5:]):  # Show last 5 alerts
                timestamp = alert["timestamp"].strftime("%H:%M:%S")
                message = f"{timestamp} - {alert['message']}"
                
                if alert["severity"] == "error":
                    st.error(message)
                elif alert["severity"] == "warning":
                    st.warning(message)
                else:
                    st.info(message)
                    
    def process_alerts(self):
        """Process alerts from the queue"""
        try:
            while True:
                try:
                    alert = self.alert_queue.get_nowait()
                    self.alert_history.append(alert)
                    if len(self.alert_history) > 50:  # Keep last 50 alerts
                        self.alert_history.pop(0)
                except queue.Empty:
                    break
        except Exception as e:
            self.logger.error(f"Error processing alerts: {str(e)}")

def create_alert_system():
    """Create or get existing alert system"""
    if 'alert_system' not in st.session_state:
        st.session_state.alert_system = RaceAlertSystem()
    return st.session_state.alert_system
