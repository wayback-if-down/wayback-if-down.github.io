from main import app
from flask.testing import FlaskClient
import pytest


@pytest.fixture
def client() -> FlaskClient:
    return app.test_client()


parameterize_url_redirect_url = pytest.mark.parametrize("url, redirect_url", [
    ("https://example.com", "https://example.com"),
    (
        "http://lawmeme.research.yale.edu/modules.php?name=News&file=article&sid=350",
        "http://web.archive.org/web/20131113081856/http://lawmeme.research.yale.edu/modules.php?"
        "name=News&file=article&sid=350",
    ),
    ("https://example.com/sakddkakas", None),
    ("https://gogleakdjkakakaskdk.sidkdka.asdf", None),
])


@parameterize_url_redirect_url
def test_redirect(client: FlaskClient, url: str, redirect_url: str) -> None:
    response = client.get("/redirect", query_string={"url": url})
    if redirect_url:
        assert response.status_code == 302
        assert response.headers["Location"] == redirect_url
    else:
        assert response.status_code == 404


@parameterize_url_redirect_url
def test_json(client: FlaskClient, url: str, redirect_url: str) -> None:
    response = client.get("/json", query_string={"url": url})
    payload = response.json
    if redirect_url:
        assert payload["redirectUrl"] == redirect_url
    else:
        assert payload["redirectUrl"] is None
