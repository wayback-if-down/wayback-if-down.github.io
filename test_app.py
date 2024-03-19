from main import app
import os
import pytest
import requests
from typing import Callable, Union
from werkzeug.test import TestResponse


GetMethod = Callable[..., Union[requests.Response, TestResponse]]


@pytest.fixture
def get_method() -> GetMethod:
    if "TEST_LIVE" in os.environ:

        def _wrapper(url, *args, **kwargs) -> requests.Response:
            """
            Wrapper to make requests.get look like app.test_client.get.
            """
            base_url = "https://wayback-if-down.ue.r.appspot.com"
            params = kwargs.pop("query_string", None)
            if params:
                kwargs["params"] = params
            kwargs.setdefault("allow_redirects", False)
            return requests.get(f"{base_url}{url}", *args, **kwargs)

        return _wrapper
    else:
        return app.test_client().get


parameterize_url_redirect_url = pytest.mark.parametrize(
    "url, redirect_url",
    [
        ("https://example.com", "https://example.com"),
        (
            "http://lawmeme.research.yale.edu/modules.php"
            "?name=News&file=article&sid=350",
            "http://web.archive.org/web/20131113081856/"
            "http://lawmeme.research.yale.edu/modules.php"
            "?name=News&file=article&sid=350",
        ),
        ("https://example.com/sakddkakas", None),
        ("https://gogleakdjkakakaskdk.sidkdka.asdf", None),
    ],
)


@parameterize_url_redirect_url
def test_redirect(get_method: GetMethod, url: str, redirect_url: str) -> None:
    response = get_method("/redirect", query_string={"url": url})
    if redirect_url:
        assert response.status_code == 302, response.text
        assert response.headers["Location"] == redirect_url
    else:
        assert response.status_code == 404, response.text


@parameterize_url_redirect_url
def test_json(get_method: GetMethod, url: str, redirect_url: str) -> None:
    response = get_method("/json", query_string={"url": url})
    payload = response.json
    if callable(payload):
        payload = payload()
    if redirect_url:
        assert payload["redirectUrl"] == redirect_url
    else:
        assert payload["redirectUrl"] is None


def test_redirect_missing_url(get_method: GetMethod) -> None:
    assert get_method("/redirect").status_code == 400


def test_json_missing_url(get_method: GetMethod) -> None:
    assert get_method("/json").status_code == 400


def test_json_cors(get_method: GetMethod) -> None:
    for url in [
        "http://localhost:393/something/or/other",
        "https://wayback-if-down.github.io",
    ]:
        headers = {"Referer": url}
        response = get_method(
            "/json", query_string={"url": "https://google.com/"}, headers=headers
        )
        assert url.startswith(response.headers["Access-Control-Allow-Origin"])

    for url in ["https://example.com/"]:
        headers = {"Referer": url}
        response = get_method(
            "/json", query_string={"url": "https://google.com/"}, headers=headers
        )
        assert "Access-Control-Allow-Origin" not in response.headers
