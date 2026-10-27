
import asyncio


class AsyncRateLimiter:
    """Ensure a minimum interval between requests."""

    def __init__(self, min_interval: float = 10.0):
        if min_interval < 0:
            raise ValueError("min_interval cannot be negative")

        self.min_interval = min_interval
        self._lock = asyncio.Lock()
        self._last_request_at: float | None = None

    async def wait(self) -> None:
        async with self._lock:
            loop = asyncio.get_running_loop()
            now = loop.time()

            if self._last_request_at is not None:
                elapsed = now - self._last_request_at
                remaining = self.min_interval - elapsed

                if remaining > 0:
                    await asyncio.sleep(remaining)

            self._last_request_at = loop.time()
