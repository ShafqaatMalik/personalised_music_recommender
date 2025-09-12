import numpy as np
import pandas as pd

from core.recommend import build_user_profile, recommend_custom


def sample_data():
    recent_tracks = [
        {
            "id": "t1",
            "name": "Track 1",
            "artist_names": ["A1"],
            "artist_ids": ["a1"],
            "album_img": None,
            "preview_url": None,
            "popularity": 50,
        },
        {
            "id": "t2",
            "name": "Track 2",
            "artist_names": ["A2"],
            "artist_ids": ["a2"],
            "album_img": None,
            "preview_url": None,
            "popularity": 70,
        },
        {
            "id": "t3",
            "name": "Track 3",
            "artist_names": ["A1", "A3"],
            "artist_ids": ["a1", "a3"],
            "album_img": None,
            "preview_url": None,
            "popularity": 40,
        },
    ]

    artist_df = pd.DataFrame(
        [
            {"id": "a1", "name": "A1", "popularity": 60},
            {"id": "a2", "name": "A2", "popularity": 30},
            {"id": "a3", "name": "A3", "popularity": 90},
        ]
    )
    return recent_tracks, artist_df


def test_build_user_profile_returns_means():
    recent_tracks, artist_df = sample_data()
    profile = build_user_profile(recent_tracks, artist_df)
    assert isinstance(profile, np.ndarray)
    # track popularity mean = (50 + 70 + 40)/3 = 160/3
    # artist avg per track: [60] , [30], [ (60+90)/2 = 75 ] => mean = (60 + 30 + 75)/3 = 165/3
    assert np.isclose(profile[0], 160 / 3)
    assert np.isclose(profile[1], 165 / 3)


def test_build_user_profile_empty():
    artist_df = pd.DataFrame([{"id": "a1", "name": "A1", "popularity": 60}])
    profile = build_user_profile([], artist_df)
    assert np.allclose(profile, np.array([0.0, 0.0]))


def test_recommend_custom_filters_by_min_popularity():
    recent_tracks, artist_df = sample_data()
    profile = build_user_profile(recent_tracks, artist_df)
    recs = recommend_custom(profile, recent_tracks, artist_df, top_n=10, min_popularity=61)
    # Only tracks whose average artist popularity >= 61 should pass
    # t1: a1=60 -> 60 (filtered out); t2: a2=30 -> 30 (filtered out); t3: a1,a3 -> 75 (kept)
    assert {r["name"] for r in recs} == {"Track 3"}


def test_recommend_custom_enforces_uniqueness_and_limit():
    recent_tracks, artist_df = sample_data()
    profile = build_user_profile(recent_tracks, artist_df)
    recs = recommend_custom(profile, recent_tracks, artist_df, top_n=2, min_popularity=0)
    assert len(recs) == 2
    # Ensure unique track ids mapped to names
    assert len({r["name"] for r in recs}) == 2
