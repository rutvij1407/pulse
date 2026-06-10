import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
import nltk
import re
import os
from config import RAW_DIR, PROCESSED_DIR

nltk.download("punkt", quiet=True)
nltk.download("stopwords", quiet=True)
nltk.download("wordnet", quiet=True)


class MusicSentimentAnalyzer:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()

    def clean_text(self, text):
        if pd.isna(text):
            return ""
        text = str(text)
        text = re.sub(r"http\S+|www\.\S+", "", text)
        text = re.sub(r"@\w+", "", text)
        text = re.sub(r"[^\w\s!?.,']", "", text)
        return re.sub(r"\s+", " ", text).strip()

    def analyze_vader(self, text):
        scores = self.vader.polarity_scores(text)
        return {
            "vader_compound": scores["compound"],
            "vader_positive": scores["pos"],
            "vader_negative": scores["neg"],
            "vader_neutral": scores["neu"]
        }

    def analyze_textblob(self, text):
        blob = TextBlob(text)
        return {
            "tb_polarity": blob.sentiment.polarity,
            "tb_subjectivity": blob.sentiment.subjectivity
        }

    def classify_sentiment(self, compound_score):
        if compound_score >= 0.05:
            return "Positive"
        elif compound_score <= -0.05:
            return "Negative"
        return "Neutral"

    def process_comments(self):
        comments_path = os.path.join(RAW_DIR, "youtube_comments.csv")
        if not os.path.exists(comments_path):
            print("No comments file found. Run youtube_collector first.")
            return pd.DataFrame()

        comments = pd.read_csv(comments_path)
        print(f"Processing {len(comments)} comments...")

        comments["clean_text"] = comments["text"].apply(self.clean_text)
        comments = comments[comments["clean_text"].str.len() > 5]

        vader_results = comments["clean_text"].apply(
            lambda x: pd.Series(self.analyze_vader(x))
        )
        comments = pd.concat([comments, vader_results], axis=1)

        tb_results = comments["clean_text"].apply(
            lambda x: pd.Series(self.analyze_textblob(x))
        )
        comments = pd.concat([comments, tb_results], axis=1)

        comments["ensemble_score"] = (comments["vader_compound"] + comments["tb_polarity"]) / 2
        comments["sentiment"] = comments["vader_compound"].apply(self.classify_sentiment)
        comments["vader_label"] = comments["vader_compound"].apply(self.classify_sentiment)
        comments["tb_label"] = comments["tb_polarity"].apply(
            lambda x: "Positive" if x > 0.1 else ("Negative" if x < -0.1 else "Neutral")
        )
        comments["models_agree"] = comments["vader_label"] == comments["tb_label"]
        comments["word_count"] = comments["clean_text"].str.split().str.len()

        output_path = os.path.join(PROCESSED_DIR, "comments_sentiment.csv")
        comments.to_csv(output_path, index=False)

        print(f"\nSentiment Distribution:\n{comments['sentiment'].value_counts()}")
        print(f"\nAverage Compound Score: {comments['vader_compound'].mean():.4f}")
        print(f"Model Agreement Rate: {comments['models_agree'].mean():.1%}")

        return comments

    def aggregate_by_video(self, comments):
        video_sentiment = comments.groupby("video_id").agg(
            avg_sentiment=("vader_compound", "mean"),
            median_sentiment=("vader_compound", "median"),
            std_sentiment=("vader_compound", "std"),
            positive_pct=("sentiment", lambda x: (x == "Positive").mean()),
            negative_pct=("sentiment", lambda x: (x == "Negative").mean()),
            neutral_pct=("sentiment", lambda x: (x == "Neutral").mean()),
            total_comments=("comment_id", "count"),
            avg_comment_likes=("like_count", "mean"),
            avg_word_count=("word_count", "mean"),
            avg_subjectivity=("tb_subjectivity", "mean")
        ).reset_index()

        output_path = os.path.join(PROCESSED_DIR, "video_sentiment_agg.csv")
        video_sentiment.to_csv(output_path, index=False)
        print(f"\nAggregated sentiment for {len(video_sentiment)} videos")
        return video_sentiment


if __name__ == "__main__":
    analyzer = MusicSentimentAnalyzer()
    comments = analyzer.process_comments()
    if not comments.empty:
        analyzer.aggregate_by_video(comments)
