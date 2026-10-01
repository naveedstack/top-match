# Top Match Backend

FastAPI + async SQLAlchemy (asyncpg) + Alembic, managed with [uv](https://docs.astral.sh/uv/).

## Setup

```bash
cp .env.example .env          # then fill in real values
uv sync                       # creates .venv with Python 3.14 + all deps
source .venv/bin/activate
```

## Run

```bash
uvicorn app.main:app --reload
```

- API docs: http://127.0.0.1:8000/docs
- Liveness: `GET /api/v1/health`
- Readiness (checks DB): `GET /api/v1/health/ready`

## Migrations

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

Models must be imported in `app/models/__init__.py` for autogenerate to detect them.

## Quality checks

```bash
ruff check . && ruff format --check .
mypy app
pytest
```

## Dependencies

```bash
uv add <package>              # runtime dependency
uv add --dev <package>        # dev-only dependency
uv lock --upgrade             # upgrade everything within constraints
```
