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


def test_redirect_missing_url(client: FlaskClient) -> None:
    assert client.get("/redirect").status_code == 400


def test_json_missing_url(client: FlaskClient) -> None:
    assert client.get("/json").status_code == 400


def test_json_cors(client: FlaskClient) -> None:
    for url in ["http://localhost:393/something/or/other", "https://wayback-if-down.github.io"]:
        headers = {"Referer": url}
        response = client.get("/json", query_string={"url": "https://google.com/"}, headers=headers)
        assert url.startswith(response.headers["Access-Control-Allow-Origin"])

    for url in ["https://example.com/"]:
        headers = {"Referer": url}
        response = client.get("/json", query_string={"url": "https://google.com/"}, headers=headers)
        assert "Access-Control-Allow-Origin" not in response.headers
