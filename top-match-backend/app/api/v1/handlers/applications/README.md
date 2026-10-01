# Applications

The frontend uploads the PDF first, then creates an application with JSON only.

1. `POST /api/v1/public/files` sends the raw PDF (`content-type: application/pdf`) and
   returns `{ "id": "<file_id>" }`. The API checks size, `%PDF-` magic bytes, encryption,
   and page count, then stores the file.
2. `POST /api/v1/public/jobs/{slug}/applications` sends `{ "email", "file_id" }` as
   `application/json`. Duplicate emails for the same job return 409. A missing or already
   used `file_id` returns 404 or 409. Closed jobs return 409. OCR is not run on apply
   (Stage 5).

Replace `{{host}}` with `http://127.0.0.1:8000`, `{{slug}}` with the job `public_slug`,
and `{{fileId}}` with the id from the upload response. No recruiter token.

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
  "file_id": "{{fileId}}"
}
```

### Duplicate Application (expect 409)

```http
POST {{host}}/api/v1/public/jobs/{{slug}}/applications HTTP/1.1
content-type: application/json

{
  "email": "candidate@example.com",
  "file_id": "{{fileId}}"
}
```

### Unknown Job Slug (expect 404)

```http
POST {{host}}/api/v1/public/jobs/does-not-exist/applications HTTP/1.1
content-type: application/json

{
  "email": "nobody@example.com",
  "file_id": "{{fileId}}"
}
```
