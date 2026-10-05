# Applications

The frontend asks the API for a short-lived PUT URL, uploads the PDF to storage,
then confirms the object. Apply is JSON only.

1. `POST /api/v1/public/files/upload-url` sends `{ "content_type": "application/pdf",
   "byte_size": N }` and returns `{ "file_id", "upload_url", "headers", "expires_at" }`.
   Rejects non-PDF types and sizes over 5 MB.
2. The browser `PUT`s the PDF to `upload_url` with the returned `headers` (S3 when
   `STORAGE_BACKEND=s3`; a local API PUT when `STORAGE_BACKEND=local`).
3. `POST /api/v1/public/files/{file_id}/complete` checks the object, validates the PDF
   (magic bytes, readable, page count), and returns `{ "id": "<file_id>" }`. Invalid
   objects are deleted.
4. `POST /api/v1/public/jobs/{slug}/applications` sends
   `{ "email", "file_id", "consented": true, "answers": { "<field_id>": ... } }` as
   `application/json` and returns `202` with status `received`. `answers` is optional when the
   job has no custom fields. Invalid answers return 422 with `field_errors`. `consented` must be
   true (privacy/AI notice on the public job). Duplicate emails for the same job return 409. A
   missing or already used resume `file_id` returns 404 or 409. Closed jobs return 409. OCR and
   scoring run in a background task after the response and still use only the resume.

Custom file fields use the same sign/PUT/complete pattern on
`POST /api/v1/public/jobs/{slug}/attachments/upload-url` and
`POST /api/v1/public/attachments/{file_id}/complete`. Allowed types are the field's `accept`
list (pdf, docx, png, jpeg). Recruiters download them from `GET /api/v1/public/attachments/{token}`.

Recruiters poll the job leaderboard, open `GET /api/v1/applications/{id}` for the
evaluation plus a 15-minute `resume_url`, and `POST /api/v1/applications/{id}/rescore`
to retry a `failed` row. `GET /api/v1/public/resumes/{token}` streams the PDF (no
Bearer header). Another recruiter's application is 404.

Replace `{{host}}` with `http://127.0.0.1:8000`, `{{slug}}` with the job `public_slug`,
and `{{fileId}}` with the id from the complete response. Recruiter routes need
`Authorization: Bearer {{token}}`. Public apply and resume download do not.

# List Endpoints

### Request Upload URL

```http
POST {{host}}/api/v1/public/files/upload-url HTTP/1.1
content-type: application/json

{
  "content_type": "application/pdf",
  "byte_size": 102400
}
```

### Put Resume (local storage)

```http
PUT {{host}}/api/v1/public/files/{{fileId}}/content HTTP/1.1
content-type: application/pdf

< /path/to/resume.pdf
```

When `STORAGE_BACKEND=s3`, PUT to the returned `upload_url` instead of this path.

### Complete Upload

```http
POST {{host}}/api/v1/public/files/{{fileId}}/complete HTTP/1.1
```

### Apply To Job

```http
POST {{host}}/api/v1/public/jobs/{{slug}}/applications HTTP/1.1
content-type: application/json

{
  "email": "candidate@example.com",
  "file_id": "{{fileId}}",
  "consented": true,
  "answers": {
    "{{fieldId}}": "Remote, 4 years of FastAPI"
  }
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
