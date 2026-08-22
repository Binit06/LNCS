"""
Live ASCII crawler monitor — run this alongside main.py to watch the crawl.

Pulls REAL numbers from Redis (same keys crawler/stats.py already writes:
crawl:request_started, crawl:request_success, crawl:request_failed,
crawl:page_crawled, crawl:url_discovered) and animates a spider walking
across a web whose size/activity reflects actual throughput.

Usage:
    python crawler_monitor.py
"""

import time

import redis
from rich.align import Align
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

WEB_WIDTH = 60
WEB_HEIGHT = 9

SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

SPIDER_FRAMES = [
    r"  /\_/\  ",
    r" (o.o)   ",
    r"  > ^ <  ",
]


def build_web(width: int, height: int) -> list[list[str]]:
    """A radial ASCII spiderweb, built once, walked over each frame."""
    grid = [[" " for _ in range(width)] for _ in range(height)]
    cx, cy = width // 2, height // 2

    # radial spokes
    import math
    for angle_deg in range(0, 360, 30):
        angle = math.radians(angle_deg)
        for r in range(1, max(width, height)):
            x = int(cx + r * math.cos(angle) * 1.4)
            y = int(cy + r * math.sin(angle) * 0.7)
            if 0 <= x < width and 0 <= y < height:
                grid[y][x] = "·"

    # concentric rings
    for ring in (3, 6, 9, 12):
        for angle_deg in range(0, 360, 8):
            angle = math.radians(angle_deg)
            x = int(cx + ring * math.cos(angle) * 1.4)
            y = int(cy + ring * math.sin(angle) * 0.7)
            if 0 <= x < width and 0 <= y < height:
                grid[y][x] = "." if grid[y][x] == " " else grid[y][x]

    return grid


BASE_WEB = build_web(WEB_WIDTH, WEB_HEIGHT)


class CrawlerMonitor:
    def __init__(self) -> None:
        self.redis = redis.Redis(host="localhost", port=6379, decode_responses=True)
        self.connected = True

        self.prev_started = 0
        self.frame = 0
        self.trail: list[tuple[int, int]] = []

    def get_int(self, key: str) -> int:
        try:
            value = self.redis.get(key)
            self.connected = True
            return int(value) if value else 0
        except redis.ConnectionError:
            self.connected = False
            return 0

    def spider_position(self, activity: int) -> tuple[int, int]:
        """Walk the spider around the web, speed tied to real request rate."""
        import math
        cx, cy = WEB_WIDTH // 2, WEB_HEIGHT // 2
        t = self.frame * (0.15 + min(activity, 20) * 0.03)
        r = 3 + 6 * ((math.sin(t * 0.4) + 1) / 2)
        x = int(cx + r * math.cos(t) * 1.4)
        y = int(cy + r * math.sin(t) * 0.7)
        x = max(0, min(WEB_WIDTH - 1, x))
        y = max(0, min(WEB_HEIGHT - 1, y))
        return x, y

    def render_web(self, x: int, y: int, active: bool) -> Text:
        grid = [row[:] for row in BASE_WEB]

        self.trail.append((x, y))
        self.trail = self.trail[-6:]

        out = Text()
        for row_i, row in enumerate(grid):
            for col_i, ch in enumerate(row):
                if (col_i, row_i) == (x, y):
                    out.append("🕷" if active else "○", style="bold")
                elif (col_i, row_i) in self.trail:
                    out.append("*", style="dim")
                elif ch == "·" or ch == ".":
                    out.append(ch, style="dim")
                else:
                    out.append(" ")
            out.append("\n")
        return out

    def make_panel(self) -> Panel:
        self.frame += 1

        started = self.get_int("crawl:request_started")
        success = self.get_int("crawl:request_success")
        failed = self.get_int("crawl:request_failed")
        pages = self.get_int("crawl:page_crawled")
        discovered = self.get_int("crawl:url_discovered")

        rps = started - self.prev_started
        self.prev_started = started
        active = rps > 0

        x, y = self.spider_position(rps)
        web = self.render_web(x, y, active)

        title = Text("🕸  CRAWLER WEB MONITOR  🕸", style="bold", justify="center")

        status_line = Text(justify="center")
        if not self.connected:
            status_line.append("REDIS UNREACHABLE", style="bold red")
        else:
            spin = SPINNER[self.frame % len(SPINNER)]
            state = "CRAWLING" if active else "IDLE"
            status_line.append(f"{spin} {state}", style="bold green" if active else "dim")

        stats = Table.grid(expand=True, padding=(0, 2))
        stats.add_column(justify="left")
        stats.add_column(justify="right")
        stats.add_row("Requests/sec", f"{rps}")
        stats.add_row("Total requests", f"{started}")
        stats.add_row("Successful", f"{success}")
        stats.add_row("Failed", f"{failed}")
        stats.add_row("Pages indexed", f"{pages}")
        stats.add_row("URLs discovered", f"{discovered}")

        body = Table.grid(expand=True)
        body.add_row(title)
        body.add_row(Text(""))
        body.add_row(Align.center(web))
        body.add_row(status_line)
        body.add_row(Text(""))
        body.add_row(stats)

        return Panel(
            body,
            title="[ live crawl activity ]",
            border_style="green" if active else "yellow",
            padding=(1, 2),
        )

    def run(self):
        with Live(self.make_panel(), refresh_per_second=8, screen=False) as live:
            while True:
                live.update(self.make_panel())
                time.sleep(0.12)


if __name__ == "__main__":
    try:
        CrawlerMonitor().run()
    except KeyboardInterrupt:
        print("\nMonitor stopped.")
