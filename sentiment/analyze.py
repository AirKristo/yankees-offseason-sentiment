"""
Sentiment analysis pipeline using transformer models.
"""

from datetime import datetime, timezone
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