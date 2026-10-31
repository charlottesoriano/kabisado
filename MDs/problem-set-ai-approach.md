# Problem Sets — AI Approach

Feature spec for generating practice problem sets from uploaded math, chemistry and physics lessons in the Reviewer Generator app.

## 1. Summary

Students upload notes or a PDF for a quantitative subject. Alongside flashcards and quizzes, the app generates a **problem set**: computational problems the student solves and types a numeric answer for, with hints, a worked solution and a score.

The core rule: **the AI writes the problem, code computes the answer.** Language models are good at reading a lesson and phrasing a problem. They are unreliable at arithmetic. So the model produces a *template* with a formula, and the app does all the math with a math library. A wrong answer key is the worst bug a study app can have, so the design is built around preventing it.

## 2. What counts as a problem

| Subject | Good fits for the MVP | Later |
| --- | --- | --- |
| Physics | Kinematics, forces, energy, work, power, Ohm's law, waves | Multi-step problems with diagrams, vectors drawn on a figure |
| Chemistry | Moles and molar mass, stoichiometry, concentration (molarity), gas laws, percent composition | Balancing equations (needs its own checker), equilibrium, reaction mechanisms |
| Math | Plugging values into formulas, percentages, linear equations, area/volume, basic statistics | Proofs, symbolic answers (e.g. "simplify this expression"), graphing |
| Programming | Predict the output, fill in the blank, find the bug, put the lines in order (all graded without running the student's code) | Write a function that passes test cases (runs the student's code in a sandbox) |

MVP answers are **a number, optionally with a unit**, or for programming an output string or a choice. Symbolic answers and student-written code come later. Programming is covered in section 10.

## 3. Approach: templated problems

Instead of generating a fixed problem like "A car accelerates at 3 m/s² for 4 s…", the model generates a **template** with variables:

```json
{
  "topic": "Uniformly accelerated motion",
  "question": "A car starts from rest and accelerates at {a} m/s² for {t} s. How far does it travel?",
  "variables": {
    "a": { "min": 1, "max": 5, "step": 0.5, "unit": "m/s^2" },
    "t": { "min": 2, "max": 10, "step": 1, "unit": "s" }
  },
  "answer_formula": "a * t**2 / 2",
  "answer_unit": "m",
  "tolerance": 0.01,
  "hints": [
    "The car starts from rest, so the initial velocity is 0.",
    "Use the kinematics equation that relates distance, acceleration and time."
  ],
  "solution_steps": [
    "Use d = v₀t + ½at² with v₀ = 0, so d = ½at².",
    "d = ½ × {a} × {t}² = {{a * t**2 / 2}} m"
  ],
  "common_mistakes": [
    { "formula": "a * t**2", "feedback": "You may have dropped the ½ in d = ½at²." },
    { "formula": "a * t", "feedback": "a × t gives the final velocity, not the distance." }
  ],
  "chunk_id": "…"
}
```

At practice time the backend:

1. Picks random values for `a` and `t` within their ranges.
2. Fills in `{a}` and `{t}` in the question and steps.
3. Computes the answer and every `{{ … }}` value in the steps with SymPy (and Pint for units), and stores them in a `problem_instances` row. Only the question is sent to the client.
4. Compares the student's input to the computed answer.

**Why templates:**

- **Correct answer keys:** the formula is evaluated by code, never by the model.
- **Unlimited practice:** every attempt gets new numbers, so students can't memorise answers.
- **Fits spaced repetition:** a template is reviewed like a flashcard, with fresh numbers each review.
- **Cheap:** one generation call per template, not per problem.
- **Better feedback:** `common_mistakes` lets the app recognise a wrong answer that matches a known mistake and say what went wrong. The same formulas can be computed into convincing multiple-choice distractors.

## 4. Generation pipeline

This runs inside the existing background generation job, after chunking.

1. **Detect quantitative chunks.** Run a cheap classifier pass, or simple heuristics such as many digits, `=` signs, units or words like "solve", "calculate" or "example". Only these chunks go on to problem generation. The deck shows a "Problem set" tab only when at least one template survives.
2. **Generate templates.** For each quantitative chunk, ask the model for 1–3 templates as JSON, using *only* formulas and methods that appear in the chunk (prompt in section 9). Prefer the chunk's own worked examples as a starting point.
3. **Validate the structure** with the Pydantic `ProblemTemplate` model via Instructor (section 8). Reject anything malformed.
4. **Verify the math** (section 5). Reject any template that fails.
5. **Deduplicate** templates that share the same formula within a document.
6. **Save** survivors as `cards` with `type = 'problem'`, and create `card_states` rows so they enter the SM-2 schedule.

## 5. Verification (where correctness comes from)

Each template must pass every check before it is saved.

| # | Check | How | Catches |
| --- | --- | --- | --- |
| 1 | Schema | Pydantic parse (Instructor) | Missing fields, wrong types |
| 2 | Formula parses | `sympy.parsing.sympy_parser.parse_expr` with a function whitelist; the only free symbols allowed are the declared variables | Typos, undeclared variables, function calls you don't allow |
| 3 | Placeholders match | Every `{x}` in the question and steps is a declared variable | Questions that show a value the formula doesn't use, or the reverse |
| 4 | Sample run | Evaluate on about 20 random draws; every result must be finite and pass `constraints` (e.g. `result > 0`) | Division by zero, negative masses, nonsense ranges |
| 5 | Units agree | Evaluate with Pint quantities (`a * t**2 / 2` with `a` in m/s² and `t` in s should give a value in m) and compare with `answer_unit` | Wrong formula for the stated quantity |
| 6 | Independent solve | Fill one random instance and ask the model, in a *separate* call without the formula, to solve it step by step and give a number. Compare with the computed answer within tolerance. | A formula that doesn't match the problem's wording, such as a wrong physics setup |
| 7 | Grounded | The formula or method must appear in, or follow directly from, the source chunk; the template stores `chunk_id` | Problems from outside the student's lesson |

Check 6 is the key one. Code guarantees the arithmetic, and a second independent solve guards the *setup*. If the two disagree, the template is discarded (or kept as a draft for review, if you add an admin view later).

**Safety:** parse model-provided formulas with SymPy's `parse_expr` using a whitelist of functions (`sqrt`, `sin`, `cos`, `tan`, `log`, `exp`, `pi`, `molar_mass`) and only the declared symbols. No attribute access, and never Python `eval` or `exec`. Full details in `03-backend.md` §5.6.

## 6. Grading the student's answer

- **Parsing input:** accept `24`, `24 m`, `0.024 km`, `2.4e1`. Parse with Pint, convert to the answer's unit, then compare. A unit with the wrong dimension (e.g. `24 s` for a distance) is graded wrong with unit feedback.
- **Tolerance:** relative error ≤ `tolerance` (default 1%) so rounding along the way still passes. Optionally add a significant-figures mode for chemistry classes that grade on sig figs.
- **Missing unit:** if the student gives only a number, assume the expected unit and show a gentle "Remember to include units" note.
- **Known mistakes:** if the wrong answer matches a `common_mistakes` formula, show that mistake's feedback.
- **Result:** correct, close (within 5%, so likely rounding), or wrong. Log the attempt with the exact variable values the student saw.

## 7. Student experience

1. The deck page gets a **Problem set** tab next to Flashcards and Quiz questions, showing the templates by topic.
2. **Practice session:** one problem per screen, with the question in rendered math, a number input with a unit field, and a **Check** button.
3. **Stuck?** **Hint** reveals hints one at a time. **Show solution** reveals the worked steps one at a time, with this attempt's numbers filled in.
4. **After answering:** feedback (correct, close, or a known mistake), a source link to the page in their notes, and **Try a similar one**, which uses the same template with new numbers.
5. **Results:** score, problems missed with their solutions, and weak topics fed into the dashboard's "Weakest topics".
6. **Spaced repetition:** each template has its own `card_states` row. A correct answer counts as "Good", a correct answer after using hints (or after viewing the solution) as "Hard", a close answer as "Hard", and a wrong answer as "Again".

**Math rendering:** questions and steps may contain LaTeX (`\frac{1}{2}at^2`). Render it with KaTeX on web, and with KaTeX inside a WebView on mobile (or a React Native math library).

## 8. Data model

Problem sets use the existing tables (full definitions in `05-database-schema.md`):

- **`cards`:** `type = 'problem'`. `payload` holds the template from section 3, including `constraints` and `subject`.
- **`card_states`:** one row per user per template.
- **`attempts`:** `kind = 'problem_set'`, so problem sessions share the scoring tables with quizzes.
- **`problem_instances`:** the variables shown (`variables jsonb`), the computed `answer_value` and `answer_unit` (kept server-side), `hints_shown` and `solution_viewed`.
- **`attempt_answers`:** the student's `answer_value` and `answer_unit`, `hints_used` and `result` (`correct`, `close`, `wrong`), linked to the instance by `instance_id`.

Pydantic schema (same as `03-backend.md` §5.6):

```python
class VariableSpec(BaseModel):
    min: float
    max: float
    step: float = Field(gt=0)
    unit: str | None = None

class Mistake(BaseModel):
    formula: str
    feedback: str

class ProblemTemplate(BaseModel):
    topic: str
    subject: Literal["math", "physics", "chemistry"]
    question: str                       # LaTeX allowed; variables as {name}
    variables: dict[str, VariableSpec]  # names match ^[a-zA-Z_]\w*$
    answer_formula: str                 # SymPy-parsable, only declared variables
    answer_unit: str | None
    tolerance: float = Field(default=0.01, ge=0, le=0.05)
    constraints: list[str] = []         # e.g. "result > 0"
    hints: list[str] = Field(min_length=1, max_length=3)
    solution_steps: list[str]           # computed values as {{expression}}
    common_mistakes: list[Mistake] = Field(default=[], max_length=3)
```

## 9. Prompt sketch

```
You create practice problem templates for a student from their own lesson notes.

Rules:
- Use only formulas, constants and methods that appear in the notes below.
- Return 1–3 templates as JSON matching the schema. Return [] if the notes have no
  calculations worth practising.
- Put variables in the question as {name}. Give each a realistic min, max, step and unit.
- answer_formula is a SymPy expression (use ** for powers) using only the declared
  variables and numbers.
  Do NOT compute any numeric answers yourself.
- solution_steps explain the method. Write computed values as {{expression}}; the app
  fills them in.
- common_mistakes lists up to 3 typical wrong formulas with one-line feedback.
- Use LaTeX for math in question and steps.

Notes (source chunk, pages 7–8):
<<<chunk text>>>
```

The independent-solve check (section 5, check 6) uses a separate short prompt: "Solve this problem step by step. End with `ANSWER: <number> <unit>`." It gets one filled-in instance and no formula.

## 10. Subject-specific notes

**Chemistry**
- **Molar masses:** compute them in code from the chemical formula with a periodic-table lookup. Never let the model supply a molar mass as a number. The template references a formula string like `NaCl`, and a helper `molar_mass("NaCl")` is exposed to the SymPy evaluator.
- **Balancing equations:** this isn't a formula template. Add a separate problem kind whose checker parses the student's coefficients and counts atoms of each element on both sides.
- Allow sig-fig grading as an option per deck.

**Math**
- For "solve for x", build the problem from the answer: pick `x`, then construct the equation (e.g. pick `x`, `a`, `b`, and show `a·x + b = {a*x+b}`). The answer is known by construction.
- Symbolic answers (expressions rather than numbers) are later work. Check them with SymPy in the backend (`simplify(student - expected) == 0`), or by evaluating both expressions at several random points.

**Physics**
- Units do most of the checking. Keep unit-aware evaluation on for every physics template.
- Limit constants to a fixed table (g = 9.8 m/s², etc.) chosen per deck, so the app matches what the teacher uses (9.8 vs 9.81).

**Programming**

The same rule applies: the AI writes the problem, and **running real code** decides the answer. A language model can be wrong about what code prints, especially with off-by-one loops, integer division or mutable defaults.

- **Detecting coding notes:** chunks with code blocks, or keywords like `def`, `for`, `function`, `class`, are marked as programming chunks. The language comes from the notes (Python, JavaScript, Java, C…). Problems use only constructs the notes have already covered.
- **MVP problem types** (no student code is run):

  | Type | Example | How the answer is made trustworthy |
  | --- | --- | --- |
  | Predict the output | "What does this print?" with a 5–10 line snippet | The backend runs the snippet in a sandbox at generation time; the real stdout becomes the answer. Snippets that error, time out or print nothing are dropped. |
  | Fill in the blank | A function with one line missing, plus 4 options | Each option is inserted and run against the AI's test cases; exactly one option must pass. |
  | Find the bug | Which line causes the wrong result? | The buggy version must fail at least one test and the fixed version must pass all tests. |
  | Order the lines (Parsons problem) | Drag shuffled lines into a working program | The correct order is run against the tests; alternative orders that also pass are accepted. |

- **Templating:** like numeric problems, snippets can have variables (`n = {n}`, list contents, loop bounds). Each "Try a similar one" gives new values, and the expected output is recomputed by running the code.
- **Grading predicted output:** compare after trimming trailing spaces and line endings. Optionally ignore case for words like `True`/`true` when the deck allows.
- **Running code safely — you don't build a sandbox, you use one.** AI-written code is untrusted, since the notes it was written from could contain text that steers the model toward harmful code. **Never run it with `exec()` or a plain `subprocess` in the API or worker.**
  - **MVP — hosted Judge0 API, generation time only.** The worker sends each snippet to Judge0 (hosted on RapidAPI, small free tier, dozens of languages) with a 2-second CPU limit and a memory cap, and gets back stdout, stderr, exit status and run time. Check the current free quota when signing up.
  - **Pre-compute variants.** For each templated snippet, generate about 5 versions with different values at generation time and store each one's real output on the card. "Try a similar one" picks from those, so **practice sessions never call the sandbox** and free-tier limits barely matter.
  - **Python-only alternative with no external service:** run snippets inside WebAssembly from the Python worker (`wasmtime` + a Python WASI build). It has no network or file access by default, with memory and fuel (CPU) limits. More setup than Judge0, but $0 and works on free hosting.
  - **Avoid self-hosting Judge0 or Piston for now.** They need Docker with privileged containers, which free hosting generally doesn't allow, so they mean paying for a VM.
- **Later — write a function:** the student writes code and it's checked against visible and hidden tests. Run it **in the student's browser** with Pyodide (Python compiled to WebAssembly): in a Web Worker on web, and inside a WebView on mobile. The student's device is the sandbox, so the server stays safe and it costs nothing. Since it's practice, a student tampering with their own grading only cheats themselves. For scored sessions, hidden tests are re-run on the server through the same Judge0 or WebAssembly path.
- **Schema:** `cards.type = 'problem'` with `subject = 'programming'` and a payload of `{language, kind (output|blank|bug|parsons), code_template, variables, options?, tests[], explanation, variants: [{values, code, expected_output}]}`. `problem_instances` stores which variant was shown.
- **UI:** code is shown in a monospace block with syntax highlighting (Shiki on web, a highlighted WebView on mobile). Answers for "predict the output" use a multiline monospace input.

## 11. Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Equations come out garbled from PDF text extraction (fractions flattened, superscripts lost) | Test 2–3 real PDFs first. MVP: support pasted notes and clean text PDFs. Later: send pages with heavy math to a vision model to transcribe them as LaTeX. |
| Model writes a formula that doesn't match the wording | Independent-solve check (section 5, check 6); student "Report problem" button |
| Unrealistic numbers (a 900 kg person) | Ranges set by the model with the sample-run constraints; tighten with per-subject sanity rules |
| Student's correct answer marked wrong because of rounding | Relative tolerance plus a "close" result; show the exact computed value in the solution |
| Cost | Only quantitative chunks are processed; at most 3 templates per chunk; one extra small call per template for verification |

## 12. MVP scope and build order

**In the MVP**
- Numeric answers with units, physics and chemistry templates, simple math templates
- Programming problems that don't run student code: predict the output, fill in the blank, find the bug, order the lines (answers verified by running code in a sandbox at generation time)
- Hints, step-by-step solution, "Try a similar one"
- Verification checks 1–7
- Scores and SM-2 scheduling for templates

**Later**
- Balancing-equation checker, symbolic answers, vision-model extraction for formula-heavy PDFs, diagrams, checking the student's working step by step
- "Write a function" coding problems, run in the browser with Pyodide and re-checked on the server for scored sessions

**Build order**
1. The SymPy/Pint evaluator and grader in the backend (`backend/app/services/problems/`), with unit tests. Web and mobile only display the results the API returns.
2. Template prompt, Pydantic schema and verification checks, run on a few sample chunks from a script.
3. Save templates as cards and add the deck's Problem set tab.
4. Practice screen: input, check, hints, solution, similar problem.
5. Scoring, SM-2 and dashboard integration.
6. Report-problem flow.

## 13. Open questions

- Should a problem set also offer multiple-choice mode, using the `common_mistakes` values as distractors? This is easier on mobile keyboards.
- Should students choose a difficulty, for example by widening the variable ranges or picking multi-step templates?
- Which value of g, and which sig-fig rules, should be the default for Philippine high school and college courses?