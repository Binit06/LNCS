import time
from config.settings import REDIS_KEY_RATE_LIMIT


class RateLimiter:
    _SCRIPT = """
    local key = KEYS[1]
    local rate_limit = tonumber(ARGV[1])
    local now = tonumber(ARGV[2])

    local next_time = redis.call('GET', key)
    if next_time then
        next_time = tonumber(next_time)
        if next_time < now then
            next_time = now
        end
    else
        next_time = now
    end

    redis.call('SET', key, next_time + rate_limit, 'EX', 3600)
    return tostring(next_time)
    """

    def __init__(self, redis_client) -> None:
        self.redis = redis_client
        self._script = self.redis.register_script(self._SCRIPT) if self.redis is not None else None
        self._local_last_request = {}

    def wait(self, site: str, rate_limit: float) -> None:
        key = REDIS_KEY_RATE_LIMIT.format(site=site)
        now = time.time()

        if self.redis is None:
            last_time = self._local_last_request.get(site, 0)
            next_time = max(last_time, now)
            self._local_last_request[site] = next_time + rate_limit
            delay = next_time - now
            if delay > 0:
                time.sleep(delay)
            return

        scheduled = float(self._script(keys=[key], args=[rate_limit, now]))

        delay = scheduled - now
        if delay > 0:
            time.sleep(delay)
