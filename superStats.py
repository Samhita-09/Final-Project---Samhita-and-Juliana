# ============================================================
# IMPORTS
# ============================================================
import requests
import json
import csv
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

load_dotenv() # Loads variables from .env
GEM_API_KEY = os.getenv("gemini_API_KEY")
SPOTIFY_API = os.getenv("spotify_API_KEY")
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID") 
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

auth_url = 'https://accounts.spotify.com/api/token'
auth_response = requests.post(auth_url, {
    'grant_type': 'client_credentials',
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
})

# Parse the JSON response to grab the token
access_token = auth_response.json().get('access_token')
print(f"Your temporary API Access Token: {access_token}")

# ============================================================
# YOUR API KEY (REQUIRED)
# ============================================================

URL = (
    
    "https://generativelanguage.googleapis.com"
    "/v1beta/models/gemini-2.5-flash:generateContent"
    f"?key={GEM_API_KEY}"
)
