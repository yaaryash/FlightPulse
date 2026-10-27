
import httpx
import pytest

from app.collector import fetch_flights


@pytest.mark.asyncio
async def test_fetch_flights_parses_response():
    mock_payload = {
        "states": [
            [
                "abc123",       # icao24
                "AI101 ",       # callsign
                "India",        # origin_country
                1799999900,     # time_position
                1799999990,     # last_contact
                73.0,           # longitude
                19.0,           # latitude
                10000.0,        # baro_altitude
                False,          # on_ground
                220.0,          # velocity
                180.0,
                90.0,
                None,
                10000.0,
                "",
                False,
                0,
            ]
        ]
    }

    async def mock_handler(request):
        return httpx.Response(200, json=mock_payload)

    transport = httpx.MockTransport(mock_handler)

    async with httpx.AsyncClient(transport=transport) as client:
        flights = await fetch_flights(client)

    assert len(flights) == 1
    assert flights[0]["icao24"] == "abc123"
    assert flights[0]["origin_country"] == "India"
    assert flights[0]["longitude"] == 73.0


@pytest.mark.asyncio
async def test_fetch_flights_empty_response():
    async def mock_handler(request):
        return httpx.Response(200, json={"states": None})

    transport = httpx.MockTransport(mock_handler)

    async with httpx.AsyncClient(transport=transport) as client:
        flights = await fetch_flights(client)

    assert flights == []


@pytest.mark.asyncio
async def test_fetch_flights_retries_after_server_error():
    attempts = 0

    async def mock_handler(request):
        nonlocal attempts
        attempts += 1

        if attempts < 3:
            return httpx.Response(503, text="Service unavailable")

        return httpx.Response(200, json={"states": []})

    transport = httpx.MockTransport(mock_handler)

    async with httpx.AsyncClient(transport=transport) as client:
        flights = await fetch_flights(client)

    assert flights == []
    assert attempts == 3


@pytest.mark.asyncio
async def test_fetch_flights_raises_after_all_retries_fail():
    attempts = 0

    async def mock_handler(request):
        nonlocal attempts
        attempts += 1
        return httpx.Response(503, text="Service unavailable")

    transport = httpx.MockTransport(mock_handler)

    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await fetch_flights(client)

    assert attempts == 3


@pytest.mark.asyncio
async def test_fetch_flights_retries_after_network_error():
    attempts = 0

    async def mock_handler(request):
        nonlocal attempts
        attempts += 1

        if attempts == 1:
            raise httpx.ConnectError("Connection failed")

        return httpx.Response(200, json={"states": []})

    transport = httpx.MockTransport(mock_handler)

    async with httpx.AsyncClient(transport=transport) as client:
        flights = await fetch_flights(client)

    assert flights == []
    assert attempts == 2
