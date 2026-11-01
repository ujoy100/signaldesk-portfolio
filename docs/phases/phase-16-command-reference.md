# Phase 16 command reference

Create ignored development-only files `secrets/postgres_password.txt` and `secrets/auth_jwt_secret.txt`, then:

```bash
docker compose config --quiet
docker compose build
docker compose up -d
docker compose up -d --wait
docker compose ps
docker compose logs --tail=200 backend
curl -fsS http://localhost:8000/ready
curl -fsS http://localhost:5173/healthz
```

Build each reviewed target explicitly:

```bash
docker build --target runtime -t signaldesk-backend:local -f backend/Dockerfile .
docker build --target evaluation -t signaldesk-evaluation:local -f backend/Dockerfile .
docker build -t signaldesk-frontend:local frontend
docker run --rm signaldesk-backend:local python -c \
  "import importlib.util; assert importlib.util.find_spec('ragas') is None; assert importlib.util.find_spec('diskcache') is None"
docker run --rm signaldesk-evaluation:local python -c \
  "import importlib.metadata as m; from backend.app.evaluation.ragas_runner import _load_ragas; _load_ragas(); print(m.version('ragas'), m.version('diskcache'))"
```

Safe fictional seeding is explicit:

```bash
docker compose --profile tools run --rm seed
```

Non-destructive restart and stop:

```bash
docker compose restart postgres qdrant backend frontend
docker compose down
```

Do not add `-v` unless permanent removal of this Compose project's volumes is explicitly intended.

Check secrets without displaying them:

```bash
test -s secrets/postgres_password.txt
test -s secrets/auth_jwt_secret.txt
git check-ignore -q secrets/postgres_password.txt
git check-ignore -q secrets/auth_jwt_secret.txt
```

Run the bounded fictional HTTP acceptance from the backend container:

```bash
docker compose exec -T backend python -m backend.scripts.verify_compose_acceptance
```
