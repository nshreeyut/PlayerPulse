"""Text feature engineering — NLP pipeline for game reviews.

Productionizes the notebook at notebooks/01_review_text_analysis.ipynb
into callable functions used by the NLP agent.

Model: cardiffnlp/twitter-roberta-base-sentiment-latest (RoBERTa)
Summary: get_llm() from api/config.py

TODO (future sprint):
  - clean_text(raw) → str
  - score_sentiment(texts) → list[dict]
  - extract_keywords(texts) → list[str]
  - summarize_reviews(texts, game_name) → str
  - build_sentiment_features(reviews) → pl.DataFrame

Installation:
    uv pip install -e ".[nlp]"   # adds transformers, torch, openai
"""

from __future__ import annotations
import polars as pl


SENTIMENT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"


def clean_text(raw: str) -> str:
    """Strip HTML tags, normalize whitespace, truncate to model max length.

    TODO: implement. See notebook cell 3 for reference.
    """
    raise NotImplementedError("TODO: implement HTML cleaning and text normalization")


def score_sentiment(texts: list[str]) -> list[dict]:
    """Run RoBERTa batch inference on cleaned review texts.

    Returns:
        List of dicts: {label: 'positive'|'neutral'|'negative', score: float}

    TODO: implement using transformers pipeline.
    Batch size 32 works well on CPU. Use truncation=True.
    """
    raise NotImplementedError("TODO: implement RoBERTa sentiment scoring")


def extract_keywords(texts: list[str]) -> list[str]:
    """Extract top complaint/praise keywords from review corpus.

    TODO: implement using KeyBERT or simple TF-IDF.
    See notebook for reference implementation.
    """
    raise NotImplementedError("TODO: implement keyword extraction")


def summarize_reviews(texts: list[str], game_name: str) -> str:
    """Generate a plain-English summary of player sentiment using LLM.

    Uses get_llm() from api/config.py — provider swappable via env var.

    TODO: implement. Sample prompt in notebook cell 8.
    """
    raise NotImplementedError("TODO: implement LLM summary via get_llm()")


def build_sentiment_features(reviews: list[dict]) -> pl.DataFrame:
    """Aggregate per-review sentiment into per-player/game features.

    Returns:
        Polars DataFrame with: player_id, avg_sentiment, pct_negative,
        top_keywords, review_count

    TODO: implement aggregation logic.
    """
    raise NotImplementedError("TODO: implement sentiment feature aggregation")
