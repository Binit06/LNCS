import time


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
        self._script = self.redis.register_script(self._SCRIPT)

    def wait(self, site: str, rate_limit: float) -> None:
        key = f"crawler:ratelimit:{site}"
        now = time.time()

        scheduled = float(self._script(keys=[key], args=[rate_limit, now]))

        delay = scheduled - now
        if delay > 0:
            time.sleep(delay)
