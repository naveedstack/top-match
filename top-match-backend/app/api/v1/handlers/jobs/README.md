# Jobs

Recruiters create a job (title, description, requirements) and receive a non-guessable
`public_slug` plus `public_url` for LinkedIn/Indeed. They can list and edit their own
jobs, inspect application counts, and close a job (sets `closed_at`, stops new applies).
The public GET is unauthenticated and returns only title, description, requirements, and
status so the candidate apply page can render. Recruiter routes look up by `id` and
`recruiter_id`; another recruiter's job is 404, not 403.

With a registered company account, recruiter routes require
`Authorization: Bearer {{token}}` using the access JWT from `/api/v1/auth/register` or
`/api/v1/auth/login`. Replace `{{host}}` with `http://127.0.0.1:8000`. After create, copy
`id` into `{{jobId}}` and `public_slug` into `{{slug}}`.

# List Endpoints

### Create Job

```http
POST {{host}}/api/v1/jobs HTTP/1.1
content-type: application/json
Authorization: Bearer {{token}}

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
