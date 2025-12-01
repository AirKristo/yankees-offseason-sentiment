"""
Database models for storing articles, odds, and sentiment scores.
"""

from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from pathlib import Path

from config import config

Base = declarative_base()

class Article(Base):
    """News articles about the Yankees."""
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True)
    source = Column(String(100))
    author = Column(String(200), nullable=True)
    title = Column(String(500))
    description = Column(Text, nullable=True)
    url = Column(String(1000), nullable=True)
    published_at = Column(DateTime(timezone=True))
    collected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationship to sentiment
    sentiment = relationship("SentimentScore", back_populates="article", uselist=False)

    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:50]}...')>"


class SentimentScore(Base):
    """Sentiment analysis results for an article."""
    __tablename__ = 'sentiment_scores'

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('articles.id'), unique=True)

    # Sentiment scores that are -1 to 1 or 0 to 1 depends on model
    positive = Column(Float)
    negative = Column(Float)
    neutral = Column(Float)
    compound = Column(Float, nullable=True)

    model_used = Column(String(200))
    analyzed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    article = relationship("Article", back_populates="sentiment")

    def __repr__(self):
        return f"<SentimentScore(article_id={self.article_id})>"

class OddsSnapshot(Base):
    """Point-in-time snapshot of Yankees World Series odds."""
    __tablename__ = 'odds_snapshots'

    id = Column(Integer, primary_key=True)
    bookmaker = Column(String(100))
    market = Column(String(50)) # "World Series Winner"

    #Odds in different formats
    american_odds = Column(Integer)
    decimal_odds = Column(Float)
    implied_probability = Column(Float)

    snapshot_at = Column(DateTime(timezone=True))
    collected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<OddsSnapshot(bookmaker={self.bookmaker}, odds={self.american_odds}, at={self.snapshot_at})>"

def get_engine():
    """Create database engine, ensuring directory exists."""

    db_path = config.DATABASE_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f'sqlite:///{db_path}')

def init_db():
    """Initialize the database tables."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    return engine

def get_session():
    """Get a new database session."""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

