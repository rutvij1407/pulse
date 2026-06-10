import time
from datetime import datetime
from spotify_collector import SpotifyCollector
from youtube_collector import YouTubeCollector


def run_pipeline():
    start = datetime.now()
    print(f"Pipeline started at {start.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    SpotifyCollector().collect_all()
    time.sleep(2)
    YouTubeCollector().collect_all()

    elapsed = datetime.now() - start
    print(f"\nPipeline complete! Duration: {elapsed}")


if __name__ == "__main__":
    run_pipeline()
