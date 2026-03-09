"""CorpNet Solutions - Public Web Application (SSRF Vulnerable)."""

import requests as http_requests
from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/")
def index():
    """Corporate landing page for CorpNet Solutions."""
    return render_template("index.html")


@app.route("/news")
def news():
    """Fake corporate news page."""
    articles = [
        {
            "title": "CorpNet Solutions Expands Cloud Infrastructure",
            "date": "2024-03-15",
            "summary": "We are proud to announce the expansion of our internal "
                       "cloud infrastructure to better serve our enterprise clients.",
        },
        {
            "title": "New Internal API Platform Launched",
            "date": "2024-02-28",
            "summary": "Our engineering team has deployed a new internal API "
                       "platform to streamline service communication across "
                       "our segmented network architecture.",
        },
        {
            "title": "Security Audit Completed Successfully",
            "date": "2024-01-10",
            "summary": "Our annual security audit has been completed. All "
                       "internal services passed compliance checks.",
        },
    ]
    return render_template("news.html", articles=articles)


@app.route("/fetch", methods=["GET", "POST"])
def fetch_url():
    """URL fetcher endpoint - VULNERABLE to SSRF (CWE-918).

    Fetches any user-supplied URL from the server side with zero validation.
    This allows an attacker to reach internal network services that are not
    directly accessible from the outside.
    """
    result = None
    url = ""
    error = None

    if request.method == "POST":
        url = request.form.get("url", "").strip()

        if url:
            # VULNERABLE: No URL validation or restriction whatsoever.
            # An attacker can supply internal IPs (e.g., http://172.21.0.2:5000)
            # to reach services on the internal network.
            try:
                resp = http_requests.get(url, timeout=5)
                result = resp.text
            except http_requests.exceptions.ConnectionError:
                error = f"Connection failed: Could not reach {url}"
            except http_requests.exceptions.Timeout:
                error = f"Request timed out for {url}"
            except http_requests.exceptions.MissingSchema:
                error = "Invalid URL format. Please include http:// or https://"
            except Exception as e:
                error = f"Error fetching URL: {str(e)}"
        else:
            error = "Please enter a URL to check."

    return render_template("fetch.html", result=result, url=url, error=error)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
