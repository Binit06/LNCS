import time

import redis


class StatsMonitor:
    RESET = "\033[0m"
    BOLD = "\033[1m"

    CYAN = "\033[36m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    WHITE = "\033[37m"
    DIM = "\033[2m"
    MAGENTA = "\033[35m"

    def __init__(self) -> None:
        self.redis = redis.Redis(
            host="localhost",
            port=6379,
            decode_responses=True
        )

        self.previous_requests = 0

    def get_int(self, key):
        value = self.redis.get(key)

        if value is None:
            return 0

        return int(value)

    def display(self):
        total_requests = self.get_int("crawl:request_started")
        successful = self.get_int("crawl:request_success")
        failed = self.get_int("crawl:request_failed")
        pages = self.get_int("crawl:page_crawled")
        discovered = self.get_int("crawl:url_discovered")

        rps = total_requests - self.previous_requests
        self.previous_requests = total_requests

        print("\033[2J\033[H", end="")

        print(f"{self.BOLD}{self.CYAN}" + "=" * 50 + self.RESET)
        print(
            f"{self.BOLD}{self.WHITE}"
            "                 CRAWLER STATS"
            f"{self.RESET}"
        )
        print(f"{self.BOLD}{self.CYAN}" + "=" * 50 + self.RESET)

        print(
            f"{self.YELLOW}Requests/sec{self.RESET}"
            f"       : {self.BOLD}{rps}{self.RESET}"
        )

        print(
            f"{self.CYAN}Total requests{self.RESET}"
            f"     : {total_requests}"
        )

        print(
            f"{self.GREEN}Successful{self.RESET}"
            f"         : {successful}"
        )

        print(
            f"{self.RED}Failed{self.RESET}"
            f"             : {failed}"
        )

        print(
            f"{self.BLUE}Pages crawled{self.RESET}"
            f"      : {pages}"
        )

        print(
            f"{self.MAGENTA}URLs discovered{self.RESET}"
            f"    : {discovered}"
        )

        print(f"{self.BOLD}{self.CYAN}" + "=" * 50 + self.RESET)

    def run(self):
        print("Stats Monitor Started")

        while True:
            try:
                self.display()
                time.sleep(1)

            except KeyboardInterrupt:
                print("\nStats monitor stopped.")
                break

            except redis.ConnectionError:
                print(
                    f"{self.RED}"
                    "Could not connect to redis."
                    f"{self.RESET}"
                )
                time.sleep(2)


if __name__ == "__main__":
    monitor = StatsMonitor()
    monitor.run()
