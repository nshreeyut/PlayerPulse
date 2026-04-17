"""NLP Agent — sentiment analysis and summarization on game reviews.

Orchestrates the NLP pipeline on review batches using RoBERTa for
sentiment scoring and get_llm() for GPT-style summaries.

TODO (future sprint):
  - process_reviews(reviews, game_name) → SentimentSummary
  - Wraps src/playerpulse/features/text_features.py functions
  - Called by POST /api/v1/ingest/reviews
"""

from api.config import get_llm


def process_reviews(reviews: list[dict], game_name: str) -> dict:
    """Run full NLP pipeline on a batch of reviews.

    Args:
        reviews: List of review dicts with 'text', 'author', 'timestamp'
        game_name: Name of the game (used in GPT summary prompt)

    Returns:
        Dict with sentiment_scores, keywords, summary, per_player_sentiment

    TODO: implement using text_features.py once that module is built.
    """
    raise NotImplementedError(
        "TODO (future sprint): implement NLP pipeline. "
        "Use score_sentiment() from text_features.py for RoBERTa inference, "
        "then get_llm() for the summary. "
        "See notebooks/01_review_text_analysis.ipynb for the reference implementation."
    )
