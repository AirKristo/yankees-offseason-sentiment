"""
Configuration managment for the project.
Loads settings from environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

#Load .env file from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

class Config:
    #Central configuration class.

    # API Keys
    NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
    ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")

    # Database
    DATABASE_PATH: Path = PROJECT_ROOT / os.getenv("DATABASE_PATH", "data/yankees_sentiment.db")

    # News collection settings
    NEWS_LOOKBACK_DAYS: int = int(os.getenv("NEWS_LOOKBACK_DAYS", 7))

    # Odds API settings
    ODDS_SPORT: str = "baseball_mlb_world_series_winner"
    ODDS_MARKET: str = "outrights" # For futures/championship odds

    # Sentiment model
    SENTIMENT_MODEL: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"

    @classmethod
    def validate(cls) -> list[str]:
        """Check for missing required configuartion. Return list of missing items."""
        missing = []
        if not cls.NEWS_API_KEY:
            missing.append("NEWS_API_KEY")
        if not cls.ODDS_API_KEY:
            missing.append("ODDS_API_KEY")
        return missing

config = Config()
