"""
Sentiment analysis pipeline using transformer models.
"""

from typing import Optional
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch.nn.functional as F

from config import config
from storage import Article, SentimentScore, get_session, init_db

class SentimentAnalyzer:
    """Sentiment analysis pipeline using transformer models (pretrained)."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or config.SENTIMENT_MODEL
        self._tokenizer = None
        self._model = None

    @property
    def tokenizer(self):
        #Lazy load tokenizer
        if self._tokenizer is None:
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        return self._tokenizer

    @property
    def model(self):
        #Lazy load model
        if self._model is None:
            self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self._model.eval()
        return self._model

    def analyze_text(self, text: str) -> dict:
        """
        Analyze sentiment of a single text

        Return dict with positive, negative, neutral, and compound scores.
        """

        if not text or not text.strip():
            return {"positive": 0.0, "negative": 0.0, "neutral": 1.0, "compound": 0.0}

        # Tokenize and truncate to model max length
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )

        with torch.no_grad():
            outputs = self.model(**inputs)
            scores = F.softmax(outputs.logits, dim=-1)

        negative = scores[0][0].item()
        neutral = scores[0][1].item()
        positive = scores[0][2].item()

        compound = positive - negative

        return {
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "compound": compound,
        }

    def analyze_article(self, article: Article) -> dict:
        """
        Analyze sentiment of a single article.

        Will be combining the title and description for the analysis.
        """

        text_parts = []
        if article.title:
            text_parts.append(article.title)
        if article.description:
            text_parts.append(article.description)

        combined_text = " ".join(text_parts)
        return self.analyze_text(combined_text)

    def analyze_unprocessed_articles(self) -> dict:
        """
        Analyze the articles without a score

        return dict with counts: {"processed": 0, "skipped": 0}
        """

        init_db()
        session = get_session()

        try:
            articles = (
                session.query(Article)
                .outerjoin(SentimentScore)
                .filter(SentimentScore.id.is_(None))
                .all()
            )

            stats = {"processed": 0, "skipped": 0}

            for article in articles:
                try:
                    scores = self.analyze_article(article)

                    sentiment = SentimentScore(
                        article_id=article.id,
                        positive=scores["positive"],
                        negative=scores["negative"],
                        neutral=scores["neutral"],
                        compound=scores["compound"],
                        model_used=self.model_name,
                    )
                    session.add(sentiment)
                    stats["processed"] += 1

                except Exception as e:
                    print(f"Error processing article {article.id}: {e}")
                    stats["skipped"] += 1

            session.commit()
            return stats

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

def main():
    #CLI entry point for sentiment analysis.

    print(f"Loading sentiment model: {config.SENTIMENT_MODEL}")
    analyzer = SentimentAnalyzer()

    print("Analyzing unprocessed articles...")
    try:
        stats = analyzer.analyze_unprocessed_articles()
        print(f"Processed {stats['processed']} articles.")
        if stats["skipped"]:
            print(f"Skipped {stats['skipped']} articles due to errors.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
