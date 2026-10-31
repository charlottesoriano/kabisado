# 06 — Use Cases

One use case per flow in `02-user-flows.md`. **Actors:** Student (the signed-in user), Clerk (identity provider), System (FastAPI backend and job worker), LLM provider (free AI API).

Each use case lists preconditions, the main success scenario, alternate and exception flows (numbered by the step they branch from), postconditions and business rules. Test cases in `07-backend-test-cases.md` and `08-frontend-test-cases.md` reference these IDs.

---

## UC-01 Sign up and sign in
**Actor:** Student, Clerk · **Goal:** get into the app with an account.

**Preconditions:** none.

**Main success scenario**
1. Student opens the app and chooses Google or email sign-up.
2. Clerk creates the account and a session.
3. Clerk sends `user.created`; System verifies the Svix signature and creates the profile.
4. App calls `GET /me`; System returns the profile.
5. App shows the dashboard (empty state for a new user).

**Alternate flows**
- 3a. Webhook arrives after step 4: `GET /me` creates the profile; the later webhook updates it (no duplicate).
- 3b. Same webhook delivered twice: the second is ignored (`svix_id` already stored).
- 1a. Returning user signs in: step 3 is skipped; dashboard shows their data.

**Exceptions**
- 2a. Wrong password or unverified email: Clerk shows the error; nothing reaches System.
- 4a. Token expired or invalid: System returns 401; app gets a fresh token and retries once, then signs out.
- 3c. Bad webhook signature: System returns 400 and changes nothing.

**Postconditions:** profile exists with the Clerk user id; the session is valid.

**Business rules:** the user id comes only from the verified token's `sub`. Deleting the user in Clerk (`user.deleted`) deletes all their data and files.

---

## UC-02 Upload a PDF
**Actor:** Student · **Goal:** turn a PDF of notes into a deck.

**Preconditions:** signed in; daily upload limit (20) not reached.

**Main success scenario**
1. Student picks a PDF and confirms the title and what to generate.
2. App checks type and size (≤ 20 MB) and calls `POST /documents`.
3. System creates the document (`queued`) and returns a signed upload URL.
4. App uploads the file and calls `POST /documents/{id}/process`.
5. System checks the file exists, is a real PDF, and has ≤ 50 pages, then queues generation (202).
6. App opens the deck page with progress (continues in UC-04).

**Alternate flows**
- 1a. Student removes the file and picks another before submitting.
- 4a. Upload interrupted: app shows "Upload failed" and lets the student retry the upload with the same document.

**Exceptions**
- 2a. Not a PDF or too large: app blocks submission with a message.
- 5a. More than 50 pages: System returns 422 `page_limit_exceeded`; document marked failed.
- 5b. File missing in Storage (upload never completed): 409 `upload_missing`.
- 5c. File is not really a PDF (magic bytes): 422 `invalid_file`.
- 5d. Encrypted PDF: job fails with `encrypted_pdf`.
- Daily limit reached: 429 `upload_limit_reached`.

**Postconditions:** a document exists with a stored file and a queued job.

---

## UC-03 Paste notes
**Actor:** Student · **Goal:** make a deck from typed or copied notes.

**Preconditions:** signed in.

**Main success scenario**
1. Student switches to Paste notes, pastes text and enters a title.
2. App checks length (200–100,000 characters) and calls `POST /documents/text`.
3. System saves the document with `raw_text` and queues generation.
4. App opens the deck page (UC-04).

**Exceptions**
- 2a. Too short or too long: app shows the character count and blocks submission; System also returns 422 if bypassed.

**Postconditions:** a text document exists with a queued job.

---

## UC-04 Generate a deck (background)
**Actor:** System, LLM provider · **Goal:** produce verified flashcards, MCQs and problem templates.

**Preconditions:** document is `queued` with a file or text.

**Main success scenario**
1. System extracts text per page.
2. System strips headers, footers and page numbers, then splits the text into chunks with headings and page ranges.
3. System marks quantitative chunks and embeds every chunk locally.
4. For each chunk, System asks the LLM for flashcards and MCQs (and problem templates for quantitative chunks), validating each response.
5. Problem templates pass all verification checks, including an independent solve by a different provider.
6. System removes duplicates, creates scheduling states (due now), and marks the document `ready`.
7. App (polling) shows the deck.

**Alternate flows**
- 4a. Provider rate-limited (429): System backs off and uses the next provider.
- 4b. Invalid JSON from the LLM: System retries up to 2 times, then skips that chunk's output.
- 4c. Chunk is a table of contents or references: LLM returns `skip`; no cards from it.
- 5a. A template fails a check: it's dropped and the failure is recorded in `generation_runs`.
- 6a. Student chose "flashcards only": no MCQs or problems are generated.

**Exceptions**
- 1a. Almost no text (scanned PDF): `failed` with `scanned_pdf`.
- 4d. All providers fail for a chunk after retries: that chunk is marked `failed`; if no chunk succeeds, the document fails with `ai_unavailable`.
- 6b. No cards at all: `failed` with `no_study_content`.
- Retry (`POST /documents/{id}/retry`): only `failed`/`pending` chunks are processed again.

**Postconditions:** document `ready` with at least one card, or `failed` with an error code.

**Business rules:** every card links to its source chunk; the LLM never computes graded answers; notes are treated as data, never as instructions.

---

## UC-05 Review flashcards
**Actor:** Student · **Goal:** review due cards and get them rescheduled.

**Preconditions:** at least one unflagged flashcard is due.

**Main success scenario**
1. Student starts review from the dashboard or a deck.
2. System returns due cards, oldest due first.
3. Student sees the front, flips the card, and sees the answer and source.
4. Student rates the card; System updates SM-2 state and logs the review in one transaction.
5. Steps 3–4 repeat; cards rated Again return at the end of the session.
6. App shows the session summary.

**Alternate flows**
- 1a. Nothing due: app shows "All caught up" with the next due time.
- 3a. Student opens the source chunk, then returns to the card.
- 3b. Student flags the card: it's removed from the session and hidden from future sessions.
- 5a. Student leaves mid-session: ratings already sent are kept.

**Exceptions**
- 4a. Network error on rating: app retries in the background; if it still fails, it shows a toast with Retry.
- 4b. Card deleted meanwhile: System returns 404; app skips the card.

**Postconditions:** each rated card has a new `due_at`; `reviews` has one row per rating.

**Business rules:** SM-2 variant in `03-backend.md` §6 (e.g. new card rated Good → due in 1 day).

---

## UC-06 Take a quiz
**Actor:** Student · **Goal:** test knowledge and get a score.

**Preconditions:** deck is `ready` and has at least one unflagged MCQ.

**Main success scenario**
1. Student starts a quiz and picks a length.
2. System samples questions (weighted toward past mistakes), shuffles options, and returns them **without answers**.
3. Student picks an option and checks it; System grades it and returns the correct option, explanation and source.
4. Step 3 repeats for each question.
5. Student finishes; System calculates the score, updates SM-2 for each question, and returns missed questions.
6. App shows results.

**Alternate flows**
- 1a. Fewer MCQs than the chosen length: the quiz uses all of them.
- 3a. Wrong answer: student asks for an explanation (UC-07).
- 6a. Student taps Review missed as flashcards: missed cards become due now.
- 6b. Student retakes the quiz: a new attempt with a new sample.

**Exceptions**
- 3b. Same question answered twice: System returns 409; the first answer stands.
- 3c. Answer for a card not in this attempt: 400.
- 5a. Finish called twice: second call returns the same result.
- Attempt belongs to another user: 404.

**Postconditions:** attempt finished with score ≤ total; each question answered once.

---

## UC-07 Explain my mistake
**Actor:** Student, System, LLM provider · **Goal:** understand why an answer was wrong, using their own notes.

**Preconditions:** a wrong quiz answer or wrong problem answer exists in the student's attempt.

**Main success scenario**
1. Student taps Explain my mistake.
2. System retrieves the card's source chunk plus the most relevant chunks from the same document.
3. System asks the LLM for a short explanation using only that context.
4. System caches the explanation and returns it with page references.

**Alternate flows**
- 1a. Explanation already cached: returned immediately, no LLM call.

**Exceptions**
- 1b. Answer was correct: 400 `not_a_mistake`.
- 3a. All providers unavailable: 503 `ai_unavailable`; app shows "Try again".
- Rate limit reached (10/min, 100/day): 429.

**Postconditions:** `attempt_answers.explanation` stored.

---

## UC-08 Generate cards on a topic
**Actor:** Student, System, LLM provider · **Goal:** get more cards about one topic from the notes.

**Preconditions:** deck is `ready`.

**Main success scenario**
1. Student enters a topic and submits.
2. System embeds the topic and retrieves the most relevant chunks.
3. System generates cards from those chunks only (`origin = topic`, up to 8).
4. New cards are saved, scheduled due now, and returned.

**Exceptions**
- 1a. Empty or overly long topic (> 100 chars): 422.
- 2a. No chunk close enough: 404 `topic_not_found`; app says the topic isn't in the notes.
- 3a. Provider unavailable: 503.
- Rate limit reached: 429.

**Postconditions:** new cards linked to their source chunks.

---

## UC-09 Practise a problem set
**Actor:** Student · **Goal:** solve computational problems with feedback.

**Preconditions:** deck has at least one verified, unflagged problem template.

**Main success scenario**
1. Student starts a problem session and picks a length.
2. System picks a template, draws values, stores the instance, and returns the question with numbers filled in (answer withheld).
3. Student enters a value and unit and checks it.
4. System converts units, grades within tolerance, and returns correct/close/wrong with feedback and the correct value.
5. Steps 2–4 repeat; student finishes and sees results.

**Alternate flows**
- 3a. Student asks for hints: revealed one at a time; hints used are recorded.
- 3b. Student views the solution: steps are shown with this instance's numbers; graded as Hard at best for SM-2.
- 4a. Answer matches a known mistake: feedback explains that mistake.
- 4b. No unit given: graded in the expected unit with a "Remember units" note.
- 5a. Try a similar one: new instance from the same template.

**Exceptions**
- 3c. Non-numeric input: app blocks it; System returns 422 if bypassed.
- 4c. Unit of the wrong dimension: graded wrong with unit feedback.
- 4d. Instance already answered: 409.
- Hint number beyond the available hints: 404.

**Postconditions:** each instance answered at most once; SM-2 updated per template at finish.

---

## UC-10 View the dashboard
**Actor:** Student · **Goal:** see what to study now.

**Preconditions:** signed in.

**Main success scenario**
1. App calls `GET /dashboard`.
2. System returns due counts, estimated minutes, 7-day accuracy, streak, decks and weakest topics, using the student's timezone.
3. Student starts a review, a quiz, or a weak-topic review.

**Alternate flows**
- 2a. New user with no decks: empty state with Upload your notes.
- 2b. A deck is generating: it shows progress; a failed deck shows Retry.
- 2c. Fewer than 3 answers on any topic: the weakest-topics panel is hidden.

**Postconditions:** none (read only).

---

## UC-11 Manage cards and decks
**Actor:** Student · **Goal:** fix or remove content.

**Preconditions:** the deck belongs to the student.

**Main success scenario (flag)**
1. Student flags a card with a reason.
2. System marks it flagged; it no longer appears in reviews, quizzes or problem sessions.

**Main success scenario (edit)**
1. Student edits a card.
2. System validates the new content for its type, saves it, marks it `edited`, and clears the flag.

**Main success scenario (delete deck)**
1. Student chooses Delete deck and confirms.
2. System deletes the file from Storage and the document (chunks, cards, states and attempts cascade).

**Exceptions**
- Edit with invalid content (e.g. MCQ with duplicate options): 422 with field errors.
- Card or deck of another user: 404.
- Delete while generating: the job notices the document is gone and stops.

**Postconditions:** flagged cards hidden; edited cards valid; deleted decks fully removed.
