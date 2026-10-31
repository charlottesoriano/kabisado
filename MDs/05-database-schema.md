# 05 — Database Schema

Postgres schema for the Reviewer Generator, hosted on Supabase with pgvector. This file is the source of truth for tables, constraints, indexes and access rules; `00-MVP.md` and `03-backend.md` summarise it.

## 1. Access and connection

- **Only the backend connects to Postgres.** The API and the job worker use SQLAlchemy 2 (async) + asyncpg through Supabase's **session pooler** (`DATABASE_URL`, `WORKER_DATABASE_URL`). Transactions, pgvector SQL and the Procrastinate job queue need a real Postgres connection, not the Supabase REST API.
- Clients (web and mobile) never talk to the database. They call the FastAPI API with a Clerk session token.
- All tables live in a private schema, **`app`**, which is not in the Supabase Data API's exposed schemas.
- The backend connects as a privileged role, so **every query is scoped to the authenticated Clerk user id** (directly or through `documents.user_id`). Another user's row returns 404.
- Second lock: RLS is enabled on every table with **no policies**, and the `anon` and `authenticated` roles have no grants on `app`. Even if the schema were exposed, client keys could read or write nothing.
- Migrations are managed with Alembic (`backend/migrations/`).

## 2. Conventions

- User ids are **Clerk ids** (`text`, e.g. `user_2abc…`), not UUIDs. Every other primary key is a `uuid` (`gen_random_uuid()`).
- Timestamps are `timestamptz`, stored in UTC. "Today" is computed in the user's `profiles.timezone`.
- Allowed values use `CHECK` constraints instead of enums, so adding a value is a one-line migration.
- Deleting a profile or a document cascades to everything under it. The backend also deletes the matching files in Storage (`uploads/{user_id}/{document_id}.pdf`).

## 3. Tables

Twelve tables.

| Table | Purpose |
| --- | --- |
| `profiles` | One row per Clerk user, synced by webhooks (or created by `GET /me`) |
| `documents` | A deck: one uploaded PDF or one pasted note |
| `chunks` | Sections of a document's text, with embeddings |
| `cards` | Flashcards, MCQs and problem templates |
| `card_states` | SM-2 schedule per user per card |
| `reviews` | Log of every rating (from review, quiz or problem) |
| `attempts` | A quiz or problem-set session (`kind`) |
| `attempt_questions` | Questions in a quiz attempt and their option shuffle |
| `problem_instances` | The numbers (or code variant) a student saw, with the computed answer kept server-side |
| `attempt_answers` | Each answer and its result |
| `generation_runs` | Metrics for each generation job |
| `webhook_events` | Processed Clerk webhook ids, for idempotency |

## 4. Migration (SQL)

```sql
create extension if not exists vector;
create extension if not exists pgcrypto;

create schema if not exists app;

-- Profiles ---------------------------------------------------------------
create table app.profiles (
  id             text primary key,                       -- Clerk user id (token `sub`)
  email          text,
  display_name   text,
  timezone       text not null default 'Asia/Manila',
  reminder_time  time,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

-- Documents (decks) ------------------------------------------------------
create table app.documents (
  id              uuid primary key default gen_random_uuid(),
  user_id         text not null references app.profiles(id) on delete cascade,
  title           text not null check (char_length(title) between 1 and 120),
  source_type     text not null check (source_type in ('pdf', 'text')),
  file_path       text,                                   -- set for pdf
  raw_text        text,                                   -- set for text
  page_count      int check (page_count between 1 and 50),
  generate_kinds  text[] not null default '{flashcard,mcq,problem}',
  status          text not null default 'queued'
                  check (status in ('queued', 'extracting', 'chunking', 'generating', 'ready', 'failed')),
  error_code      text,
  progress_done   int not null default 0,
  progress_total  int not null default 0,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  check (
    (source_type = 'pdf'  and file_path is not null) or
    (source_type = 'text' and raw_text  is not null and char_length(raw_text) between 200 and 100000)
  ),
  check (progress_done between 0 and progress_total)
);

-- Chunks -----------------------------------------------------------------
create table app.chunks (
  id               uuid primary key default gen_random_uuid(),
  document_id      uuid not null references app.documents(id) on delete cascade,
  idx              int not null,
  heading          text,
  content          text not null,
  token_count      int not null,
  page_start       int not null,
  page_end         int not null check (page_end >= page_start),
  is_quantitative  boolean not null default false,
  is_programming   boolean not null default false,
  embedding        vector(384),
  gen_status       text not null default 'pending'
                   check (gen_status in ('pending', 'done', 'failed')),
  unique (document_id, idx)
);

-- Cards ------------------------------------------------------------------
create table app.cards (
  id           uuid primary key default gen_random_uuid(),
  document_id  uuid not null references app.documents(id) on delete cascade,
  chunk_id     uuid references app.chunks(id) on delete set null,
  type         text not null check (type in ('flashcard', 'mcq', 'problem')),
  payload      jsonb not null,                         -- shape per type, see §6
  topic        text,
  origin       text not null default 'bulk' check (origin in ('bulk', 'topic')),
  flagged      boolean not null default false,
  flag_reason  text check (flag_reason in ('wrong_answer', 'unclear', 'off_topic')),
  edited       boolean not null default false,
  model        text,                                   -- generator provider/model; the verifier excludes it
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);

-- SM-2 state -------------------------------------------------------------
create table app.card_states (
  user_id           text not null references app.profiles(id) on delete cascade,
  card_id           uuid not null references app.cards(id) on delete cascade,
  ease              numeric(4,2) not null default 2.50 check (ease >= 1.30),
  interval_days     int not null default 0 check (interval_days >= 0),
  repetitions       int not null default 0 check (repetitions >= 0),
  due_at            timestamptz not null default now(),
  last_reviewed_at  timestamptz,
  primary key (user_id, card_id)
);

create table app.reviews (
  id               uuid primary key default gen_random_uuid(),
  user_id          text not null references app.profiles(id) on delete cascade,
  card_id          uuid not null references app.cards(id) on delete cascade,
  rating           smallint not null check (rating between 0 and 3),   -- Again, Hard, Good, Easy
  source           text not null check (source in ('review', 'quiz', 'problem')),
  interval_before  int not null,
  interval_after   int not null,
  reviewed_at      timestamptz not null default now()
);

-- Quiz and problem sessions ----------------------------------------------
create table app.attempts (
  id           uuid primary key default gen_random_uuid(),
  user_id      text not null references app.profiles(id) on delete cascade,
  document_id  uuid not null references app.documents(id) on delete cascade,
  kind         text not null check (kind in ('quiz', 'problem_set')),
  length       smallint not null,
  score        int check (score >= 0),
  total        int check (total >= 0),
  started_at   timestamptz not null default now(),
  finished_at  timestamptz,
  check ((kind = 'quiz' and length in (5, 10, 20)) or (kind = 'problem_set' and length in (5, 10))),
  check (score is null or total is null or score <= total)
);

create table app.attempt_questions (
  attempt_id    uuid not null references app.attempts(id) on delete cascade,
  position      smallint not null,
  card_id       uuid not null references app.cards(id) on delete cascade,
  option_order  smallint[] not null,     -- shown index -> original index, e.g. {2,0,3,1}
  primary key (attempt_id, position),
  unique (attempt_id, card_id)
);

create table app.problem_instances (
  id               uuid primary key default gen_random_uuid(),
  attempt_id       uuid not null references app.attempts(id) on delete cascade,
  card_id          uuid not null references app.cards(id) on delete cascade,
  variables        jsonb not null,       -- values drawn for this instance
  variant_index    smallint,             -- programming problems: which stored variant was shown
  answer_value     numeric,              -- computed by SymPy/Pint; never sent before grading
  answer_unit      text,
  hints_shown      smallint not null default 0,
  solution_viewed  boolean not null default false,
  created_at       timestamptz not null default now()
);

create table app.attempt_answers (
  id            uuid primary key default gen_random_uuid(),
  attempt_id    uuid not null references app.attempts(id) on delete cascade,
  card_id       uuid not null references app.cards(id) on delete cascade,
  instance_id   uuid references app.problem_instances(id) on delete cascade,
  chosen_index  smallint check (chosen_index between 0 and 3),   -- quiz: original option index
  answer_value  numeric,                                        -- problem: converted to the expected unit
  answer_unit   text,
  result        text not null check (result in ('correct', 'close', 'wrong')),
  hints_used    smallint not null default 0,
  explanation   text,                                           -- cached "Explain my mistake"
  answered_at   timestamptz not null default now()
);

-- One answer per quiz question per attempt; one answer per problem instance.
create unique index attempt_answers_quiz_once
  on app.attempt_answers (attempt_id, card_id) where instance_id is null;
create unique index attempt_answers_instance_once
  on app.attempt_answers (instance_id) where instance_id is not null;

-- Job metrics and webhooks -----------------------------------------------
create table app.generation_runs (
  id                 uuid primary key default gen_random_uuid(),
  document_id        uuid not null references app.documents(id) on delete cascade,
  started_at         timestamptz not null default now(),
  finished_at        timestamptz,
  provider_calls     jsonb not null default '{}',   -- {"groq": 12, "cerebras": 3}
  cards_kept         int not null default 0,
  cards_dropped      int not null default 0,
  template_failures  jsonb not null default '{}'    -- failures per verification check
);

create table app.webhook_events (
  svix_id      text primary key,
  event_type   text not null,
  received_at  timestamptz not null default now()
);
```

## 5. Indexes, RLS and grants

```sql
create index chunks_embedding_hnsw on app.chunks using hnsw (embedding vector_cosine_ops);
create index card_states_due       on app.card_states (user_id, due_at);
create index cards_doc_type        on app.cards (document_id, type) where not flagged;
create index answers_card_time     on app.attempt_answers (card_id, answered_at);
create index documents_user        on app.documents (user_id, created_at desc);
create index reviews_user_time     on app.reviews (user_id, reviewed_at);
create index attempts_user_doc     on app.attempts (user_id, document_id, started_at desc);

-- RLS on, no policies: client roles can never read or write.
alter table app.profiles          enable row level security;
alter table app.documents         enable row level security;
alter table app.chunks            enable row level security;
alter table app.cards             enable row level security;
alter table app.card_states       enable row level security;
alter table app.reviews           enable row level security;
alter table app.attempts          enable row level security;
alter table app.attempt_questions enable row level security;
alter table app.problem_instances enable row level security;
alter table app.attempt_answers   enable row level security;
alter table app.generation_runs   enable row level security;
alter table app.webhook_events    enable row level security;

revoke all on schema app from anon, authenticated;
revoke all on all tables in schema app from anon, authenticated;
```

## 6. Card payloads (`cards.payload`)

Validated by the Pydantic models in `03-backend.md` §5.3 and §5.6 before saving.

| Type | Payload |
| --- | --- |
| `flashcard` | `{front, back}` |
| `mcq` | `{question, options[4], answer_index, explanation}` (options in the model's order; shuffled per attempt) |
| `problem` (numeric) | `{subject, question, variables {name: {min, max, step, unit}}, answer_formula, answer_unit, tolerance, constraints, hints, solution_steps, common_mistakes}` |
| `problem` (programming) | `{subject: "programming", language, kind, code_template, variables, options?, tests[], explanation, variants: [{values, code, expected_output}]}` |

## 7. Rules enforced by the schema

- Ease never drops below 1.30; a score never exceeds its total.
- Quiz length is 5, 10 or 20; problem-set length is 5 or 10.
- One answer per quiz question per attempt, and one per problem instance (partial unique indexes above).
- A PDF document has a file path; a text document has 200–100,000 characters of text.
- Deleting a profile or document cascades to chunks, cards, states, reviews, attempts and answers.

## 8. Query: weakest topics

Used by `GET /dashboard` (`03-backend.md` §8): answers from the last 30 days, grouped by the card's topic (falling back to the chunk heading), topics with at least 3 answers, lowest accuracy first, top 3.

```sql
select coalesce(c.topic, ch.heading, 'Untitled')              as topic,
       count(*)                                               as answered,
       avg((aa.result = 'correct')::int)::numeric(5,4)        as accuracy
from app.attempt_answers aa
join app.attempts a  on a.id = aa.attempt_id
join app.cards c     on c.id = aa.card_id
left join app.chunks ch on ch.id = c.chunk_id
where a.user_id = :user_id
  and aa.answered_at >= now() - interval '30 days'
group by 1
having count(*) >= 3
order by accuracy asc, answered desc
limit 3;
```
