# Vacation Rental AI Assistant

FastAPI backend for searching vacation rentals by destination, guest count,
nightly budget, property type, amenities, and date availability. The frontend
has not been implemented yet.

## Requirements

- Python 3.10 or newer
- PostgreSQL
- Ollama with the `llama3.2:3b` model

## Setup (Windows PowerShell)

From the project root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Set `DATABASE_URL` in `.env` to a PostgreSQL connection URL, for example:

```text
DATABASE_URL=postgresql://USERNAME:PASSWORD@localhost:5432/vacation_rentals
```

Install and start Ollama separately, then download the configured model:

```powershell
ollama pull llama3.2:3b
```

Create the database named in `DATABASE_URL` before initializing the schema.
From the project root, run:

```powershell
$env:PYTHONPATH = "backend"
python -m app.db.init_db
python -m app.db.seed
uvicorn app.main:app --reload --app-dir backend
```

The API documentation is available at `http://127.0.0.1:8000/docs`; the health
check is at `http://127.0.0.1:8000/health`.

## Availability and amenities

Properties are treated as available unless an unavailable period is recorded.
Add or inspect blocked date ranges with
`POST /properties/{property_id}/unavailability` and
`GET /properties/{property_id}/unavailability`; remove one with
`DELETE /properties/{property_id}/unavailability/{period_id}`. Date ranges use
check-in-inclusive, check-out-exclusive semantics. Search requires both dates
or neither. Amenity searches require every requested amenity to match. The
existing `has_pool` field also satisfies pool amenity searches.

## Tests

Run the backend unit tests without connecting to PostgreSQL or Ollama:

```powershell
$env:PYTHONPATH = "backend"
python -m unittest discover -s backend\tests -v
```

`test_db_connection.py` and `backend\test_requirement_extractor.py` are manual
integration checks that require their respective external services.