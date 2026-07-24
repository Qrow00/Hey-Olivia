import httpx
from typing import Optional
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import re


class NewsService:
    DEFAULT_FEEDS = [
        "https://feeds.bbci.co.uk/news/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://feeds.skynews.com/feeds/rss/world.xml",
    ]

    def __init__(self):
        self.feeds = self.DEFAULT_FEEDS.copy()

    async def fetch_headlines(self, feeds: Optional[list[str]] = None, limit: int = 5) -> list[dict]:
        feeds = feeds or self.feeds
        all_items = []

        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            for feed_url in feeds:
                try:
                    resp = await client.get(feed_url)
                    resp.raise_for_status()
                    items = self._parse_rss(resp.text, limit=limit)
                    all_items.extend(items)
                except Exception:
                    continue

        all_items.sort(key=lambda x: x.get("published", ""), reverse=True)
        return all_items[:limit]

    def _parse_rss(self, xml_text: str, limit: int = 5) -> list[dict]:
        items = []
        try:
            root = ET.fromstring(xml_text)
            for item in root.iter("item"):
                title = item.findtext("title", "").strip()
                description = item.findtext("description", "").strip()
                link = item.findtext("link", "").strip()
                pub_date = item.findtext("pubDate", "").strip()

                if not title:
                    continue

                description = self._clean_html(description)

                items.append({
                    "title": title,
                    "description": description[:200] if description else "",
                    "link": link,
                    "published": pub_date,
                })

                if len(items) >= limit:
                    break
        except ET.ParseError:
            pass

        return items

    def _clean_html(self, text: str) -> str:
        return re.sub(r"<[^>]+>", "", text).strip()

    async def get_summary(self, limit: int = 5) -> str:
        try:
            headlines = await self.fetch_headlines(limit=limit)
            if not headlines:
                return "No headlines available right now."

            lines = [f"Here are your top {len(headlines)} headlines:"]
            for i, h in enumerate(headlines, 1):
                lines.append(f"{i}. {h['title']}.")

            return " ".join(lines)
        except Exception as e:
            return f"News feed unavailable: {e}"


news_service = NewsService()
