"""
Configuration for PA-API client
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Amazon PA-API credentials
AMAZON_ACCESS_KEY = os.getenv('AMAZON_ACCESS_KEY', '')
AMAZON_SECRET_KEY = os.getenv('AMAZON_SECRET_KEY', '')
AMAZON_PARTNER_TAG = os.getenv('AMAZON_PARTNER_TAG', '')
AMAZON_REGION = os.getenv('AMAZON_REGION', 'us-east-1')
