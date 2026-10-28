
import httpx
import pytest

from app.collector import fetch_flights


@pytest.fixture(autouse=True)
def disable_rate_limit_wait(monkeypatch):
    async def no_wait():
        return None

    monkeypatch.setattr(
        "app.collector.rate_limiter.wait",
        no_wait,
    )

    # Tests use fake credentials; no real secrets are needed.
    monkeypatch.setenv("OPENSKY_CLIENT_ID", "test-client")
    monkeypatch.setenv("OPENSKY_CLIENT_SECRET", "test-secret")

    # Reset the cached token before each test.
    monkeypatch.setattr("app.collector._access_token", None)
    monkeypatch.setattr("app.collector._token_expires_at", 0.0)


def mock_token_response():
    return httpx.Response(
        200,
        json={
            "access_token": "test-access-token",
            "expires_in": 1800,
            "token_type": "Bearer",
        },
    )


@pytest.mark.asyncio
async def test_fetch_flights_parses_response():
    mock_payload = {
        "states": [
            [
                "abc123",
                "AI101 ",
                "India",
                1799999900,
                1799999990,
                73.0,
                19.0,
                10000.0,
                False,
                220.0,
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
        if request.url.host == "auth.opensky-network.org":
            return mock_token_response()

        assert request.headers["Authorization"] == "Bearer test-access-token"
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
        if request.url.host == "auth.opensky-network.org":
            return mock_token_response()

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

        if request.url.host == "auth.opensky-network.org":
            return mock_token_response()

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

        if request.url.host == "auth.opensky-network.org":
            return mock_token_response()

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

        if request.url.host == "auth.opensky-network.org":
            return mock_token_response()

        attempts += 1

        if attempts == 1:
            raise httpx.ConnectError("Connection failed")

        return httpx.Response(200, json={"states": []})

    transport = httpx.MockTransport(mock_handler)

    async with httpx.AsyncClient(transport=transport) as client:
        flights = await fetch_flights(client)

    assert flights == []
    assert attempts == 2
