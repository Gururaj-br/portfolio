# Ask Gururaja

A portfolio that answers questions. My career lives in one YAML file, a FastAPI service renders it as a page, and `/api/ask` retrieves and scores the parts of it that match a visitor's question, then answers with citations.

```
data/profile.yaml   ← the only file you edit
app/main.py         ← FastAPI: page, /api/profile, /api/ask
app/retriever.py    ← TF-IDF retriever with synonym expansion, no dependencies
templates/          ← Jinja page
static/             ← CSS + JS
```

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000. Interactive API docs are at `/api/docs`.

```bash
pytest -q                                   # tests
curl "localhost:8000/api/ask?q=rag"         # ask a question
curl localhost:8000/api/profile/experience  # one section
```

## API

| Endpoint | Returns |
|---|---|
| `GET /api/profile` | The whole profile (minus the retrieval index) |
| `GET /api/profile/{section}` | One section: `person`, `experience`, `skills`, `projects`… |
| `GET /api/ask?q=…&k=3` | Top-k matching chunks with scores |
| `GET /healthz` | Health check |

## Updating content

Edit `data/profile.yaml` and push. To make something searchable, add a chunk under `index:` with an `id`, `title`, `answer` and `keywords`.

## Deploy

**Render (free tier).** In Render, choose *New → Blueprint*, pick this repo, and it reads `render.yaml`. Every push to `main` redeploys. Note that free instances sleep after inactivity, so the first visit can take ~30s.

**Fly.io.** `fly launch` (it detects the Dockerfile, set internal port 8000), then `fly deploy`.

**Any Docker host.**

```bash
docker build -t portfolio . && docker run -p 8000:8000 portfolio
```

### Custom domain with Cloudflare

1. Add your domain to Cloudflare and switch the registrar's nameservers to Cloudflare's.
2. Add the domain in your host (Render: *Settings → Custom Domains*). It gives you a target like `gururaja-portfolio.onrender.com`.
3. In Cloudflare DNS, add a `CNAME` for `@` (and `www`) pointing at that target, proxied (orange cloud).
4. Set SSL/TLS mode to **Full (strict)**.
