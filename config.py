"""Configuration settings for the application"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class"""
    # API Keys
    PUNTING_FORM_API_KEY = os.getenv('PUNTING_FORM_API_KEY', '7552b21e-851b-4803-b230-d1637a74f05c')
    TAB_API_KEY = os.getenv('TAB_API_KEY', 'demo_key')
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///racing.db')
    
    # Application Settings
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # API Rate Limits
    API_RATE_LIMIT = int(os.getenv('API_RATE_LIMIT', '100'))  # requests per minute
    API_RATE_LIMIT_PERIOD = int(os.getenv('API_RATE_LIMIT_PERIOD', '60'))  # seconds
    
    # Cache Settings
    CACHE_TTL = int(os.getenv('CACHE_TTL', '300'))  # seconds
    
    # Feature Flags
    ENABLE_PREDICTIONS = os.getenv('ENABLE_PREDICTIONS', 'True').lower() == 'true'
    ENABLE_LIVE_UPDATES = os.getenv('ENABLE_LIVE_UPDATES', 'True').lower() == 'true'
    ENABLE_NOTIFICATIONS = os.getenv('ENABLE_NOTIFICATIONS', 'True').lower() == 'true'
    
    # Model Settings
    MODEL_VERSION = os.getenv('MODEL_VERSION', 'v1.0.0')
    MODEL_UPDATE_FREQUENCY = int(os.getenv('MODEL_UPDATE_FREQUENCY', '24'))  # hours
    
    # Betting Settings
    MIN_BET_AMOUNT = float(os.getenv('MIN_BET_AMOUNT', '1.0'))
    MAX_BET_AMOUNT = float(os.getenv('MAX_BET_AMOUNT', '1000.0'))
    DEFAULT_BET_AMOUNT = float(os.getenv('DEFAULT_BET_AMOUNT', '10.0'))
    
    # UI Settings
    THEME_COLOR = os.getenv('THEME_COLOR', '#4CAF50')
    SECONDARY_COLOR = os.getenv('SECONDARY_COLOR', '#2B4F76')
    FONT_FAMILY = os.getenv('FONT_FAMILY', 'Arial, sans-serif')
