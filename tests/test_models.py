"""Tests for model training pipeline."""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from playerpulse.models.synthetic import generate_synthetic_data
from playerpulse.models.train import FEATURE_COLS, TARGET_COL, prepare_data


def test_synthetic_data_shape() -> None:
    """Test synthetic data has expected shape and columns."""
    df = generate_synthetic_data(n_players=100)
    assert len(df) == 100
    assert TARGET_COL in df.columns
    for col in FEATURE_COLS:
        assert col in df.columns, f"Missing column: {col}"


def test_synthetic_data_churn_ratio() -> None:
    """Test synthetic data has approximately 30% churn rate."""
    df = generate_synthetic_data(n_players=1000)
    churn_rate = df[TARGET_COL].mean()
    assert 0.25 <= churn_rate <= 0.35


def test_prepare_data_splits() -> None:
    """Test data preparation produces correct splits."""
    df = generate_synthetic_data(n_players=200)
    X_train, X_test, y_train, y_test, feature_names = prepare_data(df)

    assert len(X_train) + len(X_test) == 200
    assert len(y_train) == len(X_train)
    assert len(y_test) == len(X_test)
    assert len(feature_names) > 0


def test_logistic_regression_trains() -> None:
    """Test that logistic regression can train on synthetic data."""
    df = generate_synthetic_data(n_players=500)
    X_train, X_test, y_train, y_test, _ = prepare_data(df)

    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X_train, y_train)

    y_proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_proba)

    # Should do better than random (0.5) on synthetic data
    assert auc > 0.7, f"AUC too low: {auc}"


def test_no_nulls_in_features() -> None:
    """Test that feature data has no nulls after preparation."""
    df = generate_synthetic_data(n_players=200)
    X_train, X_test, _, _, _ = prepare_data(df)

    assert not np.isnan(X_train).any()
    assert not np.isnan(X_test).any()
