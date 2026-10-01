# Health

Probes used by load balancers and during local setup. Liveness only checks that the
process is serving HTTP. Readiness runs `SELECT 1` against PostgreSQL and returns 503
if the database is down.

`{{host}}` is the API origin, for example `http://127.0.0.1:8000`. These routes do not
require a recruiter token.

# List Endpoints

### Liveness

```http
GET {{host}}/api/v1/health HTTP/1.1
content-type: application/json

{
}
```

### Readiness

```http
GET {{host}}/api/v1/health/ready HTTP/1.1
content-type: application/json

{
}
```
