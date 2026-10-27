
import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)

OPENSKY_URL = "https://opensky-network.org/api/states/all"


async def fetch_flights(
    client: httpx.AsyncClient,
    retries: int = 3,
) -> list[dict]:
    """Fetch current flight states from the OpenSky API."""

    for attempt in range(retries):
        try:
            response = await client.get(OPENSKY_URL)
            response.raise_for_status()
            payload = response.json()

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

        except (httpx.HTTPError, ValueError) as exc:
            logger.warning(
                "OpenSky request failed (attempt %s/%s): %s",
                attempt + 1,
                retries,
                exc,
            )

            if attempt == retries - 1:
                raise

            await asyncio.sleep(2 ** attempt)

    return []
