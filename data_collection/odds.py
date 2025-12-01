"""
Odds data collection from the odds API
"""

import requests
from datetime import datetime, timezone
from typing import Optional

from config import config
from storage import OddsSnapshot, get_session, init_db

class OddsCollector:
    #Client for the odds API.

    BASE_URL = "https://api.the-odds-api.com/v4"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.ODDS_API_KEY
        if not self.api_key:
            raise ValueError("odds API key not configured")

    def get_championship_odds(self) -> list[dict]:
        """
        Fetch World Series future odds.

        Returns list of odds data for all teams, filter to Yankees.
        """

        url = f"{self.BASE_URL}/sports/{config.ODDS_SPORT}/odds"

        params = {
            "api_key": self.api_key,
            "regions": "us",
            "oddsFormat": "american",
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        return response.json()

    def extract_yankees_odds(self, odds_data: list[dict]) -> list[dict]:
        """
        Extract Yankees-specific odds from the API response.

        Returns list of dicts with bookmaker, odds, and timestamp info.
        """

        yankees_odds = []

        for event in odds_data:
            bookmakers = event.get("bookmakers", [])
            for bookmaker in bookmakers:
                markets = bookmaker.get("markets", [])
                for market in markets:
                    if market.get("key") == "outrights":
                        outcomes = market.get("outcomes", [])
                        for outcome in outcomes:
                            if "yankees" in outcome.get("name", "").lower():
                                yankees_odds.append({
                                    "bookmaker": bookmaker.get("title"),
                                    "market": "World Series Winner",
                                    "team": outcome.get("name"),
                                    "american_odds": outcome.get("price"),
                                    "snapshot_at": datetime.now(timezone.utc),
                                })
        return yankees_odds

    def collect_and_store(self) -> int:
        """"
        Fetch current odds and store in database.

        Returns number of snapshots stored.
        """

        init_db()
        session = get_session()

        try:
            odds_data = self.get_championship_odds()
            yankees_odds = self.extract_yankees_odds(odds_data)

            stored = 0
            for odds in yankees_odds:
                snapshot = OddsSnapshot(
                    bookmaker=odds["bookmaker"],
                    market=odds["market"],
                    american_odds=odds["american_odds"],
                    decimal_odds=self._american_to_decimal(odds["american_odds"]),
                    implied_probability=self._american_to_probability(odds["american_odds"]),
                    snapshot_at=odds["snapshot_at"],
                )
                session.add(snapshot)
                stored += 1
            session.commit()
            return stored

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


    @staticmethod
    def _american_to_decimal(american: int) -> float:
        """Convert American odds to decimal format."""
        if american > 0:
            return (american / 100) + 1
        else:
            return (100 / abs(american)) + 1


    @staticmethod
    def _american_to_probability(american: int) -> float:
        """Convert American odds to implied probability."""
        if american > 0:
            return 100 / (american + 100)
        else:
            return abs(american) / (abs(american) + 100)

def main():
    #CLI entry point for odds collection.

    missing = config.validate()
    if "ODDS_API_KEY" in missing:
        print("Error: ODDS_API_KEY not set. Add it to your .env file.")
        return

    collector = OddsCollector()

    print("Fetching Yankees World series odds...")
    try:
        count = collector.collect_and_store()
        print(f"Stored {count} odds snapshots.")
    except requests.exceptions.HTTPError as e:
        print(f"API error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
