# Applications

The frontend uploads the PDF first, then creates an application with JSON only.

1. `POST /api/v1/public/files` sends the raw PDF (`content-type: application/pdf`) and
   returns `{ "id": "<file_id>" }`. The API checks size, `%PDF-` magic bytes, encryption,
   and page count, then stores the file.
2. `POST /api/v1/public/jobs/{slug}/applications` sends
   `{ "email", "file_id", "consented": true }` as `application/json` and returns `202`
   with status `received`. `consented` must be true (privacy/AI notice on the public job).
   Duplicate emails for the same job return 409. A missing or already used `file_id`
   returns 404 or 409. Closed jobs return 409. OCR and scoring run in a background task
   after the response.

Recruiters poll the job leaderboard, open `GET /api/v1/applications/{id}` for the
evaluation plus a 15-minute `resume_url`, and `POST /api/v1/applications/{id}/rescore`
to retry a `failed` row. `GET /api/v1/public/resumes/{token}` streams the PDF (no
Bearer header). Another recruiter's application is 404.

Replace `{{host}}` with `http://127.0.0.1:8000`, `{{slug}}` with the job `public_slug`,
and `{{fileId}}` with the id from the upload response. Recruiter routes need
`Authorization: Bearer {{token}}`. Public apply and resume download do not.

# List Endpoints

### Upload Resume

```http
POST {{host}}/api/v1/public/files HTTP/1.1
content-type: application/pdf

< /path/to/resume.pdf
```

### Apply To Job

```http
POST {{host}}/api/v1/public/jobs/{{slug}}/applications HTTP/1.1
content-type: application/json

{
  "email": "candidate@example.com",
  "file_id": "{{fileId}}",
  "consented": true
}
```

### Duplicate Application (expect 409)

```http
POST {{host}}/api/v1/public/jobs/{{slug}}/applications HTTP/1.1
content-type: application/json

{
  "email": "candidate@example.com",
  "file_id": "{{fileId}}",
  "consented": true
}
```

### Unknown Job Slug (expect 404)

```http
POST {{host}}/api/v1/public/jobs/does-not-exist/applications HTTP/1.1
content-type: application/json

{
  "email": "nobody@example.com",
  "file_id": "{{fileId}}",
  "consented": true
}
```

### Get Application

```http
GET {{host}}/api/v1/applications/{{applicationId}} HTTP/1.1
Authorization: Bearer {{token}}
```

### Rescore Failed Application

```http
POST {{host}}/api/v1/applications/{{applicationId}}/rescore HTTP/1.1
Authorization: Bearer {{token}}
```

### Download Resume PDF

```http
GET {{host}}/api/v1/public/resumes/{{resumeToken}} HTTP/1.1
```
