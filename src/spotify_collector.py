import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import time
import os
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, RAW_DIR


class SpotifyCollector:
    def __init__(self):
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET
            ),
            requests_timeout=10,
            retries=3
        )
        os.makedirs(RAW_DIR, exist_ok=True)

    def get_playlist_tracks(self, playlist_id, playlist_name=""):
        tracks = []
        results = self.sp.playlist_tracks(playlist_id)
        while results:
            for item in results["items"]:
                track = item.get("track")
                if track and track.get("id"):
                    tracks.append({
                        "track_id": track["id"],
                        "track_name": track["name"],
                        "artist_name": track["artists"][0]["name"],
                        "artist_id": track["artists"][0]["id"],
                        "album_name": track["album"]["name"],
                        "album_id": track["album"]["id"],
                        "release_date": track["album"].get("release_date", ""),
                        "duration_ms": track["duration_ms"],
                        "popularity": track["popularity"],
                        "explicit": track["explicit"],
                        "playlist_id": playlist_id,
                        "playlist_name": playlist_name,
                        "added_at": item.get("added_at", "")
                    })
            results = self.sp.next(results) if results["next"] else None
        return pd.DataFrame(tracks)

    def get_audio_features(self, track_ids):
        all_features = []
        for i in range(0, len(track_ids), 100):
            batch = track_ids[i:i+100]
            features = self.sp.audio_features(batch)
            for feat in features:
                if feat:
                    all_features.append({
                        "track_id": feat["id"],
                        "danceability": feat["danceability"],
                        "energy": feat["energy"],
                        "key": feat["key"],
                        "loudness": feat["loudness"],
                        "mode": feat["mode"],
                        "speechiness": feat["speechiness"],
                        "acousticness": feat["acousticness"],
                        "instrumentalness": feat["instrumentalness"],
                        "liveness": feat["liveness"],
                        "valence": feat["valence"],
                        "tempo": feat["tempo"],
                        "time_signature": feat["time_signature"]
                    })
            time.sleep(0.5)
        return pd.DataFrame(all_features)

    def get_artist_info(self, artist_ids):
        unique_ids = list(set(artist_ids))
        all_artists = []
        for i in range(0, len(unique_ids), 50):
            batch = unique_ids[i:i+50]
            results = self.sp.artists(batch)
            for artist in results["artists"]:
                if artist:
                    all_artists.append({
                        "artist_id": artist["id"],
                        "artist_name": artist["name"],
                        "genres": ", ".join(artist.get("genres", [])),
                        "followers": artist["followers"]["total"],
                        "popularity": artist["popularity"],
                        "image_url": artist["images"][0]["url"] if artist["images"] else ""
                    })
            time.sleep(0.5)
        return pd.DataFrame(all_artists)

    def get_top_charts(self):
        chart_playlists = {
            "Today's Top Hits": "37i9dQZF1DXcBWIGoYBM5M",
            "Global Top 50": "37i9dQZEVXbMDoHDwVN2tF",
            "US Top 50": "37i9dQZEVXbLRQDuF5jeBp",
            "Viral 50 Global": "37i9dQZEVXbLiRSasKsNU9",
            "Hot Hits USA": "37i9dQZF1DX0kbJZpiYdZl",
            "Pop Rising": "37i9dQZF1DWUa8ZRTfalHk",
            "Rap Caviar": "37i9dQZF1DX0XUsuxWHRQd",
            "Rock This": "37i9dQZF1DXcF6B6QPhFDv",
            "Viva Latino": "37i9dQZF1DX10zKzsJ2jva",
            "Hot Country": "37i9dQZF1DX1lVhptIYRda"
        }
        all_tracks = []
        for name, playlist_id in chart_playlists.items():
            print(f"Fetching: {name}")
            try:
                tracks = self.get_playlist_tracks(playlist_id, name)
                all_tracks.append(tracks)
                time.sleep(1)
            except Exception as e:
                print(f"Error with {name}: {e}")
        return pd.concat(all_tracks, ignore_index=True)

    def collect_all(self):
        print("=" * 50)
        print("SPOTIFY DATA COLLECTION")
        print("=" * 50)

        print("\n[1/3] Collecting top chart tracks...")
        charts = self.get_top_charts()
        charts.to_csv(os.path.join(RAW_DIR, "spotify_charts.csv"), index=False)
        print(f"  Collected {len(charts)} chart tracks")

        print("\n[2/3] Collecting audio features...")
        track_ids = charts["track_id"].unique().tolist()
        features = self.get_audio_features(track_ids)
        features.to_csv(os.path.join(RAW_DIR, "spotify_audio_features.csv"), index=False)
        print(f"  Collected features for {len(features)} tracks")

        print("\n[3/3] Collecting artist info...")
        artist_ids = charts["artist_id"].unique().tolist()
        artists = self.get_artist_info(artist_ids)
        artists.to_csv(os.path.join(RAW_DIR, "spotify_artists.csv"), index=False)
        print(f"  Collected info for {len(artists)} artists")

        print("\nSpotify collection complete!")
        return charts, features, artists


if __name__ == "__main__":
    collector = SpotifyCollector()
    collector.collect_all()
