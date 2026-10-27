
# Flight Analytics API

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
- [x] SQLite engine and database session setup
- [ ] Flight database model and schema initialization
- [ ] Asynchronous data collection
- [ ] Data normalization and deduplication
- [ ] REST API endpoints
- [ ] Analytics endpoints
- [ ] Automated tests
