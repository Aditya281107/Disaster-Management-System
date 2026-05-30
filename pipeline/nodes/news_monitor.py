"""
Node 4: News Monitoring & Context
====================================
Queries NewsAPI (or mock) for local disaster/weather reports
to provide real-world context alongside the ML prediction.
"""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")


def _fetch_news_api(location: str) -> str:
    """Fetch real news from NewsAPI.org."""
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": f"{location} disaster OR flood OR hurricane OR storm OR earthquake",
        "sortBy": "publishedAt",
        "pageSize": 5,
        "apiKey": NEWS_API_KEY,
        "language": "en",
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    articles = data.get("articles", [])
    if not articles:
        return f"No recent disaster-related news found for {location}."

    summaries = []
    for i, article in enumerate(articles[:5], 1):
        title = article.get("title", "No title")
        desc = article.get("description", "No description")
        source = article.get("source", {}).get("name", "Unknown")
        summaries.append(f"{i}. [{source}] {title}\n   {desc}")

    return "\n\n".join(summaries)


def _mock_news(location: str, disaster_type: str = "") -> str:
    """Generate realistic mock news for demo purposes."""
    location_lower = location.lower()

    # Context-aware mock articles based on predicted disaster type
    news_db = {
        "Flood": [
            f"1. [Reuters] Heavy Rainfall Warning Issued for {location} Region\n"
            f"   Meteorological department has issued a red alert for {location} "
            "as continuous rainfall for the past 48 hours has caused water levels "
            "to rise significantly in local rivers.",
            f"2. [Local Times] Low-Lying Areas of {location} Evacuated\n"
            "   City authorities have begun evacuating residents from flood-prone "
            "areas as river levels continue to rise. Emergency shelters have been "
            "set up in schools and community centers.",
            f"3. [Weather Channel] Flood Risk Remains High Across Region\n"
            "   Sustained heavy rainfall has saturated soil and overwhelmed drainage "
            "systems. Experts warn of potential flash flooding in urban areas.",
        ],
        "Hurricane": [
            f"1. [AP News] Tropical Storm Intensifying Near {location}\n"
            f"   A tropical storm off the coast of {location} is rapidly intensifying "
            "with sustained winds above 120 km/h. Hurricane warnings have been issued.",
            f"2. [CNN] Residents Urged to Evacuate Coastal {location}\n"
            "   Emergency management officials are urging coastal residents to evacuate "
            "as the storm is expected to make landfall within 48 hours.",
            f"3. [NOAA] Storm Surge Warning for {location} Coastline\n"
            "   Storm surge of 2-4 meters is expected along the coastline. All maritime "
            "activities have been suspended.",
        ],
        "Heatwave": [
            f"1. [BBC News] Extreme Heat Advisory for {location}\n"
            f"   Temperatures in {location} are expected to exceed 45C this week, "
            "prompting health authorities to issue heat stroke warnings.",
            f"2. [Local Health Dept] Heat-Related Hospital Admissions Spike\n"
            "   Hospitals are reporting a 40% increase in heat-related emergencies. "
            "Elderly and outdoor workers are most affected.",
            f"3. [Weather Service] No Relief Expected for 72 Hours\n"
            "   The heat dome over the region is expected to persist for at least "
            "three more days before any cooling trend begins.",
        ],
        "Thunderstorm": [
            f"1. [Weather Alert] Severe Thunderstorm Watch for {location}\n"
            "   Strong thunderstorms with heavy rain, large hail, and damaging winds "
            "are expected across the region in the next 24 hours.",
            f"2. [Local News] Power Outages Reported After Lightning Strikes\n"
            "   Multiple areas reporting power outages after intense lightning activity. "
            "Utility crews are working to restore service.",
            f"3. [Emergency Services] Flash Flood Warning Accompanies Storms\n"
            "   Rapid rainfall rates may lead to flash flooding in low-lying areas "
            "and near streams.",
        ],
    }

    default_news = [
        f"1. [Local Weather] Seasonal Weather Patterns in {location}\n"
        "   Weather conditions remain within normal seasonal ranges. No significant "
        "weather events are currently forecast for the region.",
        f"2. [Climate Monitor] Regional Environmental Conditions Stable\n"
        "   Environmental monitoring systems report stable conditions across "
        "the region with no immediate concerns.",
    ]

    articles = news_db.get(disaster_type, default_news)
    return "\n\n".join(articles)


def news_monitor_node(state: dict) -> dict:
    """
    Node 4: Fetch and summarize disaster-related news for the location.
    """
    print(f"\n{'='*60}")
    print(f"[NODE 4] NEWS MONITORING & CONTEXT")
    print(f"{'='*60}")

    location = state["location"]
    # Use ML prediction to focus news search if available
    disaster_type = state.get("disaster_prediction", {}).get("predicted_disaster", "")

    if NEWS_API_KEY:
        try:
            news = _fetch_news_api(location)
            print(f"Source: NewsAPI.org")
        except Exception as e:
            print(f"API error: {e}. Falling back to mock news.")
            news = _mock_news(location, disaster_type)
    else:
        news = _mock_news(location, disaster_type)
        print(f"Source: Mock News (no API key configured)")

    print(f"\nRelevant News Articles:")
    print(news[:500] + "..." if len(news) > 500 else news)

    return {"news_context": news}
