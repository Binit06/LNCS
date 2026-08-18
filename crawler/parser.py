from __future__ import annotations
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from typing import TYPE_CHECKING
import re

if TYPE_CHECKING:
    from crawler.seeder import PageData

class PageParser:
    def parse(self, page_url: str, raw_html: str) -> "PageData":
        soup = BeautifulSoup(raw_html, "html.parser")

        title = self.get_title(soup)
        description = self.get_description(soup)

        slug = page_url.rstrip("/").split("/")[-1]
        slug = re.sub(r"[-_]", " ", slug)

        links = []

        for link in soup.find_all("a", href=True):
            href = link.get("href")

            if isinstance(href, list):
                href = str(href[0])
            elif href is not None:
                href = str(href)
            else:
                continue

            links.append(urljoin(page_url, href))

        return {
            "title": title,
            "description": description,
            "slug": slug,
            "links": links
        }
    
    def get_meta(self, soup, property_name):
        tag = soup.find("meta", property=property_name)
        if tag and tag.get("content"):
            return tag.get("content")
        tag = soup.find("meta", attrs={"name": property_name})
        if tag and tag.get("content"):
            return tag.get("content")
        return ""

    def get_title(self, soup) -> str:
        for source in ("og:title", "twitter:title"):
            value = self.get_meta(soup, source)
            if value:
                return value
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        return ""

    def get_description(self, soup) -> str:
        for source in ("og:description", "twitter:description", "description"):
            value = self.get_meta(soup, source)
            if value:
                return value
        return ""