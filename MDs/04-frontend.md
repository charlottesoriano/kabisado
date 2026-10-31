# 04 — Frontend Functionalities

Two clients share one backend: a **Next.js web app** and a **React Native (Expo) mobile app**. Both are thin. They show what the API returns and never compute scores, due dates or correct answers themselves.

## 1. Shared foundations

| Area | Approach |
| --- | --- |
| API client | `packages/api-client`: types generated from FastAPI's OpenAPI schema (`openapi-typescript`), a typed `openapi-fetch` client, and TanStack Query hooks (`useDue`, `useSubmitReview`, `useStartQuiz`, …). Both apps import the same hooks. |
| Auth | Clerk (`@clerk/nextjs` on web, `@clerk/clerk-expo` on mobile). The API client calls `getToken()` before each request and sends it as a Bearer token; on 401 it retries once with a fresh token, then signs out. |
| Design tokens | `packages/ui-tokens`: colors, spacing, radii, type scale. Web uses them in Tailwind; mobile uses them in NativeWind. |
| Theme | Paper white `#F6F5F1` background, ink `#1A1D1B`, primary green `#1E6B57`, highlighter yellow `#F4D35E`. Space Grotesk for headings, Inter for body. |
| Math | KaTeX (web) and KaTeX in a WebView (mobile) for questions, options, solutions. |
| Errors | One error component that maps API `error.code` to friendly text (e.g. `scanned_pdf` → "This looks like a scanned PDF. Try a text-based PDF or paste your notes."). |
| Loading | Skeletons for lists and cards, never a blank screen. |
| Empty states | Every list has one with a single next action. |
| Accessibility | Real buttons and links, labels on every input, `aria-label` on icon-only buttons, focus rings, 4.5:1 contrast, touch targets ≥ 44 px, state never shown by color alone. |

## 2. Screens

| Screen | Web route | Mobile route | Flow |
| --- | --- | --- | --- |
| Sign in / sign up | `/sign-in`, `/sign-up` | `(auth)/sign-in`, `(auth)/sign-up` | F1 |
| Dashboard | `/` | `(tabs)/index` | F10 |
| Upload | `/upload` | `(tabs)/upload` | F2, F3 |
| Deck list | `/decks` | `(tabs)/decks` | F11 |
| Deck detail | `/decks/[id]` | `decks/[id]` | F4, F8, F11 |
| Flashcard review | `/review` | `review` (full screen) | F5 |
| Quiz | `/decks/[id]/quiz` | `decks/[id]/quiz` | F6, F7 |
| Quiz results | `/quiz/[attemptId]/results` | `quiz/[attemptId]/results` | F6 |
| Problem practice | `/decks/[id]/problems` | `decks/[id]/problems` | F9 |
| Problem results | `/problems/[sessionId]/results` | `problems/[sessionId]/results` | F9 |
| Settings | `/settings` | `(tabs)/settings` | profile, timezone, reminder time, sign out |

Mobile tabs: **Home, Decks, Upload, Progress**. Review, quiz and problem screens open full screen with no tab bar.

## 3. Screen-by-screen functionality

### 3.1 Sign in / sign up
- Clerk's prebuilt `<SignIn />` / `<SignUp />` on web (styled with the app's tokens via Clerk `appearance`); on mobile, custom screens using Clerk's `useSignIn` / `useSignUp` / `useOAuth` hooks for Google.
- Web: Clerk middleware protects every route except sign-in/sign-up.
- After sign-in: `GET /me`, then go to the dashboard.
- Errors (from Clerk): wrong password, unverified email ("Enter the code we sent"), network offline.
- Settings uses Clerk's `<UserButton />` / `<UserProfile />` on web for account management.

### 3.2 Dashboard
- Greeting, **N cards due today**, estimated minutes, **Start review**, **Take a quiz**.
- Stat tiles: due today (new / review), 7-day quiz accuracy with change vs last week, streak.
- Deck list: title, source and size, mastery bar, due badge, status badge (Generating with progress, Failed with Retry).
- Weakest topics: top 3 with accuracy bar and a **Review** link (opens review filtered by topic).
- Empty state for new users: one card with **Upload your notes**.
- Data: `GET /dashboard`, refetched when the screen regains focus.

### 3.3 Upload
- Tabs: **Upload PDF** / **Paste notes**.
- PDF: drag-and-drop zone (web) or document picker (mobile); selected file row with name, size and remove button.
- Client checks: PDF type, ≤ 20 MB. Page count is checked by the server.
- Paste: textarea with live character count (200–100,000).
- Deck title (defaults to file name without extension) and a **Generate** selector (flashcards + quiz, flashcards only, quiz only).
- Upload progress bar for the file transfer, then redirect to the deck page.
- Prevents double submission (button disabled while uploading).

### 3.4 Deck detail
- Header: title (rename inline), source info, counts, **Review N due**, **Start quiz**, **Practice problems** (only if the deck has problems).
- While generating: progress view with stage name ("Reading your PDF", "Splitting into sections", "Writing questions") and `done / total` chunks; polls every 3 s; stops polling at `ready` or `failed`.
- Failed: reason + **Retry**.
- **Generate on a topic**: input + button; loading state; "couldn't find that topic" message; new cards appear at the top with a "New" badge.
- Tabs: Flashcards / Quiz questions / Problem set, with counts.
- Card grid: topic label, front/back or question with correct option, **Source · page N** (opens the source text in a side panel on web or a bottom sheet on mobile), flag button, edit button.
- Edit card: modal (web) or sheet (mobile) with validation matching the backend (MCQ needs 4 distinct options and one correct).
- **Delete deck** in an overflow menu, with a confirmation dialog.

### 3.5 Flashcard review
- Progress bar and "Card X of N".
- Front → flip (tap/click or Space) → back with highlighted answer and source link.
- Rating buttons Again / Hard / Good / Easy, each showing its next interval from `GET /reviews/preview/{card_id}`.
- Web keyboard: Space flips, 1–4 rate. Mobile: swipe left = Again, right = Good (buttons remain).
- **Optimistic** advance to the next card; the rating is sent in the background and retried on failure. If it finally fails, a toast offers retry.
- Again-rated cards are re-queued at the end of the session (client-side queue, server is still the source of truth for scheduling).
- Flag button; flagging removes the card from the session.
- End screen: cards reviewed, breakdown by rating, next due time, **Back to dashboard**.
- Leaving mid-session asks for confirmation; ratings already sent are kept.

### 3.6 Quiz
- Length picker (5 / 10 / 20).
- Segmented progress bar showing correct and wrong per question.
- Options as large buttons with letters A–D; one selection, then **Check answer**.
- After checking: correct option in green with "Correct", chosen wrong option in red with "Your answer" (text labels as well as color); explanation; source link; **Explain my mistake** on wrong answers; **Report question**; **Next question**.
- Mobile shows feedback in a bottom sheet.
- Explain my mistake: loading state, then the explanation with page references; errors show "Couldn't explain right now — try again".
- Options are locked after answering; the client never knows the answer before the server returns it.

### 3.7 Quiz results
- Score ring (e.g. 7/10, 70%), change vs last attempt, time taken.
- **Review missed as flashcards**, **Retake quiz**, **Back to dashboard**.
- Missed questions: question, your answer, correct answer, source link, explain link.

### 3.8 Problem practice
- Question rendered with KaTeX, numbers already filled in.
- Answer input (numeric keyboard on mobile) and unit field prefilled with the expected unit, editable.
- **Hint** (reveals hints one by one, shows "Hint 1 of 2"), **Show solution** (reveals steps one by one), **Check**.
- Result banner: Correct / Very close (rounding) / Not quite, plus feedback text (e.g. a known mistake), plus the correct value and unit.
- **Try a similar one** (same template, new numbers), **Next problem**, **Report problem**.
- Input validation: rejects non-numeric input with an inline message; accepts `2.4e1` and commas as thousands separators.

### 3.9 Problem results
- Score, problems missed with their worked solutions, topics to review.

### 3.10 Settings
- Display name, timezone, daily reminder time (mobile), sign out, delete account (confirmation).

## 4. Mobile-specific functionality
- Daily local notification at the chosen time: "You have N cards due" (count fetched when the app was last opened; no push server needed).
- Haptics on rating and on correct/wrong.
- Safe-area handling and keyboard avoidance on answer inputs.
- Offline: screens show cached data from TanStack Query; actions that need the network show "You're offline" and are disabled. Offline review is out of scope for the MVP.
- Deep links: `reviewer://decks/{id}` opens a deck (used by notifications).

## 5. Web-specific functionality
- Responsive from 360 px to 1440 px; header nav wraps; card grids reflow; side panel becomes a full-screen sheet on narrow screens.
- Keyboard shortcuts in review and quiz (1–4, Space, Enter for Check / Next).
- Server components for the dashboard shell; client components for interactive sessions.

## 6. State and data rules
- Server state lives in TanStack Query only; no duplicated global store.
- Mutations invalidate the queries they affect (e.g. a review invalidates `dashboard` and `due`).
- Session screens (review, quiz, problems) keep local UI state (current index, flipped, selected option) in component state.
- No business logic on the client: intervals, scores and correctness all come from the API.
