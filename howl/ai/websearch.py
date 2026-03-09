"""Web search for HTB machine walkthroughs and exploit info."""

import re
from html.parser import HTMLParser


class _SnippetParser(HTMLParser):
    """Extract search result snippets from DuckDuckGo HTML."""

    def __init__(self):
        super().__init__()
        self._in_result = False
        self._in_snippet = False
        self._snippets = []
        self._titles = []
        self._current = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "")
        if tag == "a" and "result__a" in cls:
            self._in_title = True
            self._current = ""
        if tag == "a" and "result__snippet" in cls:
            self._in_snippet = True
            self._current = ""

    def handle_endtag(self, tag):
        if tag == "a" and self._in_title:
            self._in_title = False
            self._titles.append(self._current.strip())
        if tag == "a" and self._in_snippet:
            self._in_snippet = False
            self._snippets.append(self._current.strip())

    def handle_data(self, data):
        if self._in_snippet or self._in_title:
            self._current += data

    @property
    def results(self) -> list[dict]:
        out = []
        for i, snippet in enumerate(self._snippets):
            title = self._titles[i] if i < len(self._titles) else ""
            if snippet:
                out.append({"title": title, "snippet": snippet})
        return out


_cache: dict[str, str] = {}


def search_walkthroughs(machine_name: str, extra_query: str = "") -> str | None:
    """Search for walkthroughs/writeups for an HTB machine.

    Uses DuckDuckGo HTML search to find relevant writeups.
    Results are cached per machine name for the session.

    Returns:
        Concatenated search snippets, or None if search fails.
    """
    cache_key = f"{machine_name}:{extra_query}"
    if cache_key in _cache:
        return _cache[cache_key]

    query = f"{machine_name} HackTheBox walkthrough writeup"
    if extra_query:
        query += f" {extra_query}"

    try:
        import httpx

        resp = httpx.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"},
            timeout=15,
            follow_redirects=True,
        )

        if resp.status_code != 200:
            return None

        parser = _SnippetParser()
        parser.feed(resp.text)
        results = parser.results

        if not results:
            return None

        # Build a summary from top results (limit to avoid token bloat)
        lines = []
        for r in results[:5]:
            title = r["title"]
            snippet = r["snippet"]
            # Clean up snippet
            snippet = re.sub(r"\s+", " ", snippet).strip()
            if snippet:
                lines.append(f"- {title}: {snippet}")

        if not lines:
            return None

        summary = "\n".join(lines)
        # Truncate to ~1500 chars to avoid blowing up the prompt
        if len(summary) > 1500:
            summary = summary[:1500] + "..."

        _cache[cache_key] = summary
        return summary

    except Exception:
        return None


def search_exploit_info(service_name: str, version: str) -> str | None:
    """Search for exploit info for a specific service version.

    Returns:
        Concatenated search snippets about exploits, or None.
    """
    cache_key = f"exploit:{service_name}:{version}"
    if cache_key in _cache:
        return _cache[cache_key]

    query = f"{service_name} {version} exploit vulnerability CVE"

    try:
        import httpx

        resp = httpx.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"},
            timeout=15,
            follow_redirects=True,
        )

        if resp.status_code != 200:
            return None

        parser = _SnippetParser()
        parser.feed(resp.text)
        results = parser.results

        if not results:
            return None

        lines = []
        for r in results[:4]:
            snippet = re.sub(r"\s+", " ", r["snippet"]).strip()
            if snippet:
                lines.append(f"- {r['title']}: {snippet}")

        if not lines:
            return None

        summary = "\n".join(lines)
        if len(summary) > 1000:
            summary = summary[:1000] + "..."

        _cache[cache_key] = summary
        return summary

    except Exception:
        return None
