# Yankees Offseason Sentiment Tracker

Looking at the media sentiment around the New York Yankees' 2025-2025 offseason and correlating it with betting odds movement.

## Overview 

This project collects news articles about the Yankees during the offseason, runs sentiment analysis on the coverage, and tracks how sentiment correlates with World Series futures odds. The goal is to see if media sentiment has any predictive or reactive relationship with how bookmakers view the team's chances.

## Features 

- **Odds Collection**: Get World Series odds from 5+ bookmakers using the Odds API
- **News Collection**: Articles about the Yankees from NewsAPI
- **Sentiment Analysis**: Scores articles using a RoBERTa-based transformer model
- **Collection Automation**: GitHub Actions workflow runs daily to gather data
- **Correlation Analysis**: The comparison of sentiment trends with odds movement as the offseason progresses

### Prerequisites 
- Python3.12+
- API keys for [NewsAPI](https://newsapi.org/) and [The Odds API](https://the-odds-api.com/)

### Installation
# Clone the repo
git clone https://github.com/AirKristo/yankees-offseason-sentiment.git
cd yankees-offseason-sentiment

# Create virtual environment
python -m venv venv
source venv/bin/activate (mac)

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

## Usage

### Collect Data
```bash
# Collect current odds
python -c "from data_collection.odds import main; main()"

# Collect recent news articles
python -c "from data_collection.news import main; main()"