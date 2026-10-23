# Partner dataset ingestion (local demo)

Local FastAPI service that accepts partner school CSV uploads, validates required columns, and records status in Postgres (`dataset_states`).

## What you need

- Docker Desktop (for local Postgres)
- Python 3.11+
- VS Code with the [REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client) extension
- DBeaver (optional, for inspecting `dataset_states`)

## 1. Start Postgres

```bash
docker compose up -d
```

This starts Postgres on port `5432` with database `ingestion_local` (user/password: `ingestion` / `ingestion`). The DDL in `sql/ddl.sql` is applied automatically on first boot.

If the table was not created (for example you reused an existing volume), apply it manually:

```bash
psql postgresql://ingestion:ingestion@localhost:5432/ingestion_local -f sql/ddl.sql
```

Or run the SQL in DBeaver against `ingestion_local`.

## 2. Create a virtualenv and install deps

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # if .env is missing
```

## 3. Run the API

From the project root (with the venv active):

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Or use the VS Code Run / Debug control on `app/main.py` if you have a launch config that runs uvicorn the same way.

Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

## 4. Install REST Client and send uploads

1. In VS Code: Extensions → search **REST Client** (humao.rest-client) → Install.
2. Open `requests.http`.
3. Click **Send Request** above each `POST` (after you make the on-camera change below).

Sample files:

- `data/schools_partner_batch_01.csv` — ~200 rows with `school_id`, `name`, `lat`, `lon`, `admin1`
- `data/schools_partner_batch_01_bad.csv` — same rows but **without** `admin1`

## On camera: what to change

In `app/main.py`, add `admin1` to `REQUIRED_COLUMNS` (about 1–3 lines), for example:

```python
REQUIRED_COLUMNS = {"school_id", "name", "lat", "lon", "admin1"}
```

Save, ensure uvicorn is running (reload or restart), then:

1. POST the good CSV → expect `validated` and `row_count` ≈ 200 in `dataset_states`.
2. POST the bad CSV → expect `failed` (missing `admin1`).

## Table shape

`dataset_states`: `id`, `filename`, `row_count`, `status`, `created_at`, `updated_at`

Status flow: insert as `received` → update to `validated` or `failed` (and set `updated_at`).

## Useful DBeaver query

```sql
SELECT filename, row_count, status, created_at, updated_at
FROM dataset_states
ORDER BY id;
```
# mercor-task
