# Reviewer Generator — MVP Technical Documentation

Oct 23, 2026 · @Cha

## Overview

Students upload notes or a PDF; the app turns them into flashcards, multiple-choice quizzes and auto-graded problem sets, schedules reviews with spaced repetition (SM-2), and tracks scores per deck and topic. It ships as a web app (Next.js) and a mobile app (Expo) on one Python (FastAPI) backend, with Clerk for sign-in and Supabase for Postgres, pgvector and file storage. Every AI component runs on free tiers or local models.

**Core loop:** upload → extract → chunk → embed → generate and verify → review → score.

RAG is used where retrieval adds value: topic-targeted generation ("questions about photosynthesis") and grounded explanations of wrong answers. Bulk generation walks every chunk in order and does not need vector search.

**The AI never does graded arithmetic.** For problem sets the model writes a template with a formula; the backend computes every answer with SymPy and Pint, and a second AI provider independently checks each template before it is saved.

**MVP scope**

- In: text-based PDF or pasted notes; flashcards, MCQs and problem sets (numeric answers with units); programming problems that don't run student code (predict the output, fill in the blank, find the bug, order the lines), with answers verified by running code in a sandbox at generation time; source link per card; SM-2 review; quiz and problem scoring; dashboard; topic generation; explain my mistake; flag and edit cards.
- Out (later): scanned PDFs/OCR, formula-heavy PDFs via a vision model, balancing chemical equations, symbolic answers, "write a function" coding problems (student code run in the browser with Pyodide), deck sharing, FSRS, chat with notes, offline review.

Detailed specs live in the repo's `docs/` folder: stack, flows, backend, frontend, database schema, use cases, and backend and frontend test cases (01–08).

## Tech stack

One monorepo holds a Python (FastAPI) backend, a Next.js web app and an Expo mobile app. Clerk handles sign-in; Supabase provides Postgres with pgvector and file storage; free LLM APIs do the AI work with automatic fallback.

| Layer | Choice | Why |
| --- | --- | --- |
| Backend API | Python 3.12, FastAPI, Pydantic v2, `uv` | Owns all business rules; OpenAPI schema generates the TypeScript client |
| Database access | SQLAlchemy 2 (async) + asyncpg, direct connection via Supabase's session pooler | Transactions, pgvector SQL and the job queue need real Postgres, not the Supabase REST API |
| Migrations | Alembic | Tables live in a private `app` schema the REST API can't reach |
| Background jobs | Procrastinate (Postgres-backed queue) | Generation for a long PDF outlasts a request; no Redis needed |
| Auth | Clerk (`@clerk/nextjs`, `@clerk/clerk-expo`); backend verifies the session JWT | Prebuilt sign-in; webhooks sync user profiles |
| Database | Supabase Postgres + pgvector (384 dimensions) | Relational data and embeddings in one place |
| File storage | Supabase Storage, private `uploads` bucket | Backend issues 10-minute signed upload URLs |
| PDF extraction | PyMuPDF | Text and page numbers from text-based PDFs |
| LLM gateway | LiteLLM | One interface; falls back to the next free provider on rate limits |
| LLM providers (free) | Groq and Cerebras (Llama 3.3 70B), Gemini Flash, OpenRouter free models; Ollama locally | Generation, verification on a different provider, explanations |
| Structured output | Instructor + Pydantic | Validates AI JSON and retries when it's invalid |
| Embeddings | `fastembed` with `bge-small-en-v1.5`, run in-process | Free, no rate limits, CPU only |
| Problem math | SymPy + Pint | Safe formula evaluation and unit-aware grading |
| Code execution | Judge0 hosted API (free tier) at generation time; `wasmtime` WebAssembly runner as a Python-only fallback | Verifies programming-problem answers; never `exec()` in the backend |
| Spaced repetition | SM-2 variant in Python | Same scheduling for web and mobile; clients never compute it |
| Web frontend | Next.js (App Router), TypeScript, Tailwind, shadcn/ui, KaTeX |  |
| Mobile frontend | React Native with Expo (Expo Router), NativeWind, KaTeX in a WebView | Same language and patterns as the web app |
| Data fetching | TanStack Query + client generated from OpenAPI | Same typed hooks on both apps |
| Testing | pytest, Hypothesis, Vitest, React Testing Library, MSW, Playwright, Maestro |  |
| Hosting | Vercel (web), Render/Fly/Koyeb free tier (API + worker), Expo EAS (mobile) | Each deploys its own folder from the monorepo |

&#91;embedded content: architecture · 4 components + Supabase\]

Both apps sign in with Clerk and call the FastAPI backend with the Clerk token; files go straight to Supabase Storage through signed URLs. Slow AI work runs in the background worker, which calls the free LLM APIs and writes results to Postgres.

### Repo layout and code sharing

- `backend/`: FastAPI app, job worker, Alembic migrations and tests (its own `pyproject.toml` and `uv.lock`).
- `apps/web`: Next.js app, deployed to Vercel with `apps/web` as the root directory.
- `apps/mobile`: Expo app, built with EAS.
- `packages/api-client`: TypeScript types and TanStack Query hooks generated from the backend's OpenAPI schema; CI fails if it's out of date.
- `packages/ui-tokens`: colors, spacing and type scale for Tailwind and NativeWind.
- `docs/`: the eight spec files.
- Business rules (scheduling, grading, quiz sampling) live only in the backend. UI components are not shared; each app builds its own screens on the shared client.

### Mobile-specific notes

- Upload uses `expo-document-picker`, then the same signed-URL upload as the web app.
- Flip and swipe gestures in review use `react-native-reanimated` and `react-native-gesture-handler`.
- Daily "cards due" reminders use `expo-notifications` (local notifications are enough for the MVP).
- Offline review is out of scope for the MVP; the shared SM-2 package makes it possible later.

## Data schema

Twelve tables live in a private Postgres schema, `app`, that Supabase's REST API doesn't expose; only the backend connects, and it scopes every query to the Clerk user id. User ids are Clerk ids (text such as `user_2abc…`), not UUIDs. The full SQL migration is in `docs/05-database-schema.md`.

| Table | Purpose | Key columns |
| --- | --- | --- |
| `profiles` | One row per Clerk user, synced by webhooks | `id` (Clerk id), `email`, `display_name`, `timezone` (default Asia/Manila), `reminder_time` |
| `documents` | A deck: one upload or pasted note | `user_id`, `title`, `source_type` (pdf/text), `file_path`, `raw_text`, `page_count` (≤ 50), `generate_kinds`, `status`, `error_code`, `progress_done/total` |
| `chunks` | Sections of the notes | `document_id`, `idx`, `heading`, `content`, `page_start/end`, `is_quantitative`, `embedding vector(384)`, `gen_status` (for resumable jobs) |
| `cards` | Flashcards, MCQs and problem templates | `document_id`, `chunk_id`, `type` (flashcard/mcq/problem), `payload` jsonb, `topic`, `origin` (bulk/topic), `flagged`, `edited`, `model` |
| `card_states` | SM-2 schedule per user per card | PK (`user_id`, `card_id`), `ease` (≥ 1.30), `interval_days`, `repetitions`, `due_at` |
| `reviews` | Log of every rating | `user_id`, `card_id`, `rating` (0–3), `source` (review/quiz/problem), `interval_before/after` |
| `attempts` | A quiz or problem session | `user_id`, `document_id`, `kind` (quiz/problem\_set), `length`, `score`, `total`, `finished_at` |
| `attempt_questions` | Quiz questions and their option shuffle | (`attempt_id`, `position`), `card_id`, `option_order` |
| `problem_instances` | Numbers a student saw, with the computed answer kept server-side | `attempt_id`, `card_id`, `variables`, `answer_value`, `answer_unit`, `hints_shown` |
| `attempt_answers` | Each answer and its result | `attempt_id`, `card_id`, `instance_id`, `chosen_index`, `answer_value`, `result` (correct/close/wrong), `hints_used`, `explanation` (cached) |
| `generation_runs` | Job metrics | provider calls, cards kept/dropped, template failures per check |
| `webhook_events` | Makes Clerk webhooks idempotent | `svix_id` |

**Rules the schema enforces**

- Deleting a profile or deck cascades to everything under it; the backend also deletes the files in Storage.
- One answer per quiz question per attempt (partial unique index); one answer per problem instance.
- Allowed values are `CHECK` constraints (easier to extend than enums); ease can't drop below 1.30 and a score can't exceed its total.
- RLS is enabled on every table with no policies, and client roles have no grants: a second lock if the schema were ever exposed.

**Key indexes:** HNSW on `chunks.embedding`; `card_states (user_id, due_at)` for "due today"; `cards (document_id, type)` where not flagged; `attempt_answers (card_id, answered_at)` for quiz weighting.

**Card payloads:** flashcard `{front, back}`; MCQ `{question, options[4], answer_index, explanation}`; problem `{question with {variables}, variables {min, max, step, unit}, answer_formula, answer_unit, tolerance, hints, solution_steps, common_mistakes}`; programming problem `{language, kind, code_template, variables, options?, tests[], explanation, variants[]}`.

## User flows

Eleven flows cover the MVP and work the same on web and mobile. Upload and generation run once per deck; review, quiz and problem practice repeat daily. Full use cases with error paths are in `docs/06-use-cases.md`.

### 1. Sign up and sign in

1. Student signs in with Clerk (Google or email).
2. Clerk's `user.created` webhook creates the profile; `GET /me` also creates it if the webhook hasn't arrived yet.
3. New users land on an empty dashboard with "Upload your notes"; returning users see their dashboard.
4. Deleting the account in Clerk removes all of the student's data and files.

### 2. Upload a PDF or paste notes

1. Student picks a PDF (≤ 20 MB, ≤ 50 pages) or pastes 200–100,000 characters, sets a title and chooses what to generate.
2. For a PDF, the backend returns a signed URL; the app uploads the file straight to Storage, then calls `POST /documents/{id}/process`.
3. The backend checks the file and queues the generation job; the app opens the deck page with progress.

### 3. Generation (background)

1. **Extract:** text per page; almost no text means a scanned PDF and the job fails with a clear message.
2. **Chunk and embed:** strip headers and footers, split by headings into 500–800-token chunks, embed locally.
3. **Generate:** flashcards and MCQs per chunk; problem templates for quantitative chunks. Output is schema-validated, and rate limits fall back to the next free provider.
4. **Verify:** problem templates must pass formula, unit and sample checks plus an independent solve by a different provider.
5. **Finish:** deduplicate, schedule all cards as due now, mark the deck ready. Failed decks show Retry, which resumes from unfinished chunks.

### 4. Flashcard review

1. Student starts a review from the dashboard or a deck; the backend returns due cards, oldest first.
2. Student flips each card (tap, click or Space) and sees the answer and its source page.
3. Student rates Again / Hard / Good / Easy; the backend updates the SM-2 schedule and logs the review in one transaction.
4. Cards rated Again return at the end of the session; a summary shows what was reviewed and when cards are due next.

### 5. Quiz

1. Student picks a length (5, 10 or 20); the backend samples MCQs weighted toward past mistakes and shuffles the options. **No answers are sent until the student answers.**
2. Each answer is graded by the backend, which returns the correct option, explanation and source.
3. Results show the score, change since the last attempt and missed questions, with "Review missed as flashcards".

### 6. Explain my mistake

1. On a wrong quiz or problem answer, student taps Explain my mistake.
2. The backend retrieves the card's source chunk plus the closest chunks from the same deck and asks the LLM for a short explanation using only those.
3. The explanation is shown with page references and cached.

### 7. Generate cards on a topic

1. Student types a topic on the deck page.
2. The backend retrieves matching chunks; if none are close enough, it says the topic isn't in the notes.
3. Otherwise up to 8 new cards are generated from those chunks and scheduled as due now.

### 8. Problem set practice

1. Decks with verified templates show a Problem set tab; student starts a session.
2. The backend draws numbers for a template, stores the instance and its computed answer, and returns only the question.
3. Student enters a value and unit; hints and a step-by-step solution are available.
4. The backend converts units and grades within 1% (correct), 5% (close) or wrong, recognising common mistakes.
5. "Try a similar one" uses the same template with new numbers; results feed SM-2 and weakest topics.

### 9. Dashboard

- Cards due today (new and review), estimated minutes, 7-day accuracy, streak, decks with mastery and status, and the three weakest topics, all in the student's timezone.

### 10. Manage cards and decks

- Flag a card to hide it from sessions; edit a card (validated, and unflagged); rename or delete a deck (deleting removes its file and all its data).

### 11. Daily reminder (mobile)

- A local notification at the student's chosen time says how many cards are due and opens the review.
