import csv
import io
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
import psycopg

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://ingestion:ingestion@localhost:5432/ingestion_local",
)

# On camera: add "admin1" to this set (1–3 line change).
REQUIRED_COLUMNS = {"school_id", "name", "lat", "lon"}

app = FastAPI(title="Partner dataset ingestion")


def get_conn():
    return psycopg.connect(DATABASE_URL)


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="CSV file required")

    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="File must be UTF-8 CSV") from exc

    reader = csv.DictReader(io.StringIO(text))
    columns = set(reader.fieldnames or [])
    rows = list(reader)
    row_count = len(rows)

    now = datetime.now(timezone.utc)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO dataset_states (filename, row_count, status, created_at, updated_at)
                VALUES (%s, NULL, 'received', %s, %s)
                RETURNING id
                """,
                (file.filename, now, now),
            )
            dataset_id = cur.fetchone()[0]
            conn.commit()

            missing = REQUIRED_COLUMNS - columns
            if missing:
                status = "failed"
                final_row_count = None
                detail = f"missing columns: {sorted(missing)}"
            else:
                status = "validated"
                final_row_count = row_count
                detail = "ok"

            updated = datetime.now(timezone.utc)
            cur.execute(
                """
                UPDATE dataset_states
                SET status = %s, row_count = %s, updated_at = %s
                WHERE id = %s
                """,
                (status, final_row_count, updated, dataset_id),
            )
            conn.commit()

    return {
        "id": dataset_id,
        "filename": file.filename,
        "status": status,
        "row_count": final_row_count,
        "detail": detail,
    }


@app.get("/health")
def health():
    return {"status": "ok"}
