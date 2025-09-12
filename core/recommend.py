import numpy as np
import pandas as pd
from typing import List, Dict


def build_user_profile(recent_tracks: List[Dict], artist_df: pd.DataFrame) -> np.ndarray:
    """
    Create a user profile based on track and artist popularity.

    Args:
        recent_tracks (list[dict]): List of track metadata.
        artist_df (pd.DataFrame): DataFrame of artist details.

    Returns:
        np.ndarray: Array of average track and artist popularity.
    """
    if not recent_tracks:
        return np.array([0.0, 0.0])

    track_pops = [t.get("popularity", 0) for t in recent_tracks]
    avg_artist_pops = []

    for track in recent_tracks:
        pops = [
            artist_df.loc[artist_df["id"] == aid, "popularity"].values[0]
            for aid in track.get("artist_ids", [])
            if aid in artist_df["id"].values
        ]
        avg_artist_pops.append(float(np.mean(pops)) if pops else 0.0)

    return np.array([float(np.mean(track_pops)), float(np.mean(avg_artist_pops))])


def recommend_custom(
    user_profile: np.ndarray,
    recent_tracks: List[Dict],
    artist_df: pd.DataFrame,
    top_n: int = 10,
    min_popularity: int = 0,
) -> List[Dict]:
    """
    Recommend tracks based on similarity to user profile.

    Args:
        user_profile (np.ndarray): User profile features.
        recent_tracks (list[dict]): List of track metadata.
        artist_df (pd.DataFrame): DataFrame of artist details.
        top_n (int): Number of recommendations to return.
        min_popularity (int): Minimum average artist popularity.

    Returns:
        list[dict]: List of recommended track dictionaries.
    """
    if user_profile is None or len(user_profile) != 2:
        return []

    scored_tracks = []
    for track in recent_tracks or []:
        track_pop = track.get("popularity", 0)
        artist_pops = [
            artist_df.loc[artist_df["id"] == aid, "popularity"].values[0]
            for aid in track.get("artist_ids", [])
            if aid in artist_df["id"].values
        ]
        avg_artist_pop = float(np.mean(artist_pops)) if artist_pops else 0.0
        track_vector = np.array([float(track_pop), avg_artist_pop])
        # Similarity as inverse of Euclidean distance to profile
        sim = 1 - float(np.linalg.norm(user_profile - track_vector))
        scored_tracks.append((track, sim, avg_artist_pop))

    # Sort by similarity descending
    scored_tracks.sort(key=lambda x: x[1], reverse=True)

    recommendations: List[Dict] = []
    seen_ids = set()
    for track, score, avg_artist_pop in scored_tracks:
        if avg_artist_pop < min_popularity:
            continue
        tid = track.get("id")
        if tid and tid not in seen_ids:
            recommendations.append(
                {
                    "name": track.get("name"),
                    "artist": ", ".join(track.get("artist_names", [])),
                    "album_img": track.get("album_img"),
                    "preview_url": track.get("preview_url"),
                }
            )
            seen_ids.add(tid)
        if len(recommendations) >= top_n:
            break

    return recommendations
