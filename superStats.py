# ============================================================
# IMPORTS
# ============================================================
import requests
import json
import csv
import os
import sys
from datetime import datetime
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from dotenv import load_dotenv

load_dotenv() # Loads variables from .env
gemini_API_KEY = os.getenv("gemini_API_KEY")
CLIENT_ID = os.getenv("CLIENT_ID") 
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:8000/callback"

# used Gemini to get this
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope="user-top-read user-read-recently-played",
    show_dialog=True
)
sp = spotipy.Spotify(auth_manager=sp_oauth)

# ============================================================
# YOUR API KEY (REQUIRED)
# ============================================================

URL = (
    "https://generativelanguage.googleapis.com"
    "/v1beta/models/gemini-2.5-flash:generateContent"
    f"?key={gemini_API_KEY}"
)

# ============================================================
# STEP 0: HANDLE PATHS FOR PYINSTALLER
# ============================================================

def get_base_dir():
    """
    Returns the folder where the program is running:
    - If running as .py, it's the script folder
    - If running as .exe (PyInstaller), it's the exe folder
    """
    if getattr(sys, "frozen", False):
        # Running in PyInstaller bundle
        return os.path.dirname(sys.executable)
    else:
        # Running as normal .py script
        return os.path.dirname(os.path.abspath(__file__))

# ============================================================
# STEP 1: GET SPOTIFY INFORMATION FROM THE USER
# ============================================================

def get_spotify_data():
    # We used ai to get the spotify data because after getting the api and everything, we didn't know how to actually access the data
    """
    Pulls the maximum allowed history from Spotify's top items and recently played endpoints.
    """
    all_tracks_records = []

    # --- PART A: Get Top Tracks ---
    try:
        top_tracks = sp.current_user_top_tracks(limit=50, time_range="medium_term")
        for item in top_tracks.get('items', []):
            song = item.get('name')
            artist = item['artists'][0]['name'] if item.get('artists') else "Unknown"
            # Removed the album name to save space
            all_tracks_records.append(f"[Top Track] {song} by {artist}")
    except Exception as e:
        print("Error fetching top tracks:", e)

    # --- PART B: Get Recently Played Tracks ---
    try:
        recent_tracks = sp.current_user_recently_played(limit=50)
        for item in recent_tracks.get('items', []):
            track = item.get('track', {})
            song = track.get('name')
            artist = track['artists'][0]['name'] if track.get('artists') else "Unknown"
            # Just keeping a basic note that it was played recently
            all_tracks_records.append(f"[Recent] {song} by {artist}")
    except Exception as e:
        print("Error fetching recently played:", e)

    if not all_tracks_records:
        return "No listening history data could be retrieved."
        
    return "\n".join(all_tracks_records)

# ============================================================
# STEP 2: GENERATE STATS USING GEMINI
# ============================================================

def generate_stats(all_tracks_records):
    """
    Sends the user's listening data to Gemini and asks it to return stats.
    """
    prompt = f"""Based on the user's collected listening data, return their number one artist, top five artists including the number one, top five songs they've listened to the most so far, the number of times they've listened to their nbumber one top song, and the top 3 genres of songs they've listened to the most.
    
    Follow these rules strictly:
    1. Do NOT make up any data, ONLY use what is provided by spotify itself.
    2. For top artists and top songs, rank them based on how frequently they appear in the data, don't hallucinate values or make assumptions.
    3. While explicit genre data is not written in the log, you MUST use your own vast internal database and knowledge of music to look up the artists listed in the log, determine their genres, and find the top 3 most prominent genres overall.
    
    Use this raw listening data:
    {all_tracks_records}
    
Respond with ONLY a valid JSON array in this exact format:
[
  {{
    "top_artist": "Your number one artist so far is...",
    "top_five_artists": "Your top 5 artists so far are...",
    "top_five_songs": "Your top 5 songs so far are...",
    "top_times_played": "The number of times you played your number one top song is:...",
    "top_genres": "Your top 3 genres so far are..."
    }}
]
Only the JSON array. No extra text.
"""

    body = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(URL, json=body, timeout=60)

        if response.status_code != 200:
            print(f"API error: {response.status_code}")
            return None

        data = response.json()

        # Extract the text response from Gemini
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

        # Remove ```json code blocks if Gemini adds them
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]

        # Convert JSON text into Python list
        return json.loads(text)

    except Exception as e:
        print("Error generating Wrapped:", e)
        return None

# ============================================================
# STEP 3: DISPLAY THE LISTENING STATS
# ============================================================

def display_stats(wrapped):
    """
    Displays stats.
    """
    for item in wrapped:
        print("\nYour Number One Artist: ")
        print(item["top_artist"])
        print()
        print("\nYour Top 5 Artists: ")
        print(item["top_five_artists"])
        print()
        print("\nYour Top 5 Songs: ")
        print(item["top_five_songs"])
        print()
        print("\nYour Top Genres: ")
        print(item["top_genres"])
        print()
        print("\nYour Top Song: ")
        print(item["top_times_played"])
    
# ============================================================
# STEP 4: SAVE RESULTS TO CSV
# ============================================================

def save_stats(wrapped):
    """
    Saves wrapped results to stats.csv next to the exe/script.
    """
    base_dir = get_base_dir()
    file_path = os.path.join(base_dir, "stats.csv")

    file_exists = os.path.exists(file_path)

    with open(file_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "top_artist",
                "top_five_artists",
                "top_five_songs",
                "top_times_played",
                "top_genres"
            ],
        )

        # Write header only once
        if not file_exists:
            writer.writeheader()

        # Write one row per question
        for i in wrapped:
            writer.writerow({
                "top_artist": f"\n{i["top_artist"]}\n\n",
                "top_five_artists": f"\n{i["top_five_artists"]}\n\n",
                "top_five_songs": f"\n{i["top_five_songs"]}\n\n",
                "top_times_played": f"\n{i["top_times_played"]}\n\n",
                "top_genres": f"\n{i["top_genres"]}\n\n",
            })

    print("Wrapped saved to", file_path)

# ============================================================
# STEP 5: MAIN PROGRAM FLOW
# ============================================================

def main():
    print("🎧🎶SuperStats🎶🎤")
    print("=" * 35)
    
    wrapped = None
    
    while True:
        print("1. Generate stats")
        print("2. View saved stats")
        print("3. Exit")
        
        choice = int(input("Enter a choice (1-3): "))
        
        if choice == 1:
            print("\nConnecting to Spotify account data...")
            data = get_spotify_data()
            print("Analyzing with Gemini...")
            wrapped = generate_stats(data)
            if not wrapped:
                print("Could not generate your Wrapped.")
            else:
                print("Wrapped generated! Please pick choice #2 to view it.")
        elif choice == 2:
            if not wrapped:
                print("Please pick choice 1 before choice 2. The stats must be generated in order to display them.")
            else:
                display_stats(wrapped)
                save_stats(wrapped)
        elif choice == 3:
            print("Thanks for using SuperStats!")
            print("Enjoy your listening!")
            break
        else:
            print("Invalid. Please enter a choice 1 or 2.")

# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")