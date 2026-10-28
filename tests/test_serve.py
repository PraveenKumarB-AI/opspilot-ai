"""The production app serves the API under /api and the React app everywhere else."""
import pytest
from fastapi.testclient import TestClient

from api import serve


@pytest.fixture()
def client():
    return TestClient(serve.app)  # conftest.py already points the database at a temp file


def test_api_is_under_api_prefix(client):
    assert client.get("/api/health").status_code == 200


@pytest.mark.skipif(not serve.DIST.exists(), reason="run npm run build first")
def test_deep_link_returns_index_html(client):
    r = client.get("/queue/3")
    assert r.status_code == 200 and "<div id=\"root\">" in r.text


@pytest.mark.skipif(not serve.DIST.exists(), reason="run npm run build first")
def test_path_traversal_is_blocked(client):
    r = client.get("/..%2F..%2Fapi%2Fmain.py")
    assert "FastAPI" not in r.text
