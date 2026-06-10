from googleapiclient.discovery import build
import pandas as pd
import time
import os
from config import YOUTUBE_API_KEY, RAW_DIR


class YouTubeCollector:
    def __init__(self):
        self.youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        os.makedirs(RAW_DIR, exist_ok=True)

    def search_music_videos(self, query, max_results=50):
        videos = []
        next_page = None
        while len(videos) < max_results:
            request = self.youtube.search().list(
                q=query, part="snippet", type="video",
                videoCategoryId="10", maxResults=min(50, max_results - len(videos)),
                order="viewCount", pageToken=next_page
            )
            response = request.execute()
            for item in response["items"]:
                videos.append({
                    "video_id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "channel_title": item["snippet"]["channelTitle"],
                    "channel_id": item["snippet"]["channelId"],
                    "published_at": item["snippet"]["publishedAt"],
                    "description": item["snippet"].get("description", ""),
                    "search_query": query
                })
            next_page = response.get("nextPageToken")
            if not next_page:
                break
            time.sleep(0.5)
        return pd.DataFrame(videos)

    def get_video_stats(self, video_ids):
        stats = []
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i+50]
            request = self.youtube.videos().list(
                part="statistics,contentDetails", id=",".join(batch)
            )
            response = request.execute()
            for item in response["items"]:
                s = item.get("statistics", {})
                stats.append({
                    "video_id": item["id"],
                    "view_count": int(s.get("viewCount", 0)),
                    "like_count": int(s.get("likeCount", 0)),
                    "comment_count": int(s.get("commentCount", 0)),
                    "duration": item["contentDetails"]["duration"]
                })
            time.sleep(0.5)
        return pd.DataFrame(stats)

    def get_video_comments(self, video_id, max_comments=100):
        comments = []
        try:
            request = self.youtube.commentThreads().list(
                part="snippet", videoId=video_id,
                maxResults=min(100, max_comments),
                order="relevance", textFormat="plainText"
            )
            response = request.execute()
            for item in response["items"]:
                comment = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "video_id": video_id,
                    "comment_id": item["id"],
                    "author": comment["authorDisplayName"],
                    "text": comment["textDisplay"],
                    "like_count": comment["likeCount"],
                    "published_at": comment["publishedAt"],
                    "updated_at": comment["updatedAt"]
                })
        except Exception as e:
            print(f"  Comments disabled or error for {video_id}: {e}")
        return pd.DataFrame(comments)

    def collect_all(self):
        print("=" * 50)
        print("YOUTUBE DATA COLLECTION")
        print("=" * 50)

        search_queries = [
            "official music video 2025", "official music video 2024",
            "top hits music video", "hip hop music video", "pop music video",
            "latin music video", "k-pop music video", "rock music video",
            "country music video", "r&b music video"
        ]

        print("\n[1/3] Searching music videos...")
        all_videos = []
        for query in search_queries:
            print(f"  Searching: {query}")
            videos = self.search_music_videos(query, max_results=30)
            all_videos.append(videos)
            time.sleep(1)

        videos_df = pd.concat(all_videos, ignore_index=True).drop_duplicates(subset=["video_id"])
        videos_df.to_csv(os.path.join(RAW_DIR, "youtube_videos.csv"), index=False)
        print(f"  Found {len(videos_df)} unique videos")

        print("\n[2/3] Fetching video statistics...")
        stats = self.get_video_stats(videos_df["video_id"].tolist())
        stats.to_csv(os.path.join(RAW_DIR, "youtube_stats.csv"), index=False)
        print(f"  Got stats for {len(stats)} videos")

        print("\n[3/3] Collecting comments...")
        merged = videos_df.merge(stats, on="video_id")
        top_videos = merged.nlargest(100, "view_count")
        all_comments = []
        for _, row in top_videos.iterrows():
            comments = self.get_video_comments(row["video_id"], max_comments=50)
            if not comments.empty:
                all_comments.append(comments)
            time.sleep(0.5)

        if all_comments:
            comments_df = pd.concat(all_comments, ignore_index=True)
            comments_df.to_csv(os.path.join(RAW_DIR, "youtube_comments.csv"), index=False)
            print(f"  Collected {len(comments_df)} comments")

        print("\nYouTube collection complete!")
        return videos_df, stats


if __name__ == "__main__":
    collector = YouTubeCollector()
    collector.collect_all()
