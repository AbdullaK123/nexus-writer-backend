# Playwright adversarial E2E tests

These tests exercise the real React frontend against the real FastAPI backend. They deliberately avoid AI-dependent flows so failures are deterministic and attributable to Nexus itself.

Prerequisites:

```bash
cd frontend
npm install -D @playwright/test
npx playwright install chromium
```

Run PostgreSQL, Redis, migrations, and the backend API first. The Playwright config starts the Vite frontend automatically.

Defaults:

- frontend: `http://127.0.0.1:5173`
- backend API: `http://127.0.0.1:8000/api`

Override them with `E2E_FRONTEND_URL` and `E2E_API_BASE_URL`.

Run:

```bash
npm run test:e2e
```

The assertions are intentionally descriptive. When one fails, the message should tell you which production invariant was violated rather than merely reporting that a selector was missing.
