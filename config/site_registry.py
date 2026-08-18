from typing import TypedDict

class SiteConfig(TypedDict):
    base_url: str
    seed_url: str
    name: str
    blocklist: list[str]
    allowindb: list[str]
    rate_limit: float


SITE_REGISTRY: dict[str, SiteConfig] = {
    "royalroad.com": SiteConfig(
        base_url="https://www.royalroad.com/",
        seed_url="/fictions/search?page=250",
        name="Royal Road",
        blocklist=["/user/", "/login", "/signup", "/chapter", "/premium", "/ideas", "/forum", "/support", "/blog", "/author-dashboard", "/ps", "review", "/profile", "/private", "/e/", "/gp", "/dp", "/music", "/amazon"],
        allowindb=["/fiction/"],
        rate_limit=1.0,
    ),
    "novelbins.com": SiteConfig(
        base_url="https://novelbins.com/",
        seed_url="/novel",
        name="Novel Bins",
        blocklist=["/chapter", "/login", "/lostpassword", "/admin", "/about-us", "/privacy-policy", "/terms-of-use"],
        allowindb=["/novel/"],
        rate_limit=0.15
    )
}