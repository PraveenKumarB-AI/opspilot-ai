"""Test settings: fallback mode, TF-IDF embeddings, throwaway database. Free and repeatable."""
import os
import tempfile

os.environ["OPSPILOT_MODE"] = "fallback"
os.environ["OPSPILOT_EMBEDDINGS"] = "tfidf"
os.environ["OPSPILOT_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")

import pytest  # noqa: E402

from opspilot import db  # noqa: E402


@pytest.fixture
def conn():
    """A fresh in-memory database for each test."""
    c = db.connect(":memory:")
    yield c
    c.close()
