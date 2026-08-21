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


SITE_REGISTRY: dict[str, SiteConfig] = {
    "novelfire.net": SiteConfig(
        base_url="https://novelfire.net/",
        seed_url="https://novelfire.net/genre-all/sort-popular/status-all/all-novel?page=6",
        name="Novel Fire",
        blocklist=["/chapter"],
        allowindb=["/book/"],
        unidirection=True,
        unidirection_url_struct="/all-novel?page",
        rate_limit=1.0

    ),
    # "royalroad.com": SiteConfig(
    #     base_url="https://www.royalroad.com/",
    #     seed_url="/fictions/search?page=990",
    #     name="Royal Road",
    #     blocklist=["/user/", "/login", "/signup", "/chapter", "/premium", "/ideas", "/forum", "/support", "/blog", "/author-dashboard", "/ps", "review", "/profile", "/private", "/e/", "/gp", "/dp", "/music", "/amazon"],
    #     allowindb=["/fiction/"],
    #     unidirection=False,
    #     unidirection_url_struct="",
    #     rate_limit=1.0,
    # ),
    # "novelbins.com": SiteConfig(
    #     base_url="https://novelbins.com/",
    #     seed_url="/novel",
    #     name="Novel Bins",
    #     blocklist=["/chapter", "/login", "/lostpassword", "/admin", "/about-us", "/privacy-policy", "/terms-of-use"],
    #     allowindb=["/novel/"],
    #     rate_limit=0.15
    # )
}
