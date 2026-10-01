# Auth

One company is one `Recruiter` account. Register with company name, email, and password
to receive a short-lived access JWT and a refresh JWT. Recruiter routes send the access
token as `Authorization: Bearer {{token}}`. Refresh rotates: the old refresh `jti` is
revoked and a new pair is issued. Logout revokes the current refresh token.

Public candidate routes do not use these tokens. Google login is not in this API yet.

Replace `{{host}}` with `http://127.0.0.1:8000`. After register or login, copy
`access_token` into `{{token}}` and `refresh_token` into `{{refreshToken}}`.

# List Endpoints

### Register

```http
POST http://127.0.0.1:8000/api/v1/auth/register HTTP/1.1
content-type: application/json

{
  "company_name": "Acme Hiring",
  "email": "naveed221@gmail.com",
  "password": "naveed2211"
}
```

### Login

```http
POST http://127.0.0.1:8000/api/v1/auth/login HTTP/1.1
content-type: application/json

{
  "email": "naveed221@gmail.com",
  "password": "naveed2211"
}
```

### Refresh Tokens

```http
POST http://127.0.0.1:8000/api/v1/auth/refresh HTTP/1.1
content-type: application/json

{
  "refresh_token": "{{refreshToken}}"
}
```

### Logout

```http
POST http://127.0.0.1:8000/api/v1/auth/logout HTTP/1.1
content-type: application/json

{
  "refresh_token": "{{refreshToken}}"
}
```

### Current Recruiter

```http
GET {{host}}/api/v1/auth/me HTTP/1.1
content-type: application/json
Authorization: Bearer {{token}}

{
}
```
