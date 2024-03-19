from flask import abort, Flask, jsonify, redirect, request
import enum
import requests
from typing import Tuple
from urllib.parse import urlparse


class Status(enum.Enum):
    LIVE = "live"
    ARCHIVED = "archived"
    BROKEN = "broken"


def process_url(url: str) -> Tuple[Status, str]:
    """
    Process a url to determine if its live, archived, or broken.

    Args:
        url: Url to check.

    Returns:
        Tupe of status and url to redirect to (or `None` if broken).
    """
    # Return the original URL if available.
    try:
        response = requests.head(url, allow_redirects=True)
        response.raise_for_status()
        return Status.LIVE, url
    except (requests.exceptions.ConnectionError, requests.HTTPError) as ex:
        app.logger.info("url '%s' is not live: %s", url, ex)

    # Redirect to the most recent wayback capture if it's available.
    response = requests.get("http://archive.org/wayback/available", {"url": url})
    try:
        response.raise_for_status()
        payload = response.json()
        archived_snapshots = payload.get("archived_snapshots")
        if archived_snapshots:
            return Status.ARCHIVED, archived_snapshots["closest"]["url"]
        app.logger.info("url '%s' has not been archived", url)
    except (
        requests.exceptions.ConnectionError,
        requests.HTTPError,
    ) as ex:  # pragma: no cover
        app.logger.info("failed to check if url '%s' is archived: %s", url, ex)

    return Status.BROKEN, None


app = Flask(__name__)


@app.route("/redirect")
def index():
    """
    Redirect to the live or archived page if available or raise 404 if the link is broken.
    """
    url = request.args.get("url")
    if url is None:
        abort(400, "query string argument `url` must be given")

    _, redirect_url = process_url(url)
    if redirect_url:
        return redirect(redirect_url)
    abort(404, f"sorry the url '{url}' is broken")


@app.route("/json")
def json():
    """
    Check if a website is live, archived, or broken. Return the status and appropriate redirect url
    as json.
    """
    url = request.args.get("url")
    if url is None:
        abort(400, "query string argument `url` must be given")

    status, url = process_url(url)
    response = jsonify(status=status.value, redirectUrl=url)

    if request.referrer:
        referrer = urlparse(request.referrer)
        if (
            referrer.netloc.startswith("localhost")
            or referrer.netloc == "wayback-if-down.github.io"
        ):
            origin = f"{referrer.scheme}://{referrer.netloc}"
            response.headers.add_header("Access-Control-Allow-Origin", origin)

    return response
