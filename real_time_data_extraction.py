from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import hopsworks
import pandas as pd
import os
import streamlit as st
import numpy as np
# load_dotenv()

def init_spotify_client():
    """Initialize the Spotify client using SpotifyOAuth directly."""
    return Spotify(auth_manager=SpotifyOAuth(
        client_id=st.secrets["spotify"]["SPOTIPY_CLIENT_ID"], #os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=st.secrets["spotify"]["SPOTIPY_CLIENT_SECRET"], #os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=st.secrets["spotify"]["SPOTIPY_REDIRECT_URI"], #os.getenv("SPOTIPY_REDIRECT_URI"),
        scope="user-top-read playlist-modify-public playlist-modify-private"
    ))

def fetch_top_tracks(spotify_client, limit=10, time_range="short_term"):
    """Fetch user's top tracks."""
    results = spotify_client.current_user_top_tracks(limit=limit, time_range=time_range)
    return results["items"]

def process_spotify_data(tracks):
    """Process Spotify data and return a DataFrame."""
    extra_fields = {
        "album_name": "unknown_album",
        "duration_ms": 0,
        "acousticness": 0,
        "danceability": 0,
        "energy": 0,
        "key": 0,
        "loudness": 0,
        "mode": 0,
        "speechiness": 0,
        "instrumentalness": 0,
        "liveness": 0,
        "tempo": 0,
        "time_signature": 0,
        "artist_avg_popularity": 0,
        "artist_popularity_std": 0,
        "artist_track_count": 0,
        "artist_avg_acousticness": 0,
        "artist_avg_danceability": 0,
        "artist_avg_energy": 0,
        "duration_minutes": 0,
        "track_genre": "unknown" 
    }
    data = []
    for track in tracks:
        normalized_popularity = track["popularity"] / 100.0
        row = {
            "track_id": track["id"],
            "track_name": track["name"],
            "artist_name": ", ".join(artist["name"] for artist in track["artists"]),
            "popularity": normalized_popularity
        }
        row.update(extra_fields)
        data.append(row)    
    return pd.DataFrame(data)

def upload_to_hopsworks(df, feature_group_name="recommender_spotify", version=2):
    """Upload DataFrame to Hopsworks Feature Group, skipping tracks that already exist."""
    import numpy as np
    
    # Get API key from secrets
    hopsworks_api_key = st.secrets["hopsworks"]["api_key"]
    if not hopsworks_api_key:
        raise ValueError("HOPSWORKS_API_KEY not found in secrets. Please check your configuration.")
    
    # Set environment variable for Hopsworks
    os.environ["HOPSWORKS_API_KEY"] = hopsworks_api_key
    
    # Connect to Hopsworks
    project = hopsworks.login()
    fs = project.get_feature_store()
    feature_group = fs.get_feature_group(name=feature_group_name, version=version)
    
    # Fetch existing tracks to check for duplicates
    existing_df = feature_group.read()
    existing_track_ids = set(existing_df['track_id'].tolist())
    
    # Filter to only include new tracks
    new_tracks_df = df[~df['track_id'].isin(existing_track_ids)]
    
    # If no new tracks, skip upload
    if new_tracks_df.empty:
        return "No new tracks to upload. Using existing data."
    
    # Prepare new tracks for upload
    columns_to_convert = [
        "acousticness", "danceability", "energy", "loudness", "speechiness", 
        "instrumentalness", "liveness", "tempo", "time_signature", 
        "artist_avg_popularity", "artist_popularity_std", "artist_track_count", 
        "artist_avg_acousticness", "artist_avg_danceability", "artist_avg_energy", 
        "duration_minutes"
    ]
    
    # Convert to appropriate types
    new_tracks_df[columns_to_convert] = new_tracks_df[columns_to_convert].astype(float)    
    new_tracks_df["time_signature"] = new_tracks_df["time_signature"].astype(np.int64)
    
    # Upload only the new tracks
    feature_group.insert(new_tracks_df, write_options={"wait_for_job": True})
    
    return f"Uploaded {len(new_tracks_df)} new tracks to Hopsworks"

if __name__ == "__main__":
    # Initialize Spotify client using SpotifyOAuth directly
    spotify_client = init_spotify_client()
    
    # Fetch top tracks
    top_tracks = fetch_top_tracks(spotify_client, limit=10, time_range="short_term")
    
    print("Top 10 songs user played most recently:")
    
    # Process the data
    df = process_spotify_data(top_tracks)
    
    # Display and save the data
    print(df.to_string())
    df.to_csv("output.csv", index=True)
    print("Data saved to output.csv")
    
    # Upload to Hopsworks
    result = upload_to_hopsworks(df)
    print(result)