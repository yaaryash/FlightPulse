# FlightPulse ✈️

An asynchronous flight data collection and analytics API built with Python, FastAPI, and Pandas. FlightPulse collects live flight data from the OpenSky API, normalizes and deduplicates records, persists them in SQLite, and exposes REST endpoints for flight queries and analytics.

## Features

- **Asynchronous data collection** using HTTPX.
- **Resilient API requests** with timeout, retry, and rate-limiting handling.
- **Data normalization and validation** for timestamps, coordinates, velocity, and optional fields.
- **Duplicate detection** using SHA-256 fingerprints and Pandas batch deduplication.
- **Database persistence** using SQLAlchemy and SQLite, with per-record savepoints.
- **Flight listing and filtering** through REST endpoints.
- **Analytics endpoints** for country-wise statistics and flight summaries.
- **Automated testing** with Pytest.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| FastAPI | REST API framework |
| HTTPX | Asynchronous HTTP requests |
| Pandas | Data normalization, deduplication, and analytics |
| SQLAlchemy | ORM and database operations |
| SQLite | Relational database |
| Pydantic | Request and response validation |
| Pytest | Automated testing |

## Architecture

```text
OpenSky API
     |
     v
Async HTTPX Collector
     |
     v
Retry, Timeout & Rate Limiting
     |
     v
Data Normalization & Validation
     |
     v
Pandas Batch Deduplication
     |
     v
SHA-256 Fingerprint Generation
     |
     v
SQLAlchemy Persistence
     |
     v
SQLite Database
     |
     +----------------------+
     |                      |
     v                      v
Flight REST API        Analytics API
```

## Project Structure

```text
FlightPulse/
├── app/
│   ├── routes/
│   │   ├── flights.py
│   │   └── analytics.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── collector.py
│   ├── pipeline.py
│   └── rate_limiter.py
├── data/
│   └── sample_flights.json
├── tests/
│   ├── test_api.py
│   ├── test_collector.py
│   ├── test_pipeline.py
│   └── test_rate_limiter.py
├── requirements.txt
└── README.md
```

## Getting Started

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd flights
```

Replace the placeholder with your actual repository URL.

### 2. Create and activate a Python environment

Using Conda:

```bash
conda create -n flight-api python=3.11
conda activate flight-api
```

Alternatively, use a Python virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows Git Bash:

```bash
source .venv/Scripts/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Start the API server

```bash
uvicorn app.main:app --reload
```

The API will be available at:

- API base URL: `http://127.0.0.1:8000`
- Interactive Swagger documentation: `http://127.0.0.1:8000/docs`
- Health endpoint: `http://127.0.0.1:8000/health`

The application creates missing database tables during startup.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Root endpoint |
| GET | `/health` | Health check |
| GET | `/flights/` | List flight records with filtering and pagination |
| GET | `/analytics/countries` | Country-wise flight analytics |
| GET | `/analytics/summary` | Flight summary statistics |
| POST | `/pipeline/run` | Fetch, normalize, deduplicate, and persist live flight data |

Open `/docs` while the server is running to inspect endpoint parameters and response schemas.

### Run the data pipeline

Send a `POST` request to:

```text
http://127.0.0.1:8000/pipeline/run
```

Example using curl:

```bash
curl -X POST http://127.0.0.1:8000/pipeline/run
```

A successful execution returns processing metrics, including the number of records fetched, normalized, inserted, skipped as duplicates, and records that encountered persistence errors.

Example response structure:

```json
{
  "fetched": 599,
  "normalized": 599,
  "inserted": 599,
  "duplicates": 0,
  "errors": 0
}
```

These values are an example from a successful run; actual results depend on the upstream API response and existing database records.

## Data Processing

1. Fetch flight data asynchronously from the OpenSky API.
2. Validate required fields and normalize optional values.
3. Convert Unix timestamps into UTC-based, timezone-naive Python datetimes for SQLite compatibility.
4. Validate numeric values and geographic coordinate ranges.
5. Generate SHA-256 fingerprints for flight-state deduplication.
6. Use Pandas to remove duplicates within each fetched batch and normalize missing values.
7. Persist records through SQLAlchemy while detecting existing fingerprints.
8. Expose stored records and aggregated statistics through REST endpoints.

## Error Handling and Reliability

- HTTP request timeouts and retry handling.
- Rate limiting for upstream API requests.
- Invalid flight records are rejected during normalization.
- Missing numeric and timestamp values are normalized to avoid `NaN` and `NaT` database errors.
- Database savepoints isolate individual insert failures.
- Existing fingerprints prevent duplicate records from being inserted again.

## Running Tests

Run the complete test suite:

```bash
python -m pytest -v
```

Run a specific test module:

```bash
python -m pytest tests/test_pipeline.py -v
```

The current test suite contains **24 passing tests**, covering API endpoints, data collection, normalization, deduplication, database persistence, pipeline execution, and rate limiting.

## Current Project Status

- [x] FastAPI application and SQLite integration
- [x] SQLAlchemy flight model and schemas
- [x] Asynchronous OpenSky data collection
- [x] Retry, timeout, and rate-limiting handling
- [x] Data normalization and validation
- [x] SHA-256 fingerprint generation
- [x] Pandas batch deduplication
- [x] Database persistence and duplicate detection
- [x] Flight listing and analytics endpoints
- [x] Live pipeline integration
- [x] Missing-value regression tests
- [x] 24 automated tests passing

## Future Improvements

- Add scheduled background data collection.
- Introduce database migrations with Alembic.
- Add PostgreSQL support for production deployments.
- Add structured logging and pipeline execution metrics.
- Containerize the application using Docker.
- Add CI workflows to run tests automatically on GitHub.

## License

Add a license appropriate for your intended use before distributing the project.
