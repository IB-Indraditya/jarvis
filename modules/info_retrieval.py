"""
modules/info_retrieval.py
=======================================================
Information Retrieval
=======================================================
- Web search
- Weather
- News
- Wikipedia/knowledge bases
- Maps
- APIs
"""

import requests
from config import Config
from utils.logger import get_logger

logger = get_logger("jarvis.info_retrieval")


# def web_search(query: str, num_results: int = 5) -> list[dict]:
#     """Generic web search using DuckDuckGo's HTML endpoint (no API key needed).
#     Swap this for Google Custom Search / Bing / SerpAPI in production."""
#     try:
#         resp = requests.post(
#             "https://html.duckduckgo.com/html/",
#             data={"q": query},
#             headers={"User-Agent": "Mozilla/5.0 (JARVIS)"},
#             timeout=8,
#         )
#         from bs4 import BeautifulSoup
#         soup = BeautifulSoup(resp.text, "html.parser")
#         results = []
#         for a in soup.select(".result__a")[:num_results]:
#             results.append({"title": a.get_text(strip=True), "url": a.get("href")})
#         return results
#     except Exception as exc:  # noqa: BLE001
#         logger.error(f"web_search failed: {exc}")
#         return []

# def web_search(query: str, num_results: int = 5) -> list[dict]:
#     try:
#         import requests
#         import os

#         api_key = os.getenv("BRAVE_SEARCH_API_KEY")

#         if not api_key:
#             logger.error("BRAVE_SEARCH_API_KEY is not configured")
#             return []

#         url = "https://api.search.brave.com/res/v1/web/search"

#         headers = {
#             "Accept": "application/json",
#             "X-Subscription-Token": api_key,
#         }

#         params = {
#             "q": query,
#             "count": num_results,
#         }

#         resp = requests.get(
#             url,
#             headers=headers,
#             params=params,
#             timeout=15,
#         )

#         logger.info(
#             f"Brave Search status: {resp.status_code}"
#         )

#         resp.raise_for_status()

#         data = resp.json()

#         results = []

#         for item in data.get("web", {}).get("results", [])[:num_results]:

#             results.append({
#                 "title": item.get("title", ""),
#                 "url": item.get("url", ""),
#                 "description": item.get("description", ""),
#             })

#         logger.info(
#             f"Search returned {len(results)} results"
#         )

#         return results

#     except Exception as exc:
#         logger.exception(
#             f"web_search failed: {exc}"
#         )
#         return []
def web_search(query: str, num_results: int = 5) -> list[dict]:
    """Web search using SerpApi."""

    try:
        import os
        import serpapi

        api_key = os.getenv("SERPAPI_KEY")

        if not api_key:
            logger.error("SERPAPI_KEY is not configured.")
            return []

        client = serpapi.Client(
            api_key=api_key
        )

        results = client.search({
            "engine": "google",
            "q": query,
            "num": num_results,
            "hl": "en",
            "gl": "in"
        })

        organic_results = results.get(
            "organic_results",
            []
        )

        output = []

        for result in organic_results[:num_results]:

            output.append({
                "title": result.get("title", ""),
                "url": result.get("link", ""),
            })

        logger.info(
            f"SerpApi returned {len(output)} results"
        )

        return output

    except Exception as exc:

        logger.exception(
            f"web_search failed: {exc}"
        )

        return []

def get_weather(city: str) -> dict:
    if not Config.WEATHER_API_KEY:
        return {"error": "WEATHER_API_KEY not configured."}
    try:
        resp = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": Config.WEATHER_API_KEY, "units": "metric"},
            timeout=8,
        )
        data = resp.json()
        if resp.status_code != 200:
            return {"error": data.get("message", "weather lookup failed")}
        return {
            "city": data.get("name"),
            "temp_c": data["main"]["temp"],
            "feels_like_c": data["main"]["feels_like"],
            "description": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"],
        }
    except Exception as exc:  # noqa: BLE001
        logger.error(f"get_weather failed: {exc}")
        return {"error": str(exc)}

def get_news(topic: str = "technology", num_results: int = 5) -> list[dict]:
    if not Config.NEWS_API_KEY:
        return [{"error": "NEWS_API_KEY not configured."}]
    try:
        resp = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={"category": topic, "apiKey": Config.NEWS_API_KEY, "pageSize": num_results, "language": "en"},
            timeout=8,
        )
        data = resp.json()
        return [
            {"title": a["title"], "source": a["source"]["name"], "url": a["url"]}
            for a in data.get("articles", [])
        ]
    except Exception as exc:  # noqa: BLE001
        logger.error(f"get_news failed: {exc}")
        return [{"error": str(exc)}]


def wikipedia_summary(query: str, sentences: int = 3) -> str:
    try:
        import wikipedia
        return wikipedia.summary(query, sentences=sentences, auto_suggest=True)
    except Exception as exc:  # noqa: BLE001
        logger.error(f"wikipedia_summary failed: {exc}")
        return f"Couldn't find a Wikipedia summary for '{query}'."


def geocode_place(place: str) -> dict:
    """Free geocoding via OpenStreetMap Nominatim (maps)."""
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": place, "format": "json", "limit": 1},
            headers={"User-Agent": "JARVIS/1.0"},
            timeout=8,
        )
        results = resp.json()
        if not results:
            return {"error": "location not found"}
        r = results[0]
        return {"lat": r["lat"], "lon": r["lon"], "display_name": r["display_name"]}
    except Exception as exc:  # noqa: BLE001
        logger.error(f"geocode_place failed: {exc}")
        return {"error": str(exc)}
