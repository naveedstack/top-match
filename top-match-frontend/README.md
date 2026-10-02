# Top Match Frontend

Next.js (App Router, `src/`) + TypeScript + Tailwind + React Query + Axios.

## Setup

```bash
cp .env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000.

`NEXT_PUBLIC_API_URL` defaults to `http://127.0.0.1:8000/api/v1`.

- Types live in `src/types/` (`auth`, `jobs`, `applications`).
- Request functions live in `src/api/`. React Query hooks live in `src/hooks/`.
- `src/lib/api.ts` attaches the access token and, on `401`, refreshes once and retries. Refresh rotation is single-flight so parallel requests do not revoke each other.
- `useAuth()` from `src/context/auth-context.tsx` exposes `user`, `isAuthenticated`, `isLoading`, `login`, `register`, and `logout`.

The backend must allow this origin in `CORS_ORIGINS` (for example `http://localhost:3000`).
