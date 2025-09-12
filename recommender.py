import os
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from core.recommend import build_user_profile, recommend_custom


############################################################
# Streamlit Page Configuration
# Sets up the main page properties for the dashboard UI.
############################################################
st.set_page_config(
    page_title="🎵 Spotify Music Recommender",
    page_icon="🎧",
    layout="wide",
)

############################################################
# Custom CSS Styling
# Injects custom styles for track cards, images, song titles, and artist names.
############################################################
st.markdown(
    """
    <style>
    /* Track container spacing */
    .track-container {
        margin-bottom: 20px;
    }

    img {
        border-radius: 8px;
        max-width: 250px;
        margin-bottom: 10px;
    }

    /* 🎵 Song Title Styling */
    .track-title {
        color: ##6A0DAD;  
        font-size: 15px;            /* Increase font size */
        font-family: 'Tahoma', sans-serif; /* Change font family */
        font-weight: Bold;          /* Make it bold */
        margin-bottom: -10px;
    }

    /* 👩‍🎤 Artist Name Styling */
    .track-artist {
        color: #6A0DAD;
        font-size: 15px;            /* Slightly smaller than title */
        font-family: 'Sans Serif'; /* Example different font */
        font-style: italic;
        margin-top: -20px;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


############################################################
# Spotify API Credentials
# Credentials are securely loaded from Streamlit secrets.
############################################################
CLIENT_ID = st.secrets["CLIENT_ID"]
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
REDIRECT_URI = "http://127.0.0.1:3000"
SCOPE = "user-read-recently-played user-top-read"


############################################################
# Spotify Client Setup
# Returns an authenticated Spotipy client for API access.
############################################################
@st.cache_resource(ttl=3600)
def get_spotify_client():
    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            open_browser=True,  # Force open browser for authentication
            cache_path=".spotify_cache"  # Cache authentication
        )
    )


############################################################
# Spotify Data Fetch Functions
# Functions to fetch recent tracks and artist info from Spotify API.
############################################################
def get_recent_tracks(sp, limit=50):
    """
    Fetch user's recently played tracks.

    Args:
        sp (spotipy.Spotify): Authenticated Spotify client.
        limit (int): Number of tracks to fetch.

    Returns:
        list[dict]: List of track metadata dictionaries.
    """
    results = sp.current_user_recently_played(limit=limit)
    tracks = []
    for item in results["items"]:
        track = item["track"]
        artist_names = [artist["name"] for artist in track["artists"]]
        tracks.append(
            {
                "id": track["id"],
                "name": track["name"],
                "artist_names": artist_names,
                "artist_ids": [artist["id"] for artist in track["artists"]],
                "album_img": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
                "preview_url": track["preview_url"],
                "popularity": track.get("popularity", 0),
            }
        )
    return tracks


def get_artist_info(sp, artist_ids):
    """
    Fetch artist details for a given list of artist IDs.

    Args:
        sp (spotipy.Spotify): Authenticated Spotify client.
        artist_ids (list[str]): List of Spotify artist IDs.

    Returns:
        pd.DataFrame: DataFrame of artist details.
    """
    artists = []
    for i in range(0, len(artist_ids), 50):
        artists.extend(sp.artists(artist_ids[i: i + 50])["artists"])
    return pd.DataFrame(artists)


############################################################
# Recommendation Engine
# Functions to build user profile and recommend tracks based on similarity.
############################################################
# build_user_profile and recommend_custom are now imported from core.recommend


############################################################
# Streamlit UI
# Main dashboard and user interface logic for recommendations and charts.
############################################################
st.markdown('<h1 style="color:#6A0DAD;">🎶 Personalized Music Dashboard</h1>', unsafe_allow_html=True)
# Dashboard introduction
st.write("Discover track recommendations dynamically computed from your recent Spotify listening data.")

if "sp" not in st.session_state:
    # Connect to Spotify and cache client in session state
    with st.spinner("Connecting to Spotify..."):
        try:
            st.session_state.sp = get_spotify_client()
            st.success("Successfully connected to Spotify!")
        except Exception as e:
            st.error(f"Error connecting to Spotify: {e}")
            st.info("Please check your Spotify credentials and try again.")
            st.stop()
sp = st.session_state.sp

############################################################
# Sidebar: User controls for recommendations and filtering
############################################################
with st.sidebar:
    st.markdown("<h3>Settings</h3>", unsafe_allow_html=True)
    num_recs = st.slider("Number of recommendations", 5, 20, 10)
    min_pop = st.slider("Minimum artist popularity", 0, 100, 30)
    st.markdown(
        "<small style='color:gray;'>Adjust sliders to tweak the recommendations.</small>",
        unsafe_allow_html=True,
    )

############################################################
# Data Fetching: Get recent tracks and artist info from Spotify
############################################################
recent_tracks = get_recent_tracks(sp)
artist_ids = list({aid for track in recent_tracks for aid in track["artist_ids"]})
artist_df = get_artist_info(sp, artist_ids)

############################################################
# Overview Metrics: Display summary statistics for user's listening data
############################################################
st.markdown("## Listening Overview")
col1, col2, col3 = st.columns(3)
col1.metric("Tracks Analyzed", len(recent_tracks))
col2.metric("Unique Artists", len(artist_ids))
col3.metric("Avg Artist Popularity", f"{np.round(np.mean(artist_df['popularity']), 2)}")

############################################################
# Artist Popularity Bubble Chart: Visualizes artist popularity
############################################################
artist_pop_df = pd.DataFrame({
    "Artist": artist_df["name"],
    "Popularity": artist_df["popularity"]
})

bubble_chart = alt.Chart(artist_pop_df).mark_circle().encode(
   x=alt.X("Artist", sort=None, title="Artist", axis=alt.Axis(labelAngle=0, labelFontSize=15, titleColor="#6A0DAD", titleFontWeight="bold")),
    y=alt.Y("Popularity", title="Popularity", axis=alt.Axis(labelFontSize=15, titleColor="#6A0DAD", titleFontWeight="bold")),
    size="Popularity",
    color=alt.Color("Popularity", scale=alt.Scale(scheme="plasma")),
    tooltip=["Artist", "Popularity"]
   ).properties(width=1600, height=400, title="Artist Popularity Bubble Chart")

st.altair_chart(bubble_chart, use_container_width=True)

############################################################
# Recommendations: Display recommended tracks in rows with images and audio previews
############################################################
if st.button("Generate Recommendations"):
    with st.spinner("Finding the best tracks for you..."):
        user_profile = build_user_profile(recent_tracks, artist_df)
        recommendations = recommend_custom(
            user_profile, recent_tracks, artist_df, top_n=num_recs, min_popularity=min_pop
        )

    st.markdown(f"## Top {len(recommendations)} Recommended Tracks")
    tracks_per_row = 3
    for i in range(0, len(recommendations), tracks_per_row):
        row_tracks = recommendations[i:i + tracks_per_row]
        cols = st.columns(len(row_tracks))
        for col, rec in zip(cols, row_tracks):
            with col:
                st.markdown(
                    f"""
                    <div class="track-container">
                        <h3 class="track-title">{rec['name']}</h3>
                        <div class="track-artist">by {rec['artist']}</div>
                        {f'<img src="{rec["album_img"]}" style="max-width:150px;">' if rec.get("album_img") else ''}
                        {f'<audio controls src="{rec["preview_url"]}"></audio>' if rec.get("preview_url") else ''}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )