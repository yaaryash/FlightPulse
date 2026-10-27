
# FlightPulse

An asynchronous flight data collection and analytics API built with Python.

## Tech Stack

- FastAPI — REST API
- HTTPX — asynchronous HTTP requests
- Pandas — data cleaning and analysis
- SQLAlchemy — database ORM
- SQLite — relational database
- Pydantic — request and response validation
- Pytest — automated testing

## Project Structure

```text
app/
  routes/
  main.py
  database.py
  models.py
  schemas.py
  collector.py
  pipeline.py
tests/
data/
requirements.txt
README.md
```

## Setup

Create and activate a Python environment, then install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Project Status

- [x] Initial project structure
- [x] SQLAlchemy engine and SQLite session setup
- [x] Flight database model
- [x] Initial database table creation
- [x] Pydantic request/response schemas
- [x] Field validation for flight data
- [x] Asynchronous data collector
- [x] Data normalization and validation
- [x] Timestamp conversion
- [x] SHA-256 fingerprint generation
- [x] In-batch duplicate detection
- [x] Database persistence pipeline
- [x] Flight listing and filtering endpoints
- [ ] Analytics endpoints
- [ ] Error handling and structured logging
- [x] Automated tests (12 passed)




