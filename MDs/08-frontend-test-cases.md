# 08 — Frontend Test Cases

Test cases for the Next.js web app and the Expo mobile app. IDs reference use cases in `06-use-cases.md` and screens in `04-frontend.md`.

## 1. Setup and conventions

| Item | Web | Mobile |
| --- | --- | --- |
| Unit / component | Vitest + React Testing Library | Jest (`jest-expo`) + React Native Testing Library |
| API mocking | MSW handlers built from the OpenAPI types | MSW (`msw/native`) with the same handlers |
| End-to-end | Playwright against a seeded backend; Clerk test users via `@clerk/testing` | Maestro flows on an iOS simulator and an Android emulator |
| Accessibility | `@axe-core/playwright` on every page; keyboard-only runs | RNTL accessibility queries (`getByRole`, `accessibilityLabel`); TalkBack/VoiceOver manual pass before release |
| Visual | Playwright screenshots at 375, 768, 1280 px (optional) | Maestro screenshots on two device sizes |
| Time | Fake timers for polling and toasts | Fake timers |

**Platform:** Web, Mobile, or Both (the same test runs on both, with platform-specific steps where noted). **Priority:** P0 = must pass to release; P1 = should pass; P2 = nice to have.

**Rule tested throughout:** the client never computes correctness, scores or intervals. It only shows what the API returns.

---

## 2. Shared API client and auth (UC-01)

| ID | Platform | Type | Scenario | Steps | Expected | Pri |
| --- | --- | --- | --- | --- | --- | --- |
| FE-API-01 | Both | unit | Token attached | Call any hook while signed in | Request has `Authorization: Bearer <token from getToken()>` | P0 |
| FE-API-02 | Both | unit | 401 retry | MSW returns 401 once, then 200 | One retry with a fresh token; data shown | P0 |
| FE-API-03 | Both | unit | 401 twice | MSW returns 401 twice | User signed out and sent to sign-in | P0 |
| FE-API-04 | Both | unit | Error mapping | MSW returns `{"error":{"code":"scanned_pdf"}}` | Friendly message "This looks like a scanned PDF…" | P0 |
| FE-API-05 | Both | unit | Unknown error code | `code = "something_new"` | Generic "Something went wrong" + Retry | P1 |
| FE-AUTH-01 | Web | e2e | Protected routes | Visit `/` signed out | Redirect to `/sign-in` | P0 |
| FE-AUTH-02 | Both | e2e | Sign in | Sign in with a Clerk test user | Dashboard shown; `GET /me` called | P0 |
| FE-AUTH-03 | Mobile | e2e | Session persists | Sign in, kill and reopen the app | Still signed in (SecureStore token cache) | P0 |
| FE-AUTH-04 | Both | e2e | Sign out | Settings → Sign out | Back to sign-in; cached data cleared (no previous user's decks on next sign-in) | P0 |
| FE-AUTH-05 | Mobile | component | Sign-in errors | Wrong password from Clerk | Inline error under the field; button re-enabled | P1 |

## 3. Dashboard (UC-10)

| ID | Platform | Type | Scenario | Steps | Expected | Pri |
| --- | --- | --- | --- | --- | --- | --- |
| FE-DSH-01 | Both | component | Populated | Mock dashboard: 24 due, 78%, streak 5, 3 decks, 3 weak topics | All values shown as returned; "24 cards due today" | P0 |
| FE-DSH-02 | Both | component | New user | Empty dashboard response | Empty state with one "Upload your notes" action; no zeros-filled tiles | P0 |
| FE-DSH-03 | Both | component | Loading | Delay the response | Skeletons, then content; no layout jump in the header | P1 |
| FE-DSH-04 | Both | component | Generating deck | Deck with `status = generating`, 9 of 14 | "Generating" badge and progress bar at 64% | P1 |
| FE-DSH-05 | Both | component | Failed deck | Deck with `failed` | Error badge and Retry; Retry calls `POST /retry` | P1 |
| FE-DSH-06 | Both | component | Nothing due | 0 due | "All caught up" instead of Start review | P1 |
| FE-DSH-07 | Both | component | Weak topics hidden | Empty `weakest_topics` | Panel not shown | P2 |
| FE-DSH-08 | Both | integration | Refetch on return | Finish a review, go back | Dashboard refetched; due count decreased | P0 |
| FE-DSH-09 | Both | e2e | Weak topic review | Tap Review on a weak topic | Review opens filtered to that topic (`topic` query param) | P1 |

## 4. Upload (UC-02, UC-03)

| ID | Platform | Type | Scenario | Steps | Expected | Pri |
| --- | --- | --- | --- | --- | --- | --- |
| FE-UP-01 | Web | component | Drag and drop | Drop a PDF on the zone | File row with name and size; title prefilled from file name | P0 |
| FE-UP-02 | Mobile | component | Document picker | Pick a PDF via mocked `expo-document-picker` | File row shown; title prefilled | P0 |
| FE-UP-03 | Both | component | Wrong type | Choose a `.docx` | Error "Please choose a PDF"; Generate disabled | P0 |
| FE-UP-04 | Both | component | Too large | 21 MB PDF | Error "PDFs up to 20 MB"; Generate disabled | P0 |
| FE-UP-05 | Both | component | Remove file | Tap remove | Back to the empty drop zone | P2 |
| FE-UP-06 | Both | integration | Upload sequence | Submit a valid PDF | Calls in order: `POST /documents` → PUT to signed URL → `POST /process`; then navigates to the deck page | P0 |
| FE-UP-07 | Both | component | Double submit | Tap Generate twice quickly | Only one `POST /documents` | P0 |
| FE-UP-08 | Both | integration | Upload fails | Signed URL PUT returns 500 | "Upload failed" with Retry; Retry re-uploads to the same document | P1 |
| FE-UP-09 | Both | integration | Page limit | `/process` returns 422 `page_limit_exceeded` | Message "PDFs up to 50 pages"; stays on upload screen | P0 |
| FE-UP-10 | Both | component | Paste notes count | Type 150 characters | Counter "150 / 200 minimum"; Generate disabled until 200 | P0 |
| FE-UP-11 | Both | integration | Paste notes submit | 1,500 characters | `POST /documents/text`; navigate to deck page | P0 |
| FE-UP-12 | Both | integration | Daily limit | 429 `upload_limit_reached` | "You've reached today's upload limit" | P2 |

## 5. Deck page and generation (UC-04, UC-08, UC-11)

| ID | Platform | Type | Scenario | Steps | Expected | Pri |
| --- | --- | --- | --- | --- | --- | --- |
| FE-DCK-01 | Both | component | Polling | Status `generating` → `generating` → `ready` | Polls every 3 s; stops after `ready`; deck view appears | P0 |
| FE-DCK-02 | Both | component | Stage labels | `extracting`, `chunking`, `generating` | "Reading your PDF", "Splitting into sections", "Writing questions" | P2 |
| FE-DCK-03 | Both | component | Failed scanned | `failed`, `scanned_pdf` | Reason shown + "Paste notes instead" link + Retry | P0 |
| FE-DCK-04 | Both | component | Polling stops on leave | Navigate away while generating | No further requests | P1 |
| FE-DCK-05 | Both | component | Tabs and counts | 40 flashcards, 24 MCQs, 0 problems | Two tabs with counts; Problem set tab hidden; Practice problems button hidden | P0 |
| FE-DCK-06 | Both | component | Problems available | 5 problem templates | Problem set tab and Practice problems button shown | P0 |
| FE-DCK-07 | Both | component | Show source | Tap "Source · p. 3" | Side panel (web) / bottom sheet (mobile) with the chunk text | P1 |
| FE-DCK-08 | Both | integration | Topic generation | Enter "Krebs cycle", submit | Loading state; new cards at top with "New" badge | P0 |
| FE-DCK-09 | Both | integration | Topic not found | 404 `topic_not_found` | "We couldn't find that topic in your notes" | P0 |
| FE-DCK-10 | Both | component | Empty topic | Submit empty input | Button disabled; no request | P1 |
| FE-DCK-11 | Both | integration | Flag card | Flag → reason → confirm | `POST /flag`; card shows "Flagged" and drops out of counts | P1 |
| FE-DCK-12 | Both | component | Edit MCQ validation | Make two options identical | Inline error; Save disabled | P0 |
| FE-DCK-13 | Both | integration | Edit saved | Change a flashcard back | `PATCH /cards/{id}`; card updated; flag cleared | P1 |
| FE-DCK-14 | Both | integration | Delete deck | Delete → confirm | `DELETE` called; back to deck list; deck gone; dashboard refetched | P0 |
| FE-DCK-15 | Both | component | Delete cancel | Delete → Cancel | No request | P1 |
| FE-DCK-16 | Both | component | Rename | Edit title inline, Enter | `PATCH /documents/{id}`; title updated | P2 |

## 6. Flashcard review (UC-05)

| ID | Platform | Type | Scenario | Steps | Expected | Pri |
| --- | --- | --- | --- | --- | --- | --- |
| FE-REV-01 | Both | component | Front first | Start review with 12 cards | Front shown; "Card 1 of 12"; rating buttons hidden until flip | P0 |
| FE-REV-02 | Both | component | Flip | Tap card (mobile) / click or Space (web) | Back shown with answer and source link; rating buttons appear | P0 |
| FE-REV-03 | Both | component | Interval labels | Preview `{again:1, hard:3, good:6, easy:9}` | Buttons show "1 day", "3 days", "6 days", "9 days" exactly as returned | P0 |
| FE-REV-04 | Web | component | Keyboard rating | Flip, press 3 | Rated Good; next card | P0 |
| FE-REV-05 | Web | component | Keys before flip | Press 3 on the front | Nothing happens | P1 |
| FE-REV-06 | Mobile | component | Swipe | Swipe right on the back | Rated Good; swipe left = Again | P1 |
| FE-REV-07 | Both | integration | Optimistic advance | Rate with a 2-s API delay | Next card shown immediately; request sent with `{card_id, rating}` | P0 |
| FE-REV-08 | Both | integration | Rating fails | API returns 500 twice | Background retry, then toast "Couldn't save your rating" with Retry | P0 |
| FE-REV-09 | Both | component | Again re-queue | Rate card 1 Again in a 3-card session | Card 1 appears again after card 3 | P0 |
| FE-REV-10 | Both | component | Flag during review | Flag current card | Removed from session; count adjusts ("Card 2 of 11") | P1 |
| FE-REV-11 | Both | component | Summary | Finish session | Cards reviewed and counts per rating; next due time | P1 |
| FE-REV-12 | Both | component | Nothing due | Empty due list | "All caught up" with next due time; no empty card | P1 |
| FE-REV-13 | Both | component | Leave mid-session | Tap close | Confirm dialog; confirming exits; already-sent ratings unaffected | P1 |
| FE-REV-14 | Both | component | 404 card | Rating returns 404 | Card skipped silently; session continues | P2 |

## 7. Quiz and explain my mistake (UC-06, UC-07)

| ID | Platform | Type | Scenario | Steps | Expected | Pri |
| --- | --- | --- | --- | --- | --- | --- |
| FE-QZ-01 | Both | component | Length picker | Choose 10 | `POST /quizzes {length: 10}` | P0 |
| FE-QZ-02 | Both | component | Check disabled | No option selected | Check answer disabled | P0 |
| FE-QZ-03 | Both | component | Select and check | Select B, Check | `POST /answers {card_id, chosen_index: 1}`; options locked | P0 |
| FE-QZ-04 | Both | component | Correct feedback | Response `correct: true` | Chosen option marked "Correct" (text + color); explanation | P0 |
| FE-QZ-05 | Both | component | Wrong feedback | Chosen B, response `correct_index: 2` | B labelled "Your answer", C labelled "Correct"; Explain my mistake shown | P0 |
| FE-QZ-06 | Both | unit | No client-side grading | Inspect quiz state before checking | No correct-answer data exists in client state or props | P0 |
| FE-QZ-07 | Both | component | Progress segments | After answers correct, wrong, correct | Segments 1–3 colored and labelled for screen readers ("Question 2, wrong") | P1 |
| FE-QZ-08 | Both | component | Double tap Check | Tap Check twice fast | One request | P0 |
| FE-QZ-09 | Web | component | Keyboard | Keys 1–4 select, Enter checks, Enter again goes next | Works without a mouse | P1 |
| FE-QZ-10 | Mobile | component | Bottom sheet | Answer a question | Feedback in a bottom sheet with Next question | P1 |
| FE-QZ-11 | Both | integration | Explain | Tap Explain my mistake | Loading state, then explanation with page reference | P0 |
| FE-QZ-12 | Both | integration | Explain fails | 503 | "Couldn't explain right now" + Try again | P1 |
| FE-QZ-13 | Both | integration | Finish | Answer last question → Next | `POST /finish`; results screen | P0 |
| FE-QZ-14 | Both | component | Results | Score 7/10, last attempt 6/10, 3 missed | "7/10", "70%", "Up from 60%", 3 missed items with both answers | P0 |
| FE-QZ-15 | Both | integration | Review missed | Tap Review missed as flashcards | Review session with those cards | P1 |
| FE-QZ-16 | Both | component | 409 on answer | Server returns 409 | Shows the existing result; no error toast | P2 |

## 8. Problem practice (UC-09)

| ID | Platform | Type | Scenario | Steps | Expected | Pri |
| --- | --- | --- | --- | --- | --- | --- |
| FE-PS-01 | Both | component | Math renders | Question with LaTeX `\frac{1}{2}at^2` | Rendered by KaTeX (web) / WebView KaTeX (mobile); no raw LaTeX visible | P0 |
| FE-PS-02 | Both | component | Unit prefilled | `expected_unit = "m"` | Unit field shows "m" and is editable | P1 |
| FE-PS-03 | Mobile | component | Numeric keyboard | Focus answer input | `keyboardType` decimal-pad; input stays visible above keyboard | P1 |
| FE-PS-04 | Both | component | Input validation | Type "abc" | Inline "Enter a number"; Check disabled | P0 |
| FE-PS-05 | Both | component | Accepted formats | "2.4e1", "1,200", "-3.5" | Accepted; sent as typed with the unit | P1 |
| FE-PS-06 | Both | integration | Correct | Response `correct` | "Correct" banner; Next problem and Try a similar one | P0 |
| FE-PS-07 | Both | integration | Close | Response `close` | "Very close — check your rounding" + correct value | P0 |
| FE-PS-08 | Both | integration | Wrong with known mistake | Response `wrong` + feedback | Feedback text shown + correct value and unit | P0 |
| FE-PS-09 | Both | integration | Units note | Response includes the units note | Note shown under the banner | P2 |
| FE-PS-10 | Both | integration | Hints one at a time | Tap Hint twice (2 hints) | "Hint 1 of 2", then "Hint 2 of 2"; Hint button disabled after the last | P1 |
| FE-PS-11 | Both | integration | Solution step by step | Show solution, then Next step | Steps revealed one at a time with numbers filled in | P0 |
| FE-PS-12 | Both | integration | Similar problem | Tap Try a similar one | New question with different numbers; input cleared | P1 |
| FE-PS-13 | Both | component | Tab visibility | Deck without problems | No Problem set tab or Practice problems button | P0 |

## 9. Mobile-specific

| ID | Type | Scenario | Steps | Expected | Pri |
| --- | --- | --- | --- | --- | --- |
| FE-MOB-01 | component | Reminder permission | First launch after sign-in | Permission prompt once; choice saved | P1 |
| FE-MOB-02 | unit | Reminder schedule | Set 19:00 with 12 due | Local notification scheduled daily at 19:00 "You have 12 cards due" | P1 |
| FE-MOB-03 | e2e | Notification deep link | Tap notification | Opens review | P2 |
| FE-MOB-04 | e2e | Deck deep link | Open `reviewer://decks/{id}` | Deck page opens (sign-in first if needed) | P2 |
| FE-MOB-05 | component | Offline | Turn network off on dashboard | Cached data shown; "You're offline" banner; Start review and uploads disabled | P1 |
| FE-MOB-06 | component | Back online | Network restored | Banner hides; queries refetch | P1 |
| FE-MOB-07 | e2e | Safe areas | Run on a notched device and an Android device with gesture nav | No content under the notch or home indicator; bottom buttons fully tappable | P1 |
| FE-MOB-08 | component | Haptics | Rate a card; answer right and wrong | Haptic called with the expected type | P2 |

## 10. Web-specific

| ID | Type | Scenario | Steps | Expected | Pri |
| --- | --- | --- | --- | --- | --- |
| FE-WEB-01 | e2e | Responsive dashboard | 375, 768, 1280 px | No horizontal scroll; nav wraps; deck list and weak topics stack on narrow screens | P0 |
| FE-WEB-02 | e2e | Responsive deck grid | 375 vs 1280 px | 1 column vs 3 columns; source panel becomes full-screen sheet on narrow | P1 |
| FE-WEB-03 | e2e | Keyboard-only review | Tab, Space, 1–4 only | Full session completes without a mouse; focus always visible | P0 |
| FE-WEB-04 | e2e | Browser back during quiz | Press back mid-quiz | Confirm dialog; quiz attempt not duplicated on return | P2 |

## 11. Accessibility (both)

| ID | Type | Scenario | Expected | Pri |
| --- | --- | --- | --- | --- |
| FE-A11Y-01 | e2e (web) | axe scan on every page | No serious or critical violations | P0 |
| FE-A11Y-02 | component | Icon buttons | Flag, close, remove, account buttons have accessible names | P0 |
| FE-A11Y-03 | component | Form labels | Every input (title, topic, answer, unit, paste area) has a label | P0 |
| FE-A11Y-04 | component | Not color alone | Quiz and problem feedback include text ("Correct", "Your answer") | P0 |
| FE-A11Y-05 | component | Touch targets | All tappable elements ≥ 44 × 44 px (mobile) | P1 |
| FE-A11Y-06 | component | Live updates | Generation progress and answer results announced (`aria-live` / `accessibilityLiveRegion`) | P1 |
| FE-A11Y-07 | manual | Screen readers | VoiceOver (iOS) and TalkBack (Android) complete a review and a quiz | P1 |
| FE-A11Y-08 | component | Reduced motion | OS reduced-motion on | Card flip and sheet animations simplified | P2 |

## 12. End-to-end journeys (release gate)

Run on web (Playwright) and mobile (Maestro) against a seeded backend with mocked LLM responses.

| ID | Journey | Expected | Pri |
| --- | --- | --- | --- |
| FE-E2E-01 | Sign up → upload a 3-page PDF → wait for ready → review 3 cards → dashboard | Due count drops by 3; streak 1 | P0 |
| FE-E2E-02 | Paste notes → ready → 5-question quiz with 1 wrong → explain → results → review missed | Score 4/5; missed card appears in review | P0 |
| FE-E2E-03 | Physics deck → problem set → wrong answer → hint → solution → similar → correct | Results show 1 of 2 correct | P0 |
| FE-E2E-04 | Upload scanned PDF | Failure message with "Paste notes instead" | P1 |
| FE-E2E-05 | Flag a card in review → it no longer appears in the next session | Flagged card absent | P1 |
| FE-E2E-06 | Delete a deck → dashboard and deck list | Deck gone everywhere; due count updated | P1 |
| FE-E2E-07 | Two accounts on the same device: sign out of A, sign in as B | B never sees A's decks, even briefly | P0 |
