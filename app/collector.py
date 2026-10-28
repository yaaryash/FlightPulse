import asyncio
import logging
import os
import time
import httpx
from app.rate_limiter import AsyncRateLimiter

logger = logging.getLogger(__name__)

OPENSKY_URL = "https://opensky-network.org/api/states/all"
TOKEN_URL = (
    "https://auth.opensky-network.org/auth/realms/opensky-network/"
    "protocol/openid-connect/token"
)

REQUEST_TIMEOUT = 20.0
MAX_RETRIES = 3
TOKEN_REFRESH_MARGIN = 60
rate_limiter = AsyncRateLimiter(min_interval=10.0)
_access_token: str | None = None
_token_expires_at = 0.0
_token_lock = asyncio.Lock()

async def get_access_token(client: httpx.AsyncClient) -> str:
    """Get an OAuth2 token and reuse it until shortly before expiry."""
    global _access_token, _token_expires_at

    client_id = os.getenv("OPENSKY_CLIENT_ID")
    client_secret = os.getenv("OPENSKY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError(
            "Missing OPENSKY_CLIENT_ID or OPENSKY_CLIENT_SECRET"
        )

    async with _token_lock:
        if (
            _access_token
            and time.monotonic() < _token_expires_at
        ):
            return _access_token

        response = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        token_data = response.json()
        _access_token = token_data["access_token"]
        expires_in = int(token_data.get("expires_in", 1800))
        _token_expires_at = (
            time.monotonic() + max(1, expires_in - TOKEN_REFRESH_MARGIN)
        )

        logger.info("OpenSky OAuth2 access token obtained")
        return _access_token


async def fetch_flights(
    client: httpx.AsyncClient,
    retries: int = MAX_RETRIES,
) -> list[dict]:
    """Fetch current flight states with OAuth2, timeout and retries."""

    if retries < 1:
        raise ValueError("retries must be at least 1")

    for attempt in range(retries):
        try:
            await rate_limiter.wait()
            token = await get_access_token(client)
            response = await client.get(
                OPENSKY_URL,
                headers={"Authorization": f"Bearer {token}"},
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 401:
                global _access_token, _token_expires_at
                _access_token = None
                _token_expires_at = 0.0

                if attempt < retries - 1:
                    continue

            if response.status_code == 429:
                retry_after = response.headers.get(
                    "X-Rate-Limit-Retry-After-Seconds"
                )
                try:
                    delay = float(retry_after) if retry_after else 2**attempt
                except ValueError:
                    delay = 2**attempt

                logger.warning(
                    "OpenSky rate limit reached (attempt %s/%s)",
                    attempt + 1,
                    retries,
                )

                if attempt == retries - 1:
                    response.raise_for_status()

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

        except (httpx.HTTPError, ValueError, KeyError):
            logger.exception(
                "OpenSky request failed (attempt %s/%s)",
                attempt + 1,
                retries,
            )

            if attempt == retries - 1:
                raise

            await asyncio.sleep(2**attempt)

    return []
