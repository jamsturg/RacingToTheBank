import os
import sys
from pathlib import Path

# Ensure we're not in numpy source directory
if 'numpy' in os.getcwd():
    os.chdir(str(Path.home()))

# Add the project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import base64
from pathlib import Path
from utils.resource_manager import resource_manager, optimize_streamlit_cache, monitor_performance

# Load custom CSS
def load_css():
    css_file = Path(__file__).parent / "static" / "custom.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from datetime import datetime, date
from typing import Dict, List, Optional, Union
import logging
import json

# Local imports
try:
    from punting_form_analyzer import PuntingFormAPI
except ImportError:
    st.error("Missing PuntingFormAPI implementation")
    raise
from account_management import AccountManager
from utils.date_utils import format_date, format_countdown
from utils.race_details import render_race_details
from utils.logger import setup_logger

# Optional imports with fallback
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# Configure logging
logger = setup_logger(
    "main",
    Path("logs/main.log"),
    level=logging.INFO
)

# Page config with reduced memory usage
st.set_page_config(
    page_title="To The Bank",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': 'Racing Analysis Platform'
    }
)

@monitor_performance
def initialize_session_state():
    """Initialize and validate session state variables with resource monitoring"""
    # Define session variables and their default values
    session_vars = {
        'initialized': True,
        'client': None,
        'selected_race': None,
        'active_tab': "Racing",
        'betslip': [],
        'logged_in': False,
        'webgl_context_lost': False,
        'connection_error': False,
        'last_refresh': None,
        'error_count': 0,
        'notifications': [],
        'dark_mode': False,
        'preferences': {},
        'tab_client': None,
        'account': None,
        'account_token': None,
        'login_error': None,
        'auth_attempts': 0,
        'last_balance_check': None,
        'loading_state': False
    }
    
    # Initialize unset variables
    for var, default in session_vars.items():
        if var not in st.session_state:
            st.session_state[var] = default
            
    # Validate existing variables
    for var in list(st.session_state):
        if var in session_vars and not isinstance(st.session_state[var], type(session_vars[var])):
            logger.warning(f"Invalid type for session variable {var}, resetting to default")
            st.session_state[var] = session_vars[var]
        elif var not in session_vars:
            # Clear old variables not in current session_vars
            del st.session_state[var]

@monitor_performance
def initialize_client() -> Optional[PuntingFormAPI]:
    """Initialize API client with resource monitoring"""
    if not st.session_state.logged_in:
        return None
        
    if st.session_state.client is None:
        try:
            # Check for API key in multiple locations
            api_key = (
                st.secrets.get("punting_form", {}).get("api_key") or
                os.environ.get("PUNTING_FORM_API_KEY")
            )
            
            if not api_key:
                logger.error("API key not found in secrets or environment")
                st.error("Missing Punting Form API key. Please check configuration.")
                st.stop()
            
            client = PuntingFormAPI(api_key)
            
            # Test API connection
            if not client.verify_credentials():
                logger.error("API credentials verification failed")
                st.error("Invalid API credentials. Please check your API key.")
                st.stop()
                
            st.session_state.client = client
            logger.info("API client initialized and verified successfully")
            
        except Exception as e:
            logger.error(f"Client initialization error: {str(e)}", exc_info=True)
            st.error(
                "Failed to initialize client. Please check your API key and network connection."
            )
            st.stop()
            
    return st.session_state.client

@monitor_performance
def main():
    try:
        # Load custom CSS
        load_css()
        
        # Initialize session state first
        initialize_session_state()
        
        # Optimize cache periodically
        optimize_streamlit_cache()
        
        # Initialize account manager
        account_manager = AccountManager()
        
        # Show login form and require login before proceeding
        account_manager.render_login()

        # Monitor resource usage
        memory_usage = resource_manager.get_memory_usage()
        cpu_usage = resource_manager.get_cpu_usage()
        
        if memory_usage['rss'] > 1500:  # If memory usage exceeds 1.5GB
            logger.warning("High memory usage detected, performing cleanup")
            resource_manager.cleanup()
            
        # Only proceed with API initialization and content if logged in
        if st.session_state.logged_in:
            if st.session_state.account and st.session_state.account.get('user_id') != 'guest':
                if st.session_state.client is None:
                    initialize_client()
            
            # Main content
            st.markdown("""
                <h1 style='text-align: center; color: #1E88E5; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);'>
                    💰 To The Bank
                </h1>
                <p style='text-align: center; font-style: italic; color: #666;'>
                    Your path to smarter racing investments
                </p>
                """, unsafe_allow_html=True)
            
            if st.session_state.active_tab == "Racing":
                render_next_to_jump()
        else:
            st.info("Please log in to access racing information")
            
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        st.error("An unexpected error occurred. Please try again.")
        resource_manager.cleanup()

if __name__ == "__main__":
    main()
