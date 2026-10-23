CREATE TABLE IF NOT EXISTS dataset_states (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    row_count INTEGER,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
