# Pulse — Streaming Music Analytics Pipeline

Automated data pipeline that ingests music data from Spotify and YouTube APIs, performs NLP sentiment analysis on listener comments, and surfaces trends through interactive Tableau dashboards.

## Key Findings

- **Pop and Hip Hop dominate** streaming charts with the highest average popularity scores
- **High energy + high danceability** tracks are significantly more likely to achieve viral status (80+ popularity)
- **YouTube comment sentiment** averages positive, with K-Pop videos showing the highest engagement rates
- **Tempo sweet spot**: hits cluster around 100–130 BPM regardless of genre

## Architecture

```
Spotify API + YouTube Data API
        |
        v
   ETL Pipeline (Python)
        |
        v
Processing & Feature Engineering (Pandas, NumPy)
        |
        v
NLP Sentiment Analysis (VADER + TextBlob)
        |
        v
Tableau Public Dashboards
```

## Tech Stack

Python · Spotify API · YouTube Data API · VADER · TextBlob · Pandas · NumPy · Tableau Public

## Setup

```bash
git clone https://github.com/rutvij1407/pulse.git
cd pulse
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys in .env
```

## Running the Pipeline

```bash
cd src
python pipeline.py        # Collect data from both APIs
python processing.py      # Clean & feature engineer
python sentiment_analysis.py  # Run NLP sentiment analysis
```

## API Keys Required

- **Spotify**: [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
- **YouTube**: [console.cloud.google.com](https://console.cloud.google.com)
