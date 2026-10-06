# Signal — Telecom Churn Dashboard

A Vite + React dashboard for the `analytics`, `customer`, and `prediction` FastAPI routes:
login page, an overview dashboard (stat cards + two charts), and a filterable,
paginated customer table with a per-row churn prediction action.

## Setup

```bash
npm install
cp .env.example .env   # then set VITE_API_BASE_URL to your FastAPI server
npm run dev
```

Runs at `http://localhost:5173` by default.

## ⚠️ One assumption you'll likely need to fix: login

Your `routes/auth.py` wasn't included with the files you shared, so `src/api/auth.js`
assumes the common FastAPI pattern: a form-encoded `OAuth2PasswordRequestForm` login at

```
POST /auth/token
Content-Type: application/x-www-form-urlencoded
  username=...&password=...
->
{ "access_token": "...", "token_type": "bearer" }
```

If your real login route has a different path, expects JSON instead of a form body,
or returns a different response shape, that's the **only** file you need to edit —
everything else (the token storage, the `Authorization: Bearer` header on every
request, the 401 → redirect-to-login handling) is already wired up in `src/api/client.js`
and doesn't need to change.

## Backend CORS

Since the frontend (`localhost:5173`) and API (likely `localhost:8000`) are different
origins, make sure your FastAPI app allows it, e.g.:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## What maps to what

| Route | Used in |
|---|---|
| `GET /analytics/churn-rate` | Dashboard bar chart |
| `GET /analytics/distribution` | Dashboard stat cards + donut chart |
| `GET /customer/` | Customers table (filters + pagination) |
| `POST /prediction/{customer_id}` | "Predict" button per table row |

`GET /customer/export` wasn't implemented yet in `customer.py` (the route body is
`pass`), so no export button was added — happy to wire one up once that route returns
something (e.g. a CSV `StreamingResponse`, which the import already sets up for).

## Structure

```
src/
  api/            axios client, one file per route group
  context/        auth state (token in localStorage)
  components/     Sidebar, Topbar, table, charts, filters, pagination, SignalBars
  layouts/        DashboardLayout (sidebar + routed content)
  pages/          Login, Dashboard, Customers
```

## Linting

```bash
npm run lint
```
