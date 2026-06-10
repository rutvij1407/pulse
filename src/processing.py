import pandas as pd
import numpy as np
import re
import os
from config import RAW_DIR, PROCESSED_DIR


def classify_mood(row):
    valence = row.get("valence", 0.5)
    energy = row.get("energy", 0.5)
    if valence > 0.6 and energy > 0.6:
        return "Happy/Energetic"
    elif valence > 0.6 and energy <= 0.6:
        return "Peaceful/Relaxed"
    elif valence <= 0.4 and energy > 0.6:
        return "Angry/Intense"
    elif valence <= 0.4 and energy <= 0.4:
        return "Sad/Melancholic"
    return "Neutral"


def parse_duration(duration_str):
    if pd.isna(duration_str):
        return 0
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", str(duration_str))
    if match:
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds
    return 0


def process_spotify_data():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    charts = pd.read_csv(os.path.join(RAW_DIR, "spotify_charts.csv"))
    features = pd.read_csv(os.path.join(RAW_DIR, "spotify_audio_features.csv"))
    artists = pd.read_csv(os.path.join(RAW_DIR, "spotify_artists.csv"))

    tracks = charts.merge(features, on="track_id", how="left")
    tracks = tracks.merge(
        artists[["artist_id", "genres", "followers", "popularity"]],
        on="artist_id", how="left", suffixes=("_track", "_artist")
    )

    tracks["release_date"] = pd.to_datetime(tracks["release_date"], errors="coerce")
    tracks["release_year"] = tracks["release_date"].dt.year
    tracks["release_month"] = tracks["release_date"].dt.month
    tracks["duration_min"] = tracks["duration_ms"] / 60000
    tracks["added_at"] = pd.to_datetime(tracks["added_at"], errors="coerce")

    tracks["primary_genre"] = tracks["genres"].apply(
        lambda x: x.split(",")[0].strip() if pd.notna(x) and x else "unknown"
    )

    genre_map = {
        "pop": "Pop", "dance pop": "Pop", "electropop": "Pop",
        "rap": "Hip Hop", "hip hop": "Hip Hop", "trap": "Hip Hop",
        "rock": "Rock", "alternative": "Rock", "indie": "Rock",
        "r&b": "R&B", "soul": "R&B", "neo soul": "R&B",
        "latin": "Latin", "reggaeton": "Latin", "latin pop": "Latin",
        "country": "Country", "country pop": "Country",
        "edm": "Electronic", "house": "Electronic", "techno": "Electronic",
        "k-pop": "K Pop", "j-pop": "J Pop",
        "jazz": "Jazz", "blues": "Blues", "classical": "Classical", "metal": "Metal"
    }
    tracks["genre_group"] = tracks["primary_genre"].str.lower().map(genre_map).fillna("Other")
    tracks["energy_level"] = pd.cut(
        tracks["energy"], bins=[0, 0.33, 0.66, 1.0], labels=["Low", "Medium", "High"]
    )
    tracks["mood"] = tracks.apply(classify_mood, axis=1)
    tracks = tracks.drop_duplicates(subset=["track_id", "playlist_id"])

    tracks.to_csv(os.path.join(PROCESSED_DIR, "spotify_master.csv"), index=False)
    print(f"Spotify master dataset: {len(tracks)} rows, {len(tracks.columns)} columns")
    return tracks


def process_youtube_data():
    videos = pd.read_csv(os.path.join(RAW_DIR, "youtube_videos.csv"))
    stats = pd.read_csv(os.path.join(RAW_DIR, "youtube_stats.csv"))

    yt_master = videos.merge(stats, on="video_id", how="left")
    yt_master["published_at"] = pd.to_datetime(yt_master["published_at"])
    yt_master["publish_year"] = yt_master["published_at"].dt.year
    yt_master["publish_month"] = yt_master["published_at"].dt.month
    yt_master["like_rate"] = (
        yt_master["like_count"] / yt_master["view_count"].replace(0, np.nan) * 100
    )
    yt_master["comment_rate"] = (
        yt_master["comment_count"] / yt_master["view_count"].replace(0, np.nan) * 100
    )
    yt_master["engagement_score"] = yt_master["like_rate"] + yt_master["comment_rate"]
    yt_master["duration_seconds"] = yt_master["duration"].apply(parse_duration)
    yt_master["duration_min"] = yt_master["duration_seconds"] / 60
    yt_master = yt_master.drop_duplicates(subset=["video_id"])

    yt_master.to_csv(os.path.join(PROCESSED_DIR, "youtube_master.csv"), index=False)
    print(f"YouTube master dataset: {len(yt_master)} rows")
    return yt_master


if __name__ == "__main__":
    process_spotify_data()
    process_youtube_data()
    print("\nProcessing complete!")
