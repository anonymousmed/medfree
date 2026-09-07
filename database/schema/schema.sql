-- =============================================================================
-- MEDFREE — Reference PostgreSQL schema (ERP-style, for docs and DBA review).
-- The source of truth is the SQLAlchemy + Alembic setup under apps/api.
-- This file is kept conceptually identical for documentation and as a deploy
-- reference for managed PostgreSQL.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- IDENTITY & RBAC
-- ---------------------------------------------------------------------------
CREATE TABLE users (
    id            BIGSERIAL PRIMARY KEY,
    supabase_id   VARCHAR(255) UNIQUE NOT NULL,
    email         VARCHAR(255) UNIQUE,
    display_name  VARCHAR(255),
    avatar_url    VARCHAR(512),
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE roles (
    id    SERIAL PRIMARY KEY,
    name  VARCHAR(50) UNIQUE NOT NULL   -- student/contributor/reviewer/medical_reviewer/moderator/content_admin/super_admin
);

CREATE TABLE user_roles (
    id      SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role    VARCHAR(50) NOT NULL,
    UNIQUE (user_id, role)
);

-- ---------------------------------------------------------------------------
-- CURRICULUM (subjects/topics — not hard-coded)
-- ---------------------------------------------------------------------------
CREATE TABLE subjects (
    id          SERIAL PRIMARY KEY,
    slug        VARCHAR(100) UNIQUE NOT NULL,
    title       VARCHAR(200) NOT NULL,
    description TEXT,
    icon        VARCHAR(50),
    color       VARCHAR(20),
    sort_order  INT NOT NULL DEFAULT 0,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE topics (
    id                  SERIAL PRIMARY KEY,
    subject_id          INT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    slug                VARCHAR(150) NOT NULL,
    title               VARCHAR(200) NOT NULL,
    summary             TEXT,
    learning_objectives TEXT,
    content_markdown    TEXT,
    sort_order          INT NOT NULL DEFAULT 0,
    is_published        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (subject_id, slug)
);

-- ---------------------------------------------------------------------------
-- LICENSING / RIGHTS
-- ---------------------------------------------------------------------------
CREATE TABLE licenses (
    id                   SERIAL PRIMARY KEY,
    name                 VARCHAR(100) UNIQUE NOT NULL,
    license_url          VARCHAR(500),
    commercial_allowed   BOOLEAN NOT NULL DEFAULT FALSE,
    modification_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    redistribution_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    attribution_required BOOLEAN NOT NULL DEFAULT TRUE,
    sharealike_required  BOOLEAN NOT NULL DEFAULT FALSE,
    ai_ingestion_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    notes                TEXT
);

CREATE TABLE authors (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(200) NOT NULL,
    affiliation VARCHAR(300),
    website    VARCHAR(500)
);

-- ---------------------------------------------------------------------------
-- RESOURCES (admin-only upload enforced at the backend)
-- ---------------------------------------------------------------------------
CREATE TABLE resources (
    id                   SERIAL PRIMARY KEY,
    title                VARCHAR(300) NOT NULL,
    resource_type        VARCHAR(60) NOT NULL,      -- book/pdf/epub/image/diagram/3d/mcq/viva/flashcard/practical/...
    creator              VARCHAR(200),
    publisher            VARCHAR(200),
    source_url           VARCHAR(500),
    local_storage_key    VARCHAR(500),
    license_id           INT REFERENCES licenses(id),
    rights_status        VARCHAR(40) NOT NULL DEFAULT 'review_required',
    ai_usage_status      VARCHAR(20) NOT NULL DEFAULT 'unknown',  -- true/false/unknown
    attribution_text     TEXT,
    review_status        VARCHAR(40) NOT NULL DEFAULT 'draft',
    medical_review_status VARCHAR(40) NOT NULL DEFAULT 'pending',
    visibility           VARCHAR(20) NOT NULL DEFAULT 'private',  -- public/private/unlisted
    verified_by          VARCHAR(100),
    is_active            BOOLEAN NOT NULL DEFAULT TRUE,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE resource_versions (
    id           SERIAL PRIMARY KEY,
    resource_id  BIGINT NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
    version_label VARCHAR(50) NOT NULL,
    storage_key  VARCHAR(500),
    checksum     VARCHAR(64),
    change_note  TEXT,
    created_by   VARCHAR(100)
);

CREATE TABLE books (
    id             SERIAL PRIMARY KEY,
    resource_id    BIGINT REFERENCES resources(id),
    author_id      INT REFERENCES authors(id),
    title          VARCHAR(300) NOT NULL,
    edition        VARCHAR(100),
    publisher      VARCHAR(200),
    isbn           VARCHAR(50),
    year           INT,
    subject_slug   VARCHAR(100),
    reading_progress INT NOT NULL DEFAULT 0
);

CREATE TABLE book_chapters (
    id           SERIAL PRIMARY KEY,
    book_id      BIGINT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    title        VARCHAR(300) NOT NULL,
    chapter_index INT NOT NULL DEFAULT 0,
    topic_slug   VARCHAR(150),
    content_key  VARCHAR(500)
);

-- ---------------------------------------------------------------------------
-- HUMAN ATLAS (first-class system, centerpiece)
-- ---------------------------------------------------------------------------
CREATE TABLE anatomical_regions (
    id        SERIAL PRIMARY KEY,
    slug      VARCHAR(100) UNIQUE NOT NULL,
    name      VARCHAR(150) NOT NULL,
    parent_id INT REFERENCES anatomical_regions(id),
    sort_order INT NOT NULL DEFAULT 0
);

CREATE TABLE anatomical_systems (
    id    SERIAL PRIMARY KEY,
    slug  VARCHAR(100) UNIQUE NOT NULL,
    name  VARCHAR(150) NOT NULL,
    icon  VARCHAR(50),
    sort_order INT NOT NULL DEFAULT 0
);

CREATE TABLE anatomical_structures (
    id                  SERIAL PRIMARY KEY,
    stable_structure_id VARCHAR(120) UNIQUE,
    preferred_name      VARCHAR(200) NOT NULL,
    latin_name          VARCHAR(200),
    synonyms            TEXT,
    region_id           INT REFERENCES anatomical_regions(id),
    system_id           INT REFERENCES anatomical_systems(id),
    parent_id           INT REFERENCES anatomical_structures(id),
    description         TEXT,
    clinical_notes      TEXT,
    surface_anatomy     TEXT,
    embryology          TEXT,
    histology           TEXT,
    radiology           TEXT,
    status              VARCHAR(30) NOT NULL DEFAULT 'review_required'
);

CREATE TABLE anatomical_relationships (
    id           SERIAL PRIMARY KEY,
    structure_a  BIGINT NOT NULL REFERENCES anatomical_structures(id) ON DELETE CASCADE,
    structure_b  BIGINT NOT NULL REFERENCES anatomical_structures(id) ON DELETE CASCADE,
    relation_type VARCHAR(50) NOT NULL,       -- supplies / drains / medial_to / ...
    description  TEXT,
    source       VARCHAR(300)
);

CREATE TABLE atlas_models (
    id                  SERIAL PRIMARY KEY,
    title               VARCHAR(200) NOT NULL,
    source              VARCHAR(300),
    license             VARCHAR(100),
    creator             VARCHAR(200),
    file_key            VARCHAR(500) NOT NULL,
    format              VARCHAR(20) NOT NULL DEFAULT 'glb',
    version             VARCHAR(30) NOT NULL DEFAULT '1.0.0',
    checksum            VARCHAR(64),
    region_id           INT REFERENCES anatomical_regions(id),
    optimization_status VARCHAR(40) NOT NULL DEFAULT 'pending',
    review_status       VARCHAR(40) NOT NULL DEFAULT 'review_required',
    default_visibility  JSONB,
    is_published        BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE atlas_model_parts (
    id            SERIAL PRIMARY KEY,
    model_id      BIGINT NOT NULL REFERENCES atlas_models(id) ON DELETE CASCADE,
    structure_id  BIGINT REFERENCES anatomical_structures(id) ON DELETE SET NULL,
    mesh_name     VARCHAR(200) NOT NULL,
    material      VARCHAR(200),
    visibility    BOOLEAN NOT NULL DEFAULT TRUE,
    highlight_config JSONB
);

CREATE TABLE atlas_annotations (
    id           SERIAL PRIMARY KEY,
    model_id     BIGINT NOT NULL REFERENCES atlas_models(id) ON DELETE CASCADE,
    structure_id BIGINT REFERENCES anatomical_structures(id) ON DELETE SET NULL,
    label        VARCHAR(200) NOT NULL,
    description  TEXT,
    position_x   DOUBLE PRECISION,
    position_y   DOUBLE PRECISION,
    position_z   DOUBLE PRECISION
);

CREATE TABLE atlas_reviews (
    id          SERIAL PRIMARY KEY,
    model_id    BIGINT NOT NULL REFERENCES atlas_models(id) ON DELETE CASCADE,
    reviewer    VARCHAR(150) NOT NULL,
    review_type VARCHAR(40) NOT NULL,   -- medical / quality / rights
    result      VARCHAR(40) NOT NULL,   -- approved / rejected / changes_requested
    notes       TEXT
);

-- ---------------------------------------------------------------------------
-- PRACTICE
-- ---------------------------------------------------------------------------
CREATE TABLE questions (
    id               SERIAL PRIMARY KEY,
    subject_slug     VARCHAR(100) NOT NULL,
    topic_slug       VARCHAR(150),
    stem             TEXT NOT NULL,
    qtype            VARCHAR(30) NOT NULL DEFAULT 'single_best_answer',
    explanation      TEXT,
    reference        VARCHAR(300),
    difficulty       VARCHAR(20) NOT NULL DEFAULT 'medium',
    learning_objective TEXT,
    reviewer         VARCHAR(150),
    image_url        VARCHAR(500),
    is_published     BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE question_options (
    id          SERIAL PRIMARY KEY,
    question_id BIGINT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    option_text TEXT NOT NULL,
    is_correct  BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order  INT NOT NULL DEFAULT 0
);

CREATE TABLE viva_questions (
    id           SERIAL PRIMARY KEY,
    subject_slug VARCHAR(100) NOT NULL,
    topic_slug   VARCHAR(150),
    prompt       TEXT NOT NULL,
    model_answer TEXT NOT NULL,
    key_points   TEXT,
    difficulty   VARCHAR(20) NOT NULL DEFAULT 'medium',
    is_published BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE flashcards (
    id           SERIAL PRIMARY KEY,
    subject_slug VARCHAR(100) NOT NULL,
    topic_slug   VARCHAR(150),
    front        TEXT NOT NULL,
    back         TEXT NOT NULL,
    card_type    VARCHAR(30) NOT NULL DEFAULT 'basic'
);

CREATE TABLE practicals (
    id           SERIAL PRIMARY KEY,
    subject_slug VARCHAR(100) NOT NULL,
    title        VARCHAR(250) NOT NULL,
    objective    TEXT,
    procedure    TEXT,
    video_url    VARCHAR(500),
    is_published BOOLEAN NOT NULL DEFAULT FALSE
);

-- ---------------------------------------------------------------------------
-- PROGRESS (per user)
-- ---------------------------------------------------------------------------
CREATE TABLE user_progress (
    id          SERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_slug VARCHAR(100) NOT NULL,
    topic_slug  VARCHAR(150),
    state       VARCHAR(30) NOT NULL DEFAULT 'not_started',
    mastery     DOUBLE PRECISION NOT NULL DEFAULT 0,
    time_spent_seconds INT NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE question_attempts (
    id                SERIAL PRIMARY KEY,
    user_id           BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question_id       BIGINT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    selected_option_id INT,
    is_correct        BOOLEAN NOT NULL DEFAULT FALSE,
    score             DOUBLE PRECISION,
    answered_at       TIMESTAMPTZ
);

CREATE TABLE viva_attempts (
    id              SERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    viva_question_id BIGINT NOT NULL REFERENCES viva_questions(id) ON DELETE CASCADE,
    student_answer  TEXT,
    self_rating     INT,
    completed_at    TIMESTAMPTZ
);

CREATE TABLE flashcard_reviews (
    id              SERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    card_id         BIGINT NOT NULL REFERENCES flashcards(id) ON DELETE CASCADE,
    quality         INT NOT NULL DEFAULT 0,
    ease_factor     DOUBLE PRECISION NOT NULL DEFAULT 2.5,
    interval_days   INT NOT NULL DEFAULT 0,
    due_at          TIMESTAMPTZ NOT NULL,
    review_count    INT NOT NULL DEFAULT 0,
    last_reviewed_at TIMESTAMPTZ
);

CREATE TABLE study_sessions (
    id               SERIAL PRIMARY KEY,
    user_id          BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    started_at       TIMESTAMPTZ,
    ended_at         TIMESTAMPTZ,
    duration_seconds INT NOT NULL DEFAULT 0,
    subject_slug     VARCHAR(100)
);

-- ---------------------------------------------------------------------------
-- NOTES: index key FK columns used in hot paths / search.
-- (trigram index for search is added by the migration as well.)
-- ---------------------------------------------------------------------------
CREATE INDEX idx_resources_type ON resources(resource_type);
CREATE INDEX idx_resources_visibility ON resources(visibility, review_status);
CREATE INDEX idx_anatomy_name ON anatomical_structures(preferred_name);
CREATE INDEX idx_topics_subject ON topics(subject_id);
CREATE INDEX idx_question_attempts_user ON question_attempts(user_id);
CREATE INDEX idx_flashcard_reviews_due ON flashcard_reviews(user_id, due_at);
