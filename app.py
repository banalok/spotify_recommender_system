import streamlit as st
from datetime import datetime
import time
from real_time_data_extraction import (
    init_spotify_client, 
    fetch_top_tracks, 
    process_spotify_data,
    upload_to_hopsworks    
)
from recommendation import get_recommendations
from dotenv import load_dotenv
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Spotify Music Recommendation System",
    page_icon="🎵",
    layout="wide"
)

# Add some custom CSS
st.markdown("""
<style>
    .header {
        background-color: #1DB954;
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
        text-align: center;
    }
    .spotify-green {
        color: #1DB954;
    }
    .card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #eee;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'spotify_client' not in st.session_state:
    st.session_state.spotify_client = None
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = None
if 'progress' not in st.session_state:
    st.session_state.progress = ""
if 'processing' not in st.session_state:
    st.session_state.processing = False

# Header
st.markdown('<div class="header"><h1>🎵 Spotify Music Recommendation System</h1></div>', unsafe_allow_html=True)

# Two column layout
left_col, right_col = st.columns([2, 1])

with right_col:
    # How it works section
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("How it works")
    st.markdown("""
    1. Click the **Get Recommendations** button
    2. The app will analyze your recent Spotify history
    3. It will recommend new songs based on your taste
    4. Save recommendations to a Spotify playlist
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Action buttons
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Actions")
    analyze_button = st.button("Get Recommendations", type="primary", use_container_width=True)
    create_playlist_button = st.button("Create Playlist", type="secondary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Show user profile if connected
    if st.session_state.spotify_client is not None:
        try:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Your Profile")
            user = st.session_state.spotify_client.current_user()
            if 'images' in user and len(user['images']) > 0:
                st.image(user['images'][0]['url'], width=100)
            st.write(f"**{user['display_name']}**")
            st.write(f"Followers: {user['followers']['total']}")
            st.markdown('</div>', unsafe_allow_html=True)
        except:
            pass

# Main content area
with left_col:
    # Results area
    message_placeholder = st.empty()
    
    # Show recommendations if available
    if st.session_state.recommendations is not None and not st.session_state.processing:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🌟 Recommended Tracks")
        
        # Create a formatted table of recommendations
        st.write("Based on your listening history, we recommend these tracks:")
        
        # Format as a table
        recs_df = st.session_state.recommendations[['track_name', 'artist_name']].copy()
        recs_df.columns = ['Track', 'Artist']
        recs_df.index = range(1, len(recs_df) + 1)  # 1-based indexing
        st.table(recs_df)
        
        st.markdown('</div>', unsafe_allow_html=True)

# Functions (unchanged)
def process_user_data():
    st.session_state.processing = True
    log = ""
    
    # Step 1: Initialize Spotify client
    log += "🎵 Step 1: Initializing Spotify client...\n"
    message_placeholder.markdown(f"""<div class="card">
    <h3>Processing</h3>
    <pre>{log}</pre>
    </div>""", unsafe_allow_html=True)
    
    try:
        st.session_state.spotify_client = init_spotify_client()
        time.sleep(1)  # Small delay for UI feedback
        
        # Step 2: Fetch top tracks
        log += "📊 Step 2: Fetching your top tracks from Spotify...\n"
        message_placeholder.markdown(f"""<div class="card">
        <h3>Processing</h3>
        <pre>{log}</pre>
        </div>""", unsafe_allow_html=True)
        
        top_tracks = fetch_top_tracks(st.session_state.spotify_client, limit=10, time_range="short_term")
        time.sleep(1)
        
        # Display top tracks
        log += "\n🎧 Your Top 10 Recent Tracks:\n"
        log += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for i, track in enumerate(top_tracks, 1):
            track_name = track["name"]
            artists = ", ".join(artist["name"] for artist in track["artists"])
            log += f"{i}. 🎵 {track_name}\n   👤 {artists}\n"
        log += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message_placeholder.markdown(f"""<div class="card">
        <h3>Processing</h3>
        <pre>{log}</pre>
        </div>""", unsafe_allow_html=True)
        time.sleep(1)
        
        # Step 3: Process data
        log += "\n📝 Step 3: Processing data...\n"
        message_placeholder.markdown(f"""<div class="card">
        <h3>Processing</h3>
        <pre>{log}</pre>
        </div>""", unsafe_allow_html=True)
        
        df = process_spotify_data(top_tracks)
        time.sleep(1)
        
        # Step 4: Upload to Hopsworks
        log += "💾 Step 4: Uploading data to Hopsworks...\n"
        message_placeholder.markdown(f"""<div class="card">
        <h3>Processing</h3>
        <pre>{log}</pre>
        </div>""", unsafe_allow_html=True)
        
        result = upload_to_hopsworks(df)
        log += f"✅ {result}\n"
        message_placeholder.markdown(f"""<div class="card">
        <h3>Processing</h3>
        <pre>{log}</pre>
        </div>""", unsafe_allow_html=True)
        time.sleep(1)
        
        # Step 5: Get recommendations
        log += "🎯 Step 5: Getting personalized recommendations...\n"
        message_placeholder.markdown(f"""<div class="card">
        <h3>Processing</h3>
        <pre>{log}</pre>
        </div>""", unsafe_allow_html=True)
        
        st.session_state.recommendations = get_recommendations(top_tracks)
        log += "\n🌟 Recommended Songs:\n"
        log += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for i, (_, row) in enumerate(st.session_state.recommendations.iterrows(), 1):
            log += f"{i}. 🎵 {row['track_name']}\n   👤 {row['artist_name']}\n"
        log += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        log += "\n✨ Click 'Create Playlist' to save these recommendations to your Spotify account!\n"
        message_placeholder.markdown(f"""<div class="card">
        <h3>Processing</h3>
        <pre>{log}</pre>
        </div>""", unsafe_allow_html=True)
        
        st.session_state.progress = log
        st.session_state.processing = False
        
        # Rerun to refresh the UI with recommendations
        st.experimental_rerun()
        
    except Exception as e:
        log += f"\n❌ Error: {str(e)}\n"
        message_placeholder.markdown(f"""<div class="card">
        <h3>Processing</h3>
        <pre>{log}</pre>
        </div>""", unsafe_allow_html=True)
        st.session_state.progress = log
        st.session_state.processing = False

def create_spotify_playlist():
    if st.session_state.spotify_client is None or st.session_state.recommendations is None:
        st.error("⚠️ Please fetch recommendations first!")
        return
    
    try:
        with st.spinner("Creating playlist in Spotify..."):
            # Get the Spotify client and recommendations
            spotify_client = st.session_state.spotify_client
            recommendations = st.session_state.recommendations
            
            # Create a new playlist
            user_profile = spotify_client.current_user()
            user_id = user_profile["id"]
            
            playlist_name = f"Recommended Tracks {datetime.now().strftime('%Y-%m-%d')}"
            playlist_description = "Personalized recommendations based on your listening history"
            
            playlist = spotify_client.user_playlist_create(
                user=user_id,
                name=playlist_name,
                public=False,
                description=playlist_description
            )
            
            # Search for each recommended track to get its URI
            track_uris = []
            for _, row in recommendations.iterrows():
                track_name = row["track_name"]
                artist_name = row["artist_name"]
                
                # Search for the track
                query = f"track:{track_name} artist:{artist_name}"
                search_results = spotify_client.search(q=query, type="track", limit=1)
                
                # If found, add to our list
                if search_results["tracks"]["items"]:
                    track_uri = search_results["tracks"]["items"][0]["uri"]
                    track_uris.append(track_uri)
            
            # Add tracks to the playlist
            if track_uris:
                spotify_client.playlist_add_items(playlist["id"], track_uris)
                result = {
                    "message": f"Created playlist '{playlist_name}' with {len(track_uris)} tracks!",
                    "url": playlist["external_urls"]["spotify"]
                }
            else:
                result = {
                    "message": "Created playlist but couldn't find any tracks to add.",
                    "url": playlist["external_urls"]["spotify"]
                }
            
        # Display success message and link
        if result['url']:
            st.success(f"✅ Success! {result['message']}")
            st.markdown(f"""
            <div style="text-align: center; padding: 10px;">
                <a href="{result["url"]}" target="_blank" style="
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #1DB954;
                    color: white;
                    text-decoration: none;
                    border-radius: 10px;
                    font-weight: bold;
                    transition: all 0.3s ease;">
                    🎧 Open in Spotify
                </a>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.success(f"✅ Success! {result['message']}")
    except Exception as e:
        st.error(f"❌ Error creating playlist: {str(e)}")

# Button actions (unchanged)
if analyze_button:
    process_user_data()

if create_playlist_button:
    create_spotify_playlist()

# Display progress (only if not actively processing and no recommendations yet)
if st.session_state.progress and not st.session_state.processing and st.session_state.recommendations is None:
    message_placeholder.markdown(f"""<div class="card">
    <h3>Results</h3>
    <pre>{st.session_state.progress}</pre>
    </div>""", unsafe_allow_html=True)
