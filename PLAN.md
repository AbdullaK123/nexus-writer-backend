# Nexus Writer — Build & Deployment Plan

End-state: production v1 deployed to Render (or Railway) with managed Postgres + pgvector, Stripe billing, Sentry, email digest, and Playwright E2E coverage.

**Starting position** — Backend ~85% (auth, story/chapter CRUD, scene extraction+embedding, SSE chat agent). Frontend has auth + design tokens + every data hook wired; every screen past login is a stub.

**Cross-cutting decisions** (change here if you disagree)
- Editor: **Tiptap (ProseMirror)**
- Charts: hand-rolled SVG (d3 already in deps if needed)
- Notifications: 30s short-poll for v1, SSE upgrade later
- Avatar: initials-only, no upload in v1
- Email provider: **Resend**
- Host: **Render** (Railway plan is identical)

**Excluded from v1**: collaboration/sharing, public story pages, i18n, mobile apps, TTS, full responsive layouts.

---

## Phase 0 — Design system + app shell

> Blocks every other phase. Do not skip.

- [ ] Build primitive components in `frontend/src/components/common/` driven by tokens in `frontend/src/index.css`:
  - [X] `Card` (+ header/title/content slots)
  - [X] `Pill` (status + filter variants)
  - [X] `Toggle`
  - [X] `Input`, `Textarea`, `Select`
  - [X] `Tabs`
  - [X] `Modal`
  - [X] `Popover`
  - [X] `Toast` + `ToastProvider`
  - [X] `EmptyState`
  - [X] `LoadingSkeleton`
  - [X] `ErrorBanner`
  - [X] `AvatarBadge` (initials, deterministic color)
  - [X] `IconButton`
  - [X] `Kbd`
- [X] `CommandPalette` primitive (⌘K), data source injected per screen
- [X] `AppShell` layout: 64px left vertical rail with `NX` mark + nav items (HOME / EDIT / CHAT / STAT / SET), active state, hover labels
- [X] Mount shell under protected route group in `frontend/src/AppRouter.tsx`
- [X] Delete unused stub `frontend/src/App.tsx`
- [X] Dev-only `/dev/kitchen-sink` route rendering every primitive in every variant
- [] Vitest snapshot tests for each primitive
- [] **Verify**: keyboard nav (Tab / Esc / arrows) works in palette, tabs, modals

---

## Phase 1 — Dashboard (Home) + Library

- [X] **Backend**: `GET /me/dashboard` → `{ total_words, total_stories, chapters_total, chapters_published, scenes_tracked, streak_days, jump_back_in: [chapter_card x3] }`
  - [X] `DashboardService.get_summary(user_id)` aggregating across stories/chapters/scenes
  - [X] Streak from `chapter.updated_at` distinct-day series
  - [X] `DashboardResponse` schema
- [X] **Backend**: extend story list with `?status=ongoing|hiatus|complete` and ensure cards return `chapter_count, word_count, last_touched_at, status`
- [X] **Frontend**: `frontend/src/components/story/DashboardPage.tsx`
  - [X] Welcome header with display name + streak chip
  - [X] 4 stat cards (TOTAL WORDS / CHAPTERS / SCENES TRACKED / STREAK)
  - [X] "Jump back in" row — 3 recent chapter cards
  - [X] Library grid with status filter pills (ALL / ONGOING / HIATUS / COMPLETE)
  - [X] `BeginNewStoryCard` that expands inline into create form
- [X] **Frontend**: `useDashboard` hook in `frontend/src/data/queries/dashboard.ts`
- [X] **Frontend**: status filter via TanStack Router search param
- [X] Click story card → `/stories/$storyId`
- [ ] **Verify**: pytest integration — seed 4 stories, `/me/dashboard` returns correct counts + streak
- [ ] **Verify**: Playwright — login, dashboard renders with seeded data, filter pills work

---

## Phase 2 — Story Detail page

- [ ] **Backend**: `GET /stories/{id}/pulse` → top-4 insight cards (returns `{status: "pending"}` until Phase 5 snapshot exists)
- [ ] **Frontend**: `StoryDetailPage`
  - [ ] Breadcrumb `← YOUR LIBRARY / {story.title}`
  - [ ] Hero (title, status pill, "Book N of M · started X ago", description)
  - [ ] Action row: `Settings` / `Ask Nexus` / `+ New Chapter`
  - [ ] Right rail stat tiles (chapters, words, scenes, streak)
  - [ ] Chapter list with DRAFT / PUBLISHED filter pills
  - [ ] "Book Pulse" insight cards column
- [ ] `+ New Chapter` opens modal → `useCreateChapter` → routes to editor
- [ ] `Ask Nexus` placeholder route until Phase 4
- [ ] Chapter row click → editor route
- [ ] **Verify**: pulse endpoint returns 200 with `pending` status when no extraction done
- [ ] **Verify**: Playwright — dashboard → story → chapter list + pulse cards

---

## Phase 3 — Chapter Editor + inline AI suggestions + ⌘K

### 3.A Editor surface

- [ ] Install `@tiptap/react @tiptap/starter-kit @tiptap/extension-placeholder`
- [ ] Add `chapter.word_target` column + migration (if not present)
- [ ] `frontend/src/components/chapter/EditorPage.tsx`
  - [ ] Collapsible chapter rail (number + title + status)
  - [ ] Centered prose canvas
  - [ ] Top breadcrumb pill (`CH 45 · THE GARDEN...`)
  - [ ] Top-right word-count HUD (`3,420 / 4,000 WORDS · SAVED`)
  - [ ] Bottom prev/next chapter pills + centered search trigger
- [ ] Debounced autosave (1.5s) → PATCH `/chapters/{id}` via `useUpdateChapter`
- [ ] HUD state machine: SAVED / SAVING / ERROR

### 3.B Command palette / search

- [ ] Wire ⌘K to global `CommandPalette` with `useStorySearch`
- [ ] Result rows: scene title, chapter, hybrid FTS+vector badge, score, tension/pacing pills
- [ ] Keyboard: ↑↓ navigate, ↵ open, ⇧↵ open new tab, Esc close
- [ ] Empty state: "Nothing in your book about that" with Ask-the-agent CTA

### 3.C Inline AI suggestions

- [ ] **Backend**: `POST /chapters/{id}/suggestions` body `{ kinds[], sensitivity, ranges? }` → `[{id, range, kind, original, suggested, rationale}]`
- [ ] **Backend**: `POST /chapters/{id}/suggestions/{sid}/refine` body `{instruction}`
- [ ] **Backend**: `chapter_suggestion_events` table for accept/reject persistence
- [ ] **Backend**: cache suggestions per chapter content hash
- [ ] **Frontend**: Tiptap decoration plugin paints underlines (style=cyan, grammar=warning, continuity=error, pacing=info)
- [ ] **Frontend**: `SuggestionPopover` with ORIGINAL / SUGGESTED / rationale + ACCEPT / REJECT / REFINE
- [ ] Accept replaces range in doc; reject hides; refine calls refine endpoint
- [ ] Trigger suggestion run on save (debounced, gated by user preference from Phase 6)
- [ ] **Verify**: Playwright — open chapter, type, SAVED within 2s; reload persists content
- [ ] **Verify**: ⌘K → search → ↵ → editor scrolls to matched scene
- [ ] **Verify**: clichéd line → underline → click → Accept → text updates
- [ ] **Verify**: pytest — suggestion endpoint deterministic with mocked AI provider

---

## Phase 4 — Chat (Ask Nexus) with SSE streaming

- [ ] Implement `frontend/src/infrastructure/sse/index.ts` (currently empty)
  - [ ] Fetch + `eventsource-parser` wrapper returning `AsyncIterable<ChatEvent>`
  - [ ] Event types: `token`, `tool_call_start`, `tool_call_result`, `cited_scenes`, `done`, `error`
- [ ] `useChatStream` hook — streaming state + cancellation
- [ ] `frontend/src/components/chat/ChatPage.tsx` two-pane layout
  - [ ] Left sidebar: story selector dropdown, `+ NEW THREAD`, recent threads list (title + preview + age)
  - [ ] Right pane: header w/ thread title + Rename / Export / Delete
  - [ ] Message stream
  - [ ] Composer with story + scene attachment chips + ASK button
- [ ] Message renderers: `UserMessage`, `AssistantMessage` (markdown), `ToolCallCard` (collapsible), `CitedSceneCard` (score, tension/pacing chips)
- [ ] `Export` → markdown download
- [ ] `Rename` → inline edit
- [ ] `Delete` → confirm modal
- [ ] **Backend**: confirm `POST /stories/{id}/chat/threads/{tid}/turn` SSE emits all event types (especially `cited_scenes`)
- [ ] **Backend**: `GET /stories/{id}/chat/threads/{tid}/export?format=md`
- [ ] **Verify**: Playwright — ask question → tokens stream → tool-call card → final answer w/ citations
- [ ] **Verify**: cancel mid-stream → request aborted, partial response visible with retry
- [ ] **Verify**: export downloads valid markdown

---

## Phase 5 — Analytics ("Book Pulse") — 4 lenses

> Largest backend lift. Extraction pipeline expands significantly.

### 5.A Extraction enrichment

- [ ] Extend `service/extraction` prompts + schemas to emit per scene:
  - [ ] `tension: LOW|MEDIUM|HIGH`
  - [ ] `pacing: SLOW|STEADY|FAST`
  - [ ] `characters: [name]`
  - [ ] `entities: [{name, kind: PLACE|FACTION|CONCEPT|THING}]`
  - [ ] `plot_threads: [{name, action: SETUP|TOUCH|RESOLVE}]`
- [ ] Migration: `plot_thread` (story_id, name, first_chapter_id, last_chapter_id, status, idle_chapters)
- [ ] Migration: `contradiction` (story_id, entity_name, kind, evidence_scene_ids[], state)
- [ ] Migration: `analytics_snapshot` (story_id, version, computed_at, payload JSONB)
- [ ] Materialized view / query for `entity_ledger`
- [ ] `service/analytics/recompute(story_id)` aggregating:
  - [ ] Character frequency + pairings
  - [ ] Tension + pacing curves
  - [ ] Thread timelines + idle counters
  - [ ] Act detection (heuristic: tension inflection or chapter thirds for v1)
  - [ ] Entity freshness (FRESH if touched last 5 ch, STALE if absent 8+)
- [ ] Contradiction LLM pass — flag entity claim conflicts → `contradiction` rows
- [ ] `worker.py`: `run_analytics_snapshot_job` cron + on-chapter-save background trigger

### 5.B Analytics API

- [ ] `GET /stories/{id}/analytics/snapshot` — meta + freshness
- [ ] `GET /stories/{id}/analytics/characters`
- [ ] `GET /stories/{id}/analytics/plot`
- [ ] `GET /stories/{id}/analytics/structure`
- [ ] `GET /stories/{id}/analytics/world`
- [ ] `POST /stories/{id}/analytics/contradictions/{cid}/dismiss`
- [ ] `POST /stories/{id}/analytics/contradictions/{cid}/intentional`
- [ ] `POST /stories/{id}/analytics/reset` (Danger Zone hook)

### 5.C Frontend

- [ ] `AnalyticsPage` shell with tabs (CHARACTERS / PLOT / STRUCTURE / WORLD), snapshot-freshness pill
- [ ] Per-tab hero opinion card with `ASK NEXUS →` deep-link
- [ ] **Characters tab**: ranked bar list (BY SCENES / BY WORDS / BY ARC toggle), pairings, density bars
- [ ] **Plot tab**: thread list + chapter timeline grid, open-threads sidebar, act-structure cards
- [ ] **Structure tab**: tension bar chart, scene-length distribution, chapter rhythm cards
- [ ] **World tab**: contradiction cards (ASK NEXUS / Mark intentional / Dismiss), entity ledger with filter pills + FRESH/STALE chips
- [ ] Hand-rolled SVG charts
- [ ] `useAnalyticsCharacters / Plot / Structure / World` hooks
- [ ] **Verify**: seeded 10-chapter story extracts + snapshots within 60s
- [ ] **Verify**: contradiction detector flags planted conflict
- [ ] **Verify**: Playwright — every tab renders, ASK NEXUS deep-links open chat with prefilled query

---

## Phase 6 — Settings + Stripe Billing + Notifications

### 6.A Preferences backend

- [ ] Migration: `user_preferences` table
  - [ ] Writing: `default_status`, `default_word_target`
  - [ ] Editor: `show_word_count`, `show_breadcrumb`, `show_prev_next`, `autocollapse_rail`
  - [ ] AI behavior: `inline_suggestions_enabled`, `kinds[]`, `sensitivity`, `agent_voice`
  - [ ] Notifications: channels + per-event toggles
  - [ ] Privacy: `model_improvement_opt_in`, `share_analytics`, `crash_reports`, `story_default_visibility`, `allow_search_indexing`
- [ ] `GET /me/preferences`, `PATCH /me/preferences`
- [ ] `PATCH /me` (display_name, email change w/ verification)

### 6.B Danger Zone

- [ ] `POST /me/analytics/reset?story_id=`
- [ ] `DELETE /me` with typed phrase server-side validated

### 6.C Billing (Stripe)

- [ ] Add `stripe` Python SDK
- [ ] Add `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID` env vars
- [ ] User columns: `stripe_customer_id`, `subscription_status`, `current_period_end`, `plan_id`
- [ ] `POST /billing/checkout-session` → returns hosted Stripe checkout URL
- [ ] `POST /billing/portal-session` → returns Customer Portal URL
- [ ] `POST /billing/webhook` → handle `customer.subscription.{created,updated,deleted}`, `invoice.payment_failed`
- [ ] Webhook signature verification

### 6.D Notifications

- [ ] Migration: `notification` (user_id, kind, payload JSONB, read_at, created_at)
- [ ] Event publisher in services: extraction_complete, contradiction_found, thread_idle_10ch, pacing_drift
- [ ] `GET /me/notifications`
- [ ] `POST /me/notifications/{id}/read`
- [ ] `POST /me/notifications/read-all`
- [ ] Email digest worker — daily cron via Resend
- [ ] HTML email templates in `src/infrastructure/email/templates/`
- [ ] Web Push toggle stored but inert (defer to v1.1)
- [ ] Frontend: 30s short-poll → toast on new notification

### 6.E Settings frontend

- [ ] `SettingsPage` shell with left rail tabs
- [ ] `ProfileTab` (identity + agent toggles)
- [ ] `WritingTab` (defaults + editor experience)
- [ ] `AIBehaviorTab` (edit suggestions + sensitivity + agent voice)
- [ ] `NotificationsTab` (channels + when-to-notify)
- [ ] `BillingTab` (plan + MANAGE → portal + cancel flow)
- [ ] `PrivacyTab` (promise + share toggles + story visibility)
- [ ] `DangerZoneTab` (reset analytics / delete story / delete account)
- [ ] `usePreferences()` + `useUpdatePreferences()` w/ optimistic updates
- [ ] Typed-phrase confirmation modal (`delete my account`, `reset analytics`)
- [ ] **Verify**: every preference round-trips through reload
- [ ] **Verify**: Stripe test mode → checkout → webhook flips `subscription_status` to active
- [ ] **Verify**: cancel via portal → webhook updates → Billing tab reflects in poll cycle
- [ ] **Verify**: notification event → in-app toast + email digest queued
- [ ] **Verify**: wrong delete phrase → 400; correct phrase → cascading wipe

---

## Phase 7 — Empty / Loading / Error pass

- [ ] Audit every screen against Figma E/L/E board
- [ ] **Empty states**
  - [ ] Dashboard shelf empty → "Begin new story"
  - [ ] No chapters → "Page one is waiting"
  - [ ] No search results
  - [ ] No chat thread → suggested prompts
- [ ] **Loading states**
  - [ ] Dashboard/library skeleton cards
  - [ ] "Reading what you just wrote" extraction progress card
  - [ ] Agent typing indicator in chat
  - [ ] Search skeleton rows
- [ ] **Error states**
  - [ ] Save-failed banner with retry (editor HUD turns red)
  - [ ] AI agent blocked (quota) with "Retry this turn" + "View error"
  - [ ] Query timeout
  - [ ] Network offline shell banner
- [ ] Backend: `GET /chapters/{id}/extraction-status` for progress card
- [ ] **Verify**: DevTools offline → banner appears
- [ ] **Verify**: mocked 500 on update → editor shows error HUD + retry restores
- [ ] **Verify**: new user sees Dashboard empty state with onboarding affordance

---

## Phase 8 — Tests (solid coverage)

- [ ] Backend test infra
  - [ ] `tests/` folder with `conftest.py`, `unit/`, `integration/`, `fixtures/`
  - [ ] testcontainers-postgres fixture (or compose-spawned ephemeral DB)
  - [ ] Mocked AI provider fixture
- [ ] Backend service tests: auth, story, chapter, scene search, chat agent, extraction, analytics aggregation, billing webhook signature, preferences round-trip, notification publish→read
- [ ] Backend integration tests via TestClient — every router responds
- [ ] Backend coverage gate ≥ 70% lines
- [ ] Frontend Vitest
  - [ ] `vitest.config.ts`
  - [ ] MSW for fetch mocking
  - [ ] Data hooks
  - [ ] Primitive components
  - [ ] SSE parser
- [ ] Frontend Playwright
  - [ ] `playwright.config.ts`
  - [ ] E2E flow: signup → create story → create chapter → type → see suggestion → accept → search scene → ask chat (mocked AI) → view analytics → toggle setting → logout
- [ ] Frontend coverage gate ≥ 60% lines
- [ ] Lint gates: `ruff check && ruff format --check`, `eslint --max-warnings 0`
- [ ] **Verify**: `make test` green
- [ ] **Verify**: `pnpm test` + `pnpm e2e` green against compose stack

---

## Phase 9 — CI/CD + Deployment to Render

- [ ] Confirm pgvector support on Render managed Postgres (fallback: Neon)
- [ ] Choose frontend delivery: Render **Static Site** (recommended) vs frontend Dockerfile + nginx
- [ ] `render.yaml`
  - [ ] `web` service (existing Dockerfile, `uvicorn main:app`, healthcheck `/health`)
  - [ ] `worker` service (same image, `python worker.py`)
  - [ ] `db` (managed Postgres + pgvector)
  - [ ] `web-frontend` (static site)
- [ ] Env groups for all secrets
  - [ ] `DATABASE_URL` (auto-injected)
  - [ ] `JWT_SECRET`, `SESSION_SECRET`
  - [ ] `OPENAI_API_KEY`
  - [ ] `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID`
  - [ ] `RESEND_API_KEY`
  - [ ] `SENTRY_DSN_BACKEND`, `SENTRY_DSN_FRONTEND`
  - [ ] `CORS_ORIGINS`, `PUBLIC_API_URL`
- [ ] Pre-deploy command runs `yoyo apply --batch ... ./migrations/yoyo`
- [ ] GitHub Actions
  - [ ] `.github/workflows/ci.yml` — backend + frontend matrix; lint, test, build; on PR + main
  - [ ] `.github/workflows/deploy.yml` — trigger Render deploy hooks on main after CI green
- [ ] Sentry
  - [ ] `sentry-sdk[fastapi]` in `src/app/lifespan.py`
  - [ ] `@sentry/react` in `frontend/src/main.tsx`
  - [ ] Gated by env DSN + Privacy preference
- [ ] Stripe webhook URL configured in Stripe dashboard
- [ ] Custom domains + auto-TLS (`api.{domain}`, `{domain}`)
- [ ] `slowapi` rate limits on auth, chat-turn, suggestion endpoints
- [ ] CORS lockdown to production frontend domain
- [ ] Structured JSON logs to stdout for Render log capture
- [ ] Render Postgres daily snapshots enabled
- [ ] Uptime monitor (BetterStack / UptimeRobot) pinging `/health` every minute
- [ ] README cleanup
  - [ ] Drop MongoDB references
  - [ ] Drop Socket.IO references
  - [ ] Add Deploy section
  - [ ] Add env var table
- [ ] **Verify**: push to `main` → CI green → deploy hooks fire → all services healthy
- [ ] **Verify**: prod smoke — sign up, create story, add chapter, run chat, complete Stripe test purchase → webhook updates DB
- [ ] **Verify**: force backend exception → Sentry receives event
- [ ] **Verify**: 10 rapid logins from same IP → slowapi rejects

---

## Further considerations

- [ ] pgvector confirmed on managed PG before Phase 9 (fallback: Neon)
- [ ] Per-user monthly AI token cap on paid tier (no enforcement on free)
- [ ] Long-running analytics on 47-chapter books surfaced via loading card + notification

---

## Excluded from v1 (track for v1.1)

- [ ] Multi-user collaboration / sharing
- [ ] Full responsive / mobile layouts
- [ ] Public story pages + SEO surface
- [ ] i18n / translation
- [ ] AI fine-tuning on user prose
- [ ] Native mobile apps
- [ ] Audio narration / TTS
- [ ] Web Push notifications (toggle exists but inert)
- [ ] Avatar upload (initials only in v1)
- [ ] Real-time SSE notifications (poll in v1)
