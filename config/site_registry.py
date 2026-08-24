from collections.abc import Callable
from typing import TypedDict


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


SITE_REGISTRY: dict[str, SiteConfig] = {
    "novelfire.net": SiteConfig(
        base_url="https://novelfire.net/",
        seed_url="/genre-all/sort-popular/status-all/all-novel?page=1",
        name="Novel Fire",
        blocklist=["/chapter"],
        allowindb=[r"/book/[^/]+"],
        unidirection=True,
        unidirection_url_struct="/all-novel?page",
        rate_limit=1.0,
        image_fix=None,
        pagination_template="/genre-all/sort-popular/status-all/all-novel?page={page}"
    ),
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
    #     pagination_template="/fictions/best-rated?page={page}"
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
    #     pagination_template="/novel/page/{page}"
    # )
}
