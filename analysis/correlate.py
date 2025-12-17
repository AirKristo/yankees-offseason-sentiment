"""
Correlation analysis between sentiment and odds movement.
"""
import argparse

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

from storage import Article, SentimentScore, OddsSnapshot, get_session, init_db

class CorrelationAnalyzer:
    # Analyze relationships between sentiment and odds.

    def __init__(self):
        self.session = None

    def _get_session(self):
        if self.session is None:
            init_db()
            self.session = get_session()
        return self.session

    def get_sentiment_timeseries(self) -> pd.DataFrame:
        """
        Get daily aggregated sentiment scores.

        Returns DataFrame with date index and mean sentiment score columns.

        """

        from sqlalchemy import select

        session = self._get_session()

        stmt = (
            select(
                    Article.published_at,
                    SentimentScore.positive,
                    SentimentScore.negative,
                    SentimentScore.neutral,
                    SentimentScore.compound,
            )
        .join(SentimentScore)
        )

        results = session.execute(stmt).fetchall()

        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results, columns=[
            "published_at", "positive", "negative", "neutral", "compound"
        ])

        # Convert to date and aggregate
        df["date"] = pd.to_datetime(df["published_at"]).dt.date
        daily = df.groupby("date").agg({
            "positive": "mean",
            "negative": "mean",
            "neutral": "mean",
            "compound": "mean",
        }).reset_index()

        daily["article_count"] = df.groupby("date").size().values
        return daily

    def get_odds_timeseries(self, bookmaker: Optional[str] = None) -> pd.DataFrame:
        """
        Get odds snapshot over time.

        Args:
            bookmaker: Optional filter for specific bookmaker

        Returns DataFrame with snapshot times and odds values.
        """
        from sqlalchemy import select

        session = self._get_session()

        stmt = select(
            OddsSnapshot.snapshot_at,
            OddsSnapshot.bookmaker,
            OddsSnapshot.american_odds,
            OddsSnapshot.implied_probability,
        )

        if bookmaker:
            stmt = stmt.where(OddsSnapshot.bookmaker == bookmaker)

        results = session.execute(stmt).fetchall()

        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results, columns=[
            "snapshot_at", "bookmaker", "american_odds", "implied_probability"
        ])

        df["date"] = pd.to_datetime(df["snapshot_at"]).dt.date

        return df

    def calculate_correlation(
            self,
            sentiment_col: str = "compound",
            odds_col: str = "implied_probability",
            lag_days: int = 0,
    ) -> dict:
        """
        Calculate correlation between sentiment and odds.

        Args:
            sentiment_col: Which sentiment metric to use
            odds_col: Which odds metric to use
            lag_days: Days to lag sentiment (positive = sentiment leads odds)

        Returns dict with correlation stats.
        """

        sentiment_df = self.get_sentiment_timeseries()
        odds_df = self.get_odds_timeseries()

        if sentiment_df.empty or odds_df.empty:
            return {"error": "Insufficient data"}

        # Aggregate odds by date (average across bookmakers)
        odds_daily = odds_df.groupby("date").agg({
            "american_odds": "mean",
            "implied_probability": "mean",
        }).reset_index()

        # Merge on date
        merged = pd.merge(
            sentiment_df,
            odds_daily,
            on="date",
            how="inner",
        )

        if len(merged) < 3:
            return {"error": "Not enough overlapping data points", "n": len(merged)}

        # Apply lag if specified
        if lag_days != 0:
            merged[sentiment_col] = merged[sentiment_col].shift(lag_days)
            merged = merged.dropna()

        if len(merged) < 3:
            return {"error": "Not enough data points after lag adjustment"}

        correlations = merged[sentiment_col].corr(merged[odds_col])

        return {
            "correlations": correlations,
            "n_observations": len(merged),
            "sentiment_metric": sentiment_col,
            "odds_metric": odds_col,
            "lag_days": lag_days,
            "date_range": {
                "start": str(merged["date"].min()),
                "end": str(merged["date"].max()),
            },
        }

    def generate_report(self) -> str:
        #Generate a summary report of the analysis

        sentiment_df = self.get_sentiment_timeseries()
        odds_df = self.get_odds_timeseries()

        lines = [
            "=" * 50,
            "Yankees Offseason Sentiment Analysis Report",
            "=" * 50,
            "",
        ]

        # Sentiment summary
        lines.append("SENTIMENT SUMMARY")
        lines.append("-" * 30)

        if not sentiment_df.empty:
            lines.append(f"Total articles analyzed: {sentiment_df['article_count'].sum()}")
            lines.append(f"Date range: {sentiment_df['date'].min()} to {sentiment_df['date'].max()}")
            lines.append(f"Average compound sentiment: {sentiment_df['compound'].mean():.3f}")
            lines.append(f"Sentiment std dev: {sentiment_df['compound'].std():.3f}")
        else:
            lines.append("No sentiment data available")

        lines.append("")

        #Odds summary
        lines.append("ODDS SUMMARY")
        lines.append("-" * 30)
        if not odds_df.empty:
            lines.append(f"Total snapshots: {len(odds_df)}")
            lines.append(f"Bookmakers tracked: {odds_df['bookmaker'].nunique()}")
            lines.append(f"Latest odds: {odds_df['american_odds'].iloc[-1]:+.0f}")
            lines.append(
                f"Implied probability range: {odds_df['implied_probability'].min():.1%} - {odds_df['implied_probability'].max():.1%}")
        else:
            lines.append("No odds data available.")

        lines.append("")

        # Correlation
        lines.append("CORRELATION ANALYSIS")
        lines.append("-" * 30)
        corr_result = self.calculate_correlation()
        if "error" in corr_result:
            lines.append(f"Could not calculate: {corr_result['error']}")
        else:
            lines.append(f"Sentiment-Odds Correlation: {corr_result['correlation']:.3f}")
            lines.append(f"Based on {corr_result['n_observations']} observations")

        return "\n".join(lines)

def main():
    #CLI entry point for correlation analysis.

    analyzer = CorrelationAnalyzer()
    print(analyzer.generate_report())

if __name__ == "__main__":
    main()
