from collections.abc import Callable
from typing import TypedDict


class SiteSelectors(TypedDict):
    title_selector: str
    description_selector: str
    image_selector: str
    image_attr: str  # attribute to read off the image_selector element, e.g. "src", "data-src"


class SiteConfig(TypedDict):
    base_url: str
    seed_url: str
    name: str
    blocklist: list[str]
    allowindb: list[str]
    unidirection: bool
    unidirection_url_struct: str
    rate_limit: float
    image_fix: Callable[[str], str] | None
    pagination_template: str | None
    selectors: SiteSelectors
    user_agent: str


# Selectors below are sourced from the site's existing Jsoup-based Kotlin crawler
# (getNovelDetails). Two known gaps versus the Kotlin logic, since a plain
# (selector, attr) pair can't express them:
#   - novelfire.net description: Kotlin clones the node and removes a nested
#     ".expand" ("Show more") button before extracting text; the selector below
#     will include that button's text if present.
#   - royalroad.com cover: Kotlin blanks out coverUrl when it resolves to a
#     "nocover" placeholder image; the selector below will keep that image as-is.
SITE_REGISTRY: dict[str, SiteConfig] = {
    # "novelfire.net": SiteConfig(
    #     base_url="https://novelfire.net/",
    #     seed_url="/genre-all/sort-popular/status-all/all-novel?page=1",
    #     name="Novel Fire",
    #     blocklist=["/chapter"],
    #     allowindb=[r"/book/[^/]+"],
    #     unidirection=True,
    #     unidirection_url_struct="/all-novel?page",
    #     rate_limit=1.0,
    #     image_fix=None,
    #     pagination_template="/genre-all/sort-popular/status-all/all-novel?page={page}",
    #     selectors=SiteSelectors(
    #         title_selector="h1.novel-title",
    #         description_selector=".summary .content",  # includes ".expand" button text, see note above
    #         image_selector=".fixed-img figure.cover img",
    #         image_attr="src"
    #     )
    # ),
    # "royalroad.com": SiteConfig(
    #     base_url="https://www.royalroad.com/",
    #     seed_url="/fictions/best-rated/?page=1",
    #     name="Royal Road",
    #     blocklist=["/user/", "/login", "/signup", "/chapter", "/premium", "/ideas", "/forum", "/support", "/blog", "/author-dashboard", "/ps", "review", "/profile", "/private", "/e/", "/gp", "/dp", "/music", "/amazon"],
    #     allowindb=[r"/fiction/\d+(?:/[^/]+)?"],
    #     unidirection=True,
    #     unidirection_url_struct="/fictions/best-rated?page=",
    #     rate_limit=0.15,
    #     image_fix=None,
    #     pagination_template="/fictions/best-rated?page={page}",
    #     selectors=SiteSelectors(
    #         title_selector=".fic-header h1",
    #         description_selector=".description",  # covers both the plain and .hidden-content cases
    #         image_selector=".fic-header img.thumbnail",  # may still be a "nocover" placeholder, see note above
    #         image_attr="src"
    #     )
    # ),
    # "novelbins.com": SiteConfig(
    #     base_url="https://novelbins.com/",
    #     seed_url="/novel/page/1",
    #     name="Novel Bins",
    #     blocklist=["/chapter", "/login", "/lostpassword", "/admin", "/about-us", "/privacy-policy", "/terms-of-use"],
    #     allowindb=[r"/novel/(?!page(?:/|$))[^/]+"],
    #     unidirection=True,
    #     unidirection_url_struct="/novel/page/",
    #     rate_limit=0.15,
    #     image_fix=lambda url: url[url.rfind("https://"):] if url.count("https://") > 1 else url,
    #     pagination_template="/novel/page/{page}",
    #     selectors=SiteSelectors(
    #         title_selector=".novel-short-info h1",
    #         description_selector=".novel-short-info p:nth-of-type(8)",  # fragile: mirrors the Kotlin index[7] heuristic
    #         image_selector="img.novel-photo",
    #         image_attr="src"
    #     )
    # ),
    "novelfull.com": SiteConfig(
        base_url="https://novelfull.com/",
        seed_url="/most-popular?page=1",
        name="Novel Full",
        blocklist=["/chapter"],
        allowindb=[r"/[^/]+\.html$"],  # exactly one path segment => novel page; anything nested (chapters, postscript, afterword, etc.) is excluded
        unidirection=True,
        unidirection_url_struct="/most-popular?page",
        rate_limit=1.0,
        image_fix=None,
        pagination_template="/most-popular?page={page}",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        selectors=SiteSelectors(
            title_selector="h3.title",
            description_selector=".desc-text",
            image_selector=".book img",
            image_attr="src"
        )
    ),
}
