from __future__ import annotations

import re
from typing import TYPE_CHECKING
from urllib.parse import urljoin

from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from crawler.seeder import PageData, SiteSelectors

class PageParser:
    def parse(self, page_url: str, raw_html: str, selector: SiteSelectors) -> PageData:
        soup = BeautifulSoup(raw_html, "html.parser")

        title = self.get_text(soup, selector.get("title_selector"))
        description = self.get_text(soup, selector.get("description_selector"))
        image = self.get_image(soup, selector.get("image_selector"), selector.get("image_att") or "src")

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
            "image": image,
            "slug": slug,
            "links": links
        }
    def get_text(self, soup, selector: str | None) -> str:
        if not selector:
            return ""
        el = soup.select_one(selector)
        if not el:
            return ""
        return el.get_text(strip=True)
    
    def get_image(self, soup, selector: str | None, attr: str = "src") -> str:
        if not selector:
            return ""
        el = soup.select_one(selector)
        if not el:
            return ""
        value = el.get(attr)
        if isinstance(value, list):
            value = value[0] if value else None
        return value or ""
