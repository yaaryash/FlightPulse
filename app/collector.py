import asyncio
import logging
import httpx
from app.rate_limiter import AsyncRateLimiter

rate_limiter = AsyncRateLimiter(min_interval=10.0)

logger = logging.getLogger(__name__)

OPENSKY_URL = "https://opensky-network.org/api/states/all"
REQUEST_TIMEOUT = 20.0
MAX_RETRIES = 3


async def fetch_flights(
    client: httpx.AsyncClient,
    retries: int = MAX_RETRIES,
) -> list[dict]:
    """Fetch current flight states with timeout and retry handling."""

    if retries < 1:
        raise ValueError("retries must be at least 1")

    for attempt in range(retries):
        try:
            await rate_limiter.wait()
            response = await client.get(
                OPENSKY_URL,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 429:
                retry_after = response.headers.get(
                    "X-Rate-Limit-Retry-After-Seconds"
                )
                logger.warning(
                    "OpenSky rate limit reached (attempt %s/%s)",
                    attempt + 1,
                    retries,
                )

                if attempt == retries - 1:
                    response.raise_for_status()

                try:
                    delay = float(retry_after) if retry_after else 2**attempt
                except ValueError:
                    delay = 2**attempt

                await asyncio.sleep(max(0, min(delay, 60)))
                continue

            response.raise_for_status()
            payload = response.json()

            if not isinstance(payload, dict):
                raise ValueError("OpenSky response must be a JSON object")

            states = payload.get("states") or []
            flights = []

            for state in states:
                if not isinstance(state, list) or len(state) < 17:
                    logger.warning("Skipping malformed flight record")
                    continue

                flights.append(
                    {
                        "icao24": state[0],
                        "callsign": state[1],
                        "origin_country": state[2],
                        "time_position": state[3],
                        "last_contact": state[4],
                        "longitude": state[5],
                        "latitude": state[6],
                        "baro_altitude": state[7],
                        "on_ground": state[8],
                        "velocity": state[9],
                    }
                )

            logger.info("Fetched %s flight records", len(flights))
            return flights

        except (httpx.HTTPError, ValueError):
            logger.exception(
                "OpenSky request failed (attempt %s/%s)",
                attempt + 1,
                retries,
            )

            if attempt == retries - 1:
                raise

            await asyncio.sleep(2**attempt)

    return []
