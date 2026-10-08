# Top Match: Screening Upgrade Plan

This is the implementation plan for the next stage of Top Match. Work through it one step at a time.

## How to work on this plan

- Before writing code for a step, read the relevant code and explain how it works today. Then propose a short plan: files to change, migrations to add, tests to write. Wait for approval.
- Implement only the step you were asked to do. Stop at the end of it and summarize what changed, what you tested and anything left open.
- Follow the repo's existing conventions (folder layout, naming, migration tool, test setup). Table and field names below are suggestions; adapt them to the codebase.
- Ask before adding a new service or infrastructure dependency (Redis, SQS, Celery, a new SaaS). Small, well-known libraries are fine; mention them in your summary.
- Every schema change needs a migration that runs cleanly on an existing database with data, with a downgrade where practical.
- Run the full test suite, linter and type checker before finishing a step.

## Rules that must not break

1. Submitting an application never waits on the model and never fails because of it.
2. The PDF text layer, metadata and hidden text never reach the model. Only OCR text from page images does.
3. No automated step removes a candidate from the recruiter's view. Every applicant who wasn't scored (knocked out, refused, unreadable, failed, waiting on budget) is visible in its own list, with the reason and a way to override or retry.
4. Resume text, emails and answers are never written to logs. Log application IDs only.
5. A recruiter can never see or act on another company's jobs or applicants. Keep returning "not found".
6. The model never produces the final score. The server computes it.

## Step 0: Make public claims match the product

The landing page says ranking is "real time" and shows "Live Sync: 2s latency". Scoring takes about 24 seconds per resume today, and the demo pipeline shows staged screening that isn't built yet.

- Reword the landing page so every claim matches what the code does today. For example, say "ranked within minutes" instead of "real time", and remove the latency figure.
- Label the demo pipeline card as an example.
- Change only the copy; leave layout and styling alone.

## Step 1: Phase pipeline and knockouts

Goal: cheap checks run first, and only applications that pass them reach the resume model.

**Data**
- `phase_results` table: `id, application_id, phase (accept | knockout | answers | resume), outcome (pass | fail | review | error | skipped), reasons (jsonb), evidence (jsonb), config_version, model_name, prompt_version, input_tokens, output_tokens, cost_usd, latency_ms, created_at`.
- On applications, store the furthest phase reached and the phase that stopped it. Alternatively, derive both from `phase_results`; pick one approach and use it consistently.

**Knockout questions**
- In the form builder, recruiters can mark a question as a knockout, separate from ordinary questions. Support three kinds: yes/no with a required answer, number with a minimum, and dropdown with allowed values.
- Each knockout has a recruiter-written reason shown when someone fails it (e.g. "Not authorized to work in Pakistan").
- Knockouts are evaluated in code, with no model call.
- Show a warning (not a block) when a knockout looks like an age proxy: graduation year, date of birth, or a maximum number of years of experience.

**Answers phase**
- Recruiters can optionally add weights to dropdown, radio, checkbox and number questions. These answers are scored in code.
- Free-text answers are stored and shown, but not sent to the model in this step.

**Pipeline runner**
- Run phases in order: accept, knockout, answers, resume. Each phase writes a `phase_results` row. A failed phase stops the pipeline, so the resume phase runs only if the earlier phases passed.
- Keep the existing statuses working (received, processing, scored, refused, failed), or map them cleanly onto the new phases.

**Recruiter view**
- The leaderboard gets a stage column and a filter by stage.
- Knocked-out applicants appear in a separate, collapsed list with their reason and a "Move forward anyway" action. The action is recorded and sends the application to the next phase.
- Refused, unreadable and failed applicants each get a visible list with the reason and a retry or override action.
- The CSV export adds "Stopped at" and "Reason" columns.

**Tests**
- A knockout failure never calls the model (mock the model client and assert zero calls).
- An override moves the application forward and is recorded.
- The export includes the new columns.

## Step 2: Per-requirement scoring and versioning

Goal: the score is built from verdicts a recruiter can check, and every score is tied to the exact requirements it was judged against.

**Structured, versioned requirements**
- Requirements become a list of items: `id, text, kind (must | nice), weight`. Migrate existing free-text requirements by splitting them into items, and let the recruiter review the result.
- Editing requirements creates a new version (`job_requirement_versions`). Old versions are never changed.
- Each evaluation stores `requirements_version_id`, `prompt_version`, `model_name` and the model settings.
- If applicants were scored against an older version, show "N applicants were scored against older requirements" with a "Rescore" action.

**Model output**
- For each requirement, the model returns `requirement_id`, `verdict (met | partial | not_met | no_evidence)`, `quotes` (verbatim from the resume) and a one-sentence `rationale`.
- It also returns `is_resume`, `injection_suspected`, and a list of dated roles: `title, employer, start, end, quote`.
- The model does not return an overall score.
- In the prompt, wrap the resume text in clear delimiters and say that it is data to evaluate, never instructions.

**Server-side checks**
- Quote verification: normalize both the quote and the resume text before matching (Unicode NFKC, ligatures like "ﬁ", hyphenation at line breaks, whitespace, case). Allow a high-threshold fuzzy match for OCR noise, but numbers inside a quote must match exactly.
- A `met` or `partial` verdict with no verified quote is downgraded to `no_evidence`.
- Years of experience: compute them in code from the dated roles, merging overlapping ranges and treating "Present" as today. Judge "N+ years" requirements from that number, not from the model's verdict.
- Score: a weighted sum of verdicts using the recruiter's weights (e.g. met = 1, partial = 0.5). Any must-have that is `not_met` caps the result.
- Bands: Strong, Possible, Weak, with thresholds in config. The leaderboard groups applicants by band and sorts by score inside each band.

**Recruiter view**
- The applicant detail page shows a table with columns for requirement, verdict and quote. Clicking a quote highlights it in the resume text.
- Recruiters can adjust weights; scores recompute without calling the model.

**Tests**
- Quote verification cases:
  - Pass: exact match, ligature, hyphenation, extra whitespace, small OCR typo.
  - Fail: a changed number, a made-up quote.
- The downgrade rule.
- Years computation, including overlaps and "Present".
- Score and band computation.
- Rescoring after a requirements edit.

## Step 3: Queue, throughput and cost control

Goal: no work is lost on deploy or restart, several applications score at once, and spending has a ceiling.

- Replace in-process scoring with a Postgres-backed queue:
  - A `screening_tasks` table.
  - Workers claim tasks with `SELECT … FOR UPDATE SKIP LOCKED`.
  - Each claim takes a lease (`locked_until`) that a heartbeat renews.
  - Failed tasks retry with exponential backoff, and move to a dead state after max attempts. Dead tasks show up in the recruiter's failed list.
  - If you'd rather use an existing library such as Procrastinate, propose it first.
- Insert the task in the same database transaction as the application, so every accepted application always has a task.
- Add a separate worker entrypoint in the same codebase, runnable as its own container. It shuts down cleanly on SIGTERM, and its concurrency is configurable.
- Spend caps: a daily cap per job and a global daily cap. Over a cap, tasks wait with a visible "waiting: budget" state instead of failing.
- Model calls: set a timeout, retry on 429 and 5xx errors, and record tokens, cost and latency in `phase_results`. Make the Gemini thinking budget configurable, so speed can be measured against quality.
- Add an optional per-job setting: verify the candidate's email before resume scoring runs.
- Add a load-test script: send 500 applications to one job within an hour, then assert none are lost or stuck.

## Step 4: Production hardening

- **Uploads:** browsers upload straight to S3 with presigned URLs under a `pending/` prefix, and files move to their final key on submit. Add a cleanup job for orphaned upload records. Document the S3 lifecycle rule that deletes `pending/` after 24 hours; it's an infrastructure step, listed at the end.
- **Rasterizer:** run it in a separate subprocess with limits on file size, page count, time and memory.
- **Manipulation signals (never sent to the model):**
  - Compare the PDF text layer with the OCR text. Text that exists in the file but isn't visible flags the application for review.
  - Measure how much of the resume copies the job description, and flag very high overlap.
- **Retention:**
  - Auto-close jobs that get no new applicants for a configurable number of days, so deletion can start.
  - Keep a minimal decision record (outcomes, reasons, versions, timestamps, no personal data) separate from candidate data and files.
  - Make retention configurable per company.
- **Accounts:** add `organizations` and `memberships` tables now, even with one recruiter per company, and move job ownership to the organization.
- **Auth:** if refresh tokens are stored in localStorage, move them to httpOnly, Secure, SameSite cookies.
- **Errors:** add Sentry to FastAPI, the worker and Next.js.
- **CI:** add a GitHub Actions pipeline that runs ruff, type checks, pytest against a Postgres service container, migrations on a fresh database, and the Next.js lint, type check and build.
- **Apply form:** add a CAPTCHA. Ask which provider to use before adding one.

## Step 5: Measuring quality

- Add a `recruiter_events` table that records when an application is opened, exported, rejected (with an optional one-tap reason), has a knockout overridden, or is rescored.
- Per-job shadow mode: scores run but stay hidden until the recruiter finishes screening by hand, so the two results can be compared.
- Offline eval scripts (not in the request path):
  - Stability: score the same resume 5 times and report how much verdicts and score vary.
  - Counterfactual: swap the name, a gender-coded name and the university, then check that verdicts don't change.
  - Agreement: given a recruiter's labeled shortlist, report recall at the top. For example, of the recruiter's top 10, how many are in our top 20.
- A stats page per job showing:
  - Completion rate
  - How many applicants stopped at each phase
  - Band distribution
  - Cost per scored applicant
  - Time to score (p50 and p95)

## Outside this plan (done by hand, not by Claude Code)

- AWS WAF rate limiting on the apply endpoint, the S3 lifecycle rule, and RDS backups.
- Switch to paid Gemini or Vertex AI so resume data isn't used for training.
- Privacy notice: list Google as a sub-processor, and say that backups keep deleted data until they expire.
- Hiring-law review before real candidates go through the system: the EU AI Act applies from December 2027 and Colorado's law from January 1, 2027.