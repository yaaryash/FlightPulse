
import asyncio
import pytest
from app.rate_limiter import AsyncRateLimiter

@pytest.mark.asyncio
async def test_rate_limiter_enforces_minimum_interval():
    limiter = AsyncRateLimiter(min_interval=0.05)

    start = asyncio.get_running_loop().time()

    await limiter.wait()
    await limiter.wait()

    elapsed = asyncio.get_running_loop().time() - start

    assert elapsed >= 0.045


def test_rate_limiter_rejects_negative_interval():
    with pytest.raises(ValueError):
        AsyncRateLimiter(min_interval=-1)
