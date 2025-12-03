#News article collected from NewsAPI
from http.client import responses

import requests
from datetime import datetime, timedelta, timezone
from typing import Optional

from config import config
from storage import Article, get_session, init_db

class NewsCollector:
    #Client for NewsAPI.

    BASE_URL = "https://newsapi.org/v2"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.NEWS_API_KEY
        if not self.api_key:
            raise ValueError("NEWS_API_KEY not configured")

    def search_yankees_articles(
        self,
        days_back: Optional[int] = None,
        page_size: int = 100,
        ) -> list[dict]:
        """
        Search for Yankees-related articles.
        
            Args:
                days_back: How many days to look back (default from config)
                page_size: Number of articles per request (max 100)
            
            Returns:
                List of article dicts from the API
        """
        days_back = days_back or config.NEWS_LOOKBACK_DAYS
        from_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")

        url = f"{self.BASE_URL}/everything"

        params = {"apiKey": self.api_key,
                  "q": '"New York Yankees" OR "Yankees" AND (baseball OR MLB OR offseason OR trade OR signing)'
                       ' OR "Aaron Judge" OR "Gerrit Cole" OR "Anthony Volpe" OR "Aaron Boone"'
                       ' OR "Hal Steinbrenner"',
                  "from": from_date,
                  "language": "en",
                  "sortBy": "publishedAt",
                  "pageSize": page_size,
                  }

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        return data.get("articles", [])

    def collect_and_store(self, days_back: Optional[int] = None) -> dict:
        """
        Fetch articles and store new ones in database.

        Returns dict with counts: {"fetched": n, "new": m, "duplicates": d}
        """
        init_db()
        session = get_session()

        try:
            articles = self.search_yankees_articles(days_back=days_back)

            stats = {"fetched": len(articles), "new": 0, "duplicates": 0}

            for article_data in articles:
                url = article_data.get("url")
                if not url:
                    continue

                # Check for existing article by URL
                existing = session.query(Article).filter_by(url=url).first()
                if existing:
                    stats["duplicates"] += 1
                    continue

                # Parse published date
                pub_str = article_data.get("publishedAt", "")
                try:
                    published_at = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    published_at = datetime.now(timezone.utc)

                article = Article(
                    source=article_data.get("source", {}).get("name", "Unknown"),
                    author=article_data.get("author"),
                    title=article_data.get("title", ""),
                    description=article_data.get("description"),
                    url=url,
                    published_at=published_at,
                    content=article_data.get("content"),
                )
                session.add(article)
                stats["new"] += 1

            session.commit()
            return stats

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


def main():
    """CLI entry point for news collection."""
    missing = config.validate()
    if "NEWS_API_KEY" in missing:
        print("Error: NEWS_API_KEY not set. Add it to your .env file.")
        return

    collector = NewsCollector()

    print(f"Fetching Yankees articles from the last {config.NEWS_LOOKBACK_DAYS} days...")
    try:
        stats = collector.collect_and_store()
        print(f"Fetched {stats['fetched']} articles.")
        print(f"  New: {stats['new']}")
        print(f"  Duplicates skipped: {stats['duplicates']}")
    except requests.exceptions.HTTPError as e:
        print(f"API error: {e}")
        if e.response is not None:
            print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()