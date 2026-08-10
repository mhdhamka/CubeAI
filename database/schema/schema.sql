-- ============================================================
-- CubeAI Database Schema
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================
-- USERS
-- ============================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- SOLVES
-- ============================================================

CREATE TABLE solves (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID REFERENCES users(id)
        ON DELETE CASCADE,

    scramble TEXT NOT NULL,

    solution TEXT,

    move_count INTEGER,

    solve_time_ms INTEGER,

    solver VARCHAR(50),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT positive_move_count
        CHECK (move_count IS NULL OR move_count >= 0),

    CONSTRAINT positive_solve_time
        CHECK (solve_time_ms IS NULL OR solve_time_ms >= 0)
);


-- ============================================================
-- CUBE SCANS
-- ============================================================

CREATE TABLE cube_scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID REFERENCES users(id)
        ON DELETE CASCADE,

    image_path TEXT,

    detected_state JSONB,

    confidence REAL,

    status VARCHAR(30) NOT NULL DEFAULT 'pending',

    error_message TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    completed_at TIMESTAMPTZ,

    CONSTRAINT valid_confidence
        CHECK (
            confidence IS NULL
            OR (confidence >= 0 AND confidence <= 1)
        )
);


-- ============================================================
-- AI COACH SESSIONS
-- ============================================================

CREATE TABLE coach_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID REFERENCES users(id)
        ON DELETE CASCADE,

    solve_id UUID REFERENCES solves(id)
        ON DELETE SET NULL,

    question TEXT NOT NULL,

    response TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_solves_user_id
    ON solves(user_id);

CREATE INDEX idx_solves_created_at
    ON solves(created_at);

CREATE INDEX idx_cube_scans_user_id
    ON cube_scans(user_id);

CREATE INDEX idx_cube_scans_created_at
    ON cube_scans(created_at);

CREATE INDEX idx_coach_sessions_user_id
    ON coach_sessions(user_id);

CREATE INDEX idx_coach_sessions_solve_id
    ON coach_sessions(solve_id);