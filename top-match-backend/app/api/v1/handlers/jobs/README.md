# Jobs

Recruiters create a job (title, description, requirements, optional `form_fields`) and receive a
non-guessable `public_slug` plus `public_url` for LinkedIn/Indeed. They can list and edit their
own jobs, inspect application counts, and close a job (sets `closed_at`, stops new applies).
`form_fields` cannot be changed after the first application (409). The public GET is
unauthenticated and returns title, description, requirements, `form_fields`, status, and the
privacy / AI-screening notices plus the hiring-law disclaimer so the candidate apply page can
render them. Recruiter routes look up by `id` and `recruiter_id`; another recruiter's job is 404,
not 403.

The leaderboard is polled (no SSE). Items are sorted by `score` descending, nulls last,
then `created_at`. `status` may repeat (`?status=scored&status=processing`) and `stage`
filters by `current_phase` (`accept`, `knockout`, `answers`, `resume`). `counts` always
cover every status on the job, including `knocked_out`, even when filtered. Job detail and leaderboard include `screening_disclaimer`. CSV export takes
either `application_ids` or `top_n`. The first CSV row is the disclaimer; cells that
start with `=`, `+`, `-`, `@`, tab, or carriage return are prefixed with `'`. The CSV
includes `stopped at` (phase) and `reason` columns for applicants that were not scored.

Radio, dropdown and number form fields may carry a `knockout` (`allowed_values` or `min`,
plus a recruiter-written `reason`; the field must be `required`). A yes/no knockout is a
radio field with `Yes`/`No` options. Radio, dropdown, checkboxes and number fields may
carry `scoring` weights for the code-only answers score. Neither is returned on the public
job endpoint. Job responses include `form_warnings` for knockouts that look like age
proxies (graduation year, maximum experience) and for questions about current or past
salary; warnings never block saving.

Number, radio and dropdown fields may also carry a `condition` (`preset`, `importance` of
`must` / `preferred` / `info`, a candidate-facing `summary`, and a `salary` range for
expected salary). A must condition needs a `knockout`, a preferred one needs `scoring`, an
info one needs neither. A form allows up to 20 questions and, separately, 10 conditions.
The public job returns `before_you_apply` (the must summaries) and hides `condition`. Job
detail includes `condition_knockouts`: per must condition, how many applicants it ever
`stopped` and how many were `moved_forward` after. The CSV adds a `stopped by condition`
column and marks condition columns with their importance.

Create and edit reject questions, conditions or requirements text that screen on personal
characteristics (gender, age, marital status, religion, ethnicity/caste/race, nationality or
citizenship, disability, photos) with 422 and
`guardrail_errors: [{ target, category, message, suggestion }]`, where `target` is a field id
or `requirements`.

With a registered company account, recruiter routes require
`Authorization: Bearer {{token}}` using the access JWT from `/api/v1/auth/register` or
`/api/v1/auth/login`. Replace `{{host}}` with `http://127.0.0.1:8000`. After create, copy
`id` into `{{jobId}}` and `public_slug` into `{{slug}}`.

# List Endpoints

### Create Job

```http
POST http://127.0.0.1:8000/api/v1/jobs HTTP/1.1
content-type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1N2Q2YWRjOS1lY2M0LTQ1MzYtYjMxNS1jM2Q5ZjhkYTMzOWEiLCJ0eXBlIjoiYWNjZXNzIiwiaWF0IjoxNzkwOTM0NDQxLCJleHAiOjE3OTA5MzUzNDF9.HS48BSglTJa37Nid1dGKaq69i2V8w6jFhtALddxHiIc

{
  "title": "Senior Backend Engineer",
  "description": "Build the Top Match screening API.",
  "requirements": "Python, FastAPI, PostgreSQL"
}
```

### List Jobs

```http
GET {{host}}/api/v1/jobs HTTP/1.1
content-type: application/json
Authorization: Bearer {{token}}

{
}
```

### Get Job

```http
GET {{host}}/api/v1/jobs/{{jobId}} HTTP/1.1
content-type: application/json
Authorization: Bearer {{token}}

{
}
```

### Update Job

```http
PATCH {{host}}/api/v1/jobs/{{jobId}} HTTP/1.1
content-type: application/json
Authorization: Bearer {{token}}

{
  "title": "Staff Backend Engineer"
}
```

### Close Job

```http
POST {{host}}/api/v1/jobs/{{jobId}}/close HTTP/1.1
content-type: application/json
Authorization: Bearer {{token}}

{
}
```

### Get Public Job

```http
GET {{host}}/api/v1/public/jobs/{{slug}} HTTP/1.1
content-type: application/json

{
}
```

### Get Leaderboard

```http
GET {{host}}/api/v1/jobs/{{jobId}}/leaderboard?limit=50&offset=0 HTTP/1.1
Authorization: Bearer {{token}}
```

### Export CSV (top N)

```http
POST {{host}}/api/v1/jobs/{{jobId}}/exports HTTP/1.1
content-type: application/json
Authorization: Bearer {{token}}

{
  "top_n": 20
}
```

### Export CSV (selected ids)

```http
POST {{host}}/api/v1/jobs/{{jobId}}/exports HTTP/1.1
content-type: application/json
Authorization: Bearer {{token}}

{
  "application_ids": ["{{applicationId}}"]
}
```
