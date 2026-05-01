# User Stories: FairShare — Splitwise-style Expense Splitting

Stories are ordered by dependency. Each one produces a concrete, testable output that the next story builds on.

**Rules:**
- No work begins on a story until every item in "Blocked until answered" is answered and recorded in this file.
- One commit per story.
- Each story must pass **both** its unit tests and QA verification before moving to the next.
- **Unit tests** cover isolated logic with mocked dependencies.
- **QA tests** are real runs of the system (browser interactions, live API round-trips) that prove the feature works end-to-end.

**Dependency chain:**
```
Story 0: Decisions (no code)
  → Story 1: Project scaffolding (server + web)
    → Story 2: Auth — register + login + JWT
      → Story 3: Groups — create, list, add members, default splits
        → Story 4: Expenses — record expenses with custom or default splits
          → Story 5: Balances — net balances + graph minimisation algorithm
            → Story 6: Settle up — record manual payments
              → Story 7: Dashboard — overview of balances across groups
                → Story 8: Cloud deployment (Fly.io)
```

---

## Story 0 — Decide the operating model

As a **project lead**, I want **clear decisions on tools, stack, and constraints documented up front**, so that **no story is blocked by an unanswered question once coding starts**.

### Acceptance criteria
- [x] The following decisions are recorded in this file (below):
  - Python version and dependency management.
  - React tooling (bundler, package manager).
  - Database choice.
  - Auth approach (JWT, sessions, etc.).
  - Deployment target.
  - CSS framework and UI component library.
- [x] A `.env.example` file documents every required environment variable.

### Unit tests
- None (no code in this story).

### QA verification
- Read through the recorded answers below. If any are blank, the story is not done.

### Blocked until answered
1. Python dependency manager: pip, poetry, or uv?
2. Database: PostgreSQL or SQLite for v1?
3. Auth approach: JWT or session-based?
4. Deployment target: Fly.io, Railway, or Vercel?
5. CSS framework: Tailwind v4?

**Recorded answers:**
- Python tooling: uv for dependency management. Python 3.12+.
- React tooling: Vite + npm. React 19 + TypeScript.
- Database: SQLite for v1 (matches callme pattern — portable, no infra needed).
- Auth: JWT (HS256, 7-day expiry) + bcrypt password hashing. Same pattern as callme.
- Deployment: Fly.io with nginx + supervisord (same single-container pattern as callme).
- CSS: Tailwind CSS v4 + shadcn/ui components + lucide-react icons.
- UI library: radix-ui primitives, class-variance-authority, clsx, tailwind-merge.

---

## Story 1 — Project scaffolding

As a **developer**, I want **a working project skeleton with linting, testing, and dev scripts configured**, so that **every subsequent story starts from a runnable baseline**.

### Acceptance criteria
- [x] `server/` directory exists with:
  - `pyproject.toml` listing core dependencies: `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `sqlmodel`, `bcrypt`, `PyJWT`, `structlog`, `email-validator`.
  - `app/main.py` — a FastAPI app with a health-check endpoint (`GET /health` → `{"status": "ok"}`).
  - `app/config.py` — reads env vars via `pydantic-settings` (`BaseSettings`).
  - `app/db/session.py` — SQLite engine setup with `init_db()` and `get_session()`.
  - `app/db/models.py` — empty models file (tables added in later stories).
  - `app/logging.py` — structlog configuration with JSON output.
  - `tests/` directory with a passing smoke test for the health endpoint.
- [x] `web/` directory exists with:
  - Vite + React 19 + TypeScript + Tailwind CSS v4 scaffolded.
  - shadcn/ui base components: Button, Input, Label.
  - A placeholder `App.tsx` that renders "FairShare".
  - Dev server starts with `npm run dev` and proxies `/api` to `localhost:3000`.
- [x] `.env.example` at repo root lists all anticipated env vars.
- [x] `.gitignore` covers Python and Node artifacts.
- [x] `Makefile` with `dev`, `test`, `test-server`, `test-web`, `deploy` targets.
- [x] `README.md` with setup instructions for both `server/` and `web/`.
- [x] Deployment configs: `Dockerfile.fly`, `fly.toml`, `fly/nginx.conf`, `fly/supervisord.conf`.

### Unit tests
- `pytest server/tests/` passes — health endpoint returns 200 with `{"status": "ok"}`.
- `cd web && npm run build` succeeds without errors.

### QA verification
1. Start the server → `curl localhost:3000/health` returns `{"status": "ok"}`.
2. Start the web dev server → browser shows the placeholder page at `localhost:5173`.

### Blocked until answered
- None (depends only on Story 0 answers).

### Completion
- Server tests: 1 passed
- Web build: succeeds without errors
- QA: `curl localhost:3000/health` → `{"status": "ok"}` — PASS
- QA: Web placeholder renders "FairShare" — PASS

---

## Story 2 — Authentication (register + login)

As a **user**, I want **to create an account and log in**, so that **my expenses are tied to my identity and I can be added to groups**.

### Acceptance criteria
- [ ] Database models:
  - `User` table with fields: `id` (UUID), `email` (unique, indexed), `password_hash`, `name`, `is_admin`, `created_at`.
- [ ] API endpoints:
  - `POST /api/auth/register` — accepts `{email, password, name}`, returns `{ok, token, user}`. Validates email format and password length (≥6 chars). Returns 409 if email already taken.
  - `POST /api/auth/login` — accepts `{email, password}`, returns `{ok, token, user}`. Returns 401 on bad credentials.
  - `GET /api/auth/me` — returns the current user (requires Bearer token). Returns 401 if not authenticated.
- [ ] JWT tokens: HS256, 7-day expiry, payload contains `sub` (user_id), `email`, `name`.
- [ ] Admin user auto-created on startup from `FAIRSHARE_SECRET_KEY` env var.
- [ ] Web pages:
  - `/login` — email + password form, error display, link to register.
  - `/register` — email + password + name form, error display, link to login.
  - `AuthGuard` component wrapping protected routes — redirects to `/login` if no valid token.
  - Token stored in `localStorage`, cleared on 401 responses.
- [ ] After successful login/register, user is redirected to `/` (dashboard).

### Unit tests
- Register: creates user, returns JWT, rejects duplicate email, rejects short password.
- Login: returns JWT for valid credentials, rejects invalid email, rejects wrong password.
- Me: returns user info for valid token, returns 401 for missing/invalid token.
- Password hashing: bcrypt round-trip works correctly.

### QA verification
1. Open `/register` in browser → fill form → submit → redirected to dashboard.
2. Log out → open `/login` → log in with same credentials → redirected to dashboard.
3. Try to visit `/` without token → redirected to `/login`.
4. Register with duplicate email → see error message.
5. `curl POST /api/auth/register` with valid data → 200 with token.
6. `curl POST /api/auth/login` with wrong password → 401.

### Blocked until answered
- None.

---

## Story 3 — Groups (create, list, members, default splits)

As a **user**, I want **to create expense groups and add other registered users**, so that **I can track shared expenses with specific people**.

### Acceptance criteria
- [ ] Database models:
  - `Group` table: `id` (UUID), `name`, `created_by` (FK→users), `created_at`.
  - `GroupMember` table: `id` (UUID), `group_id` (FK→groups), `user_id` (FK→users), `default_split_percent`, `joined_at`.
- [ ] API endpoints:
  - `GET /api/groups` — list groups the current user belongs to. Returns `[{id, name, member_count, created_at}]`.
  - `POST /api/groups` — create group with `{name, member_emails[]}`. Creator auto-added. Default splits set to equal (100% / N members). Unknown emails are silently skipped (user must register first).
  - `GET /api/groups/:id` — group detail with full member list and split percentages. Returns 403 if not a member.
  - `POST /api/groups/:id/members` — add member by email. Recalculates equal splits for all members. Returns 404 if email not found, 409 if already a member.
  - `PUT /api/groups/:id/splits` — update default split percentages. Validates they sum to 100%.
- [ ] API endpoint for user search:
  - `GET /api/users/search?q=...` — search users by email or name prefix (for adding to groups).
- [ ] Web pages:
  - `/groups` — list of groups with member count and "Create Group" button.
  - `/groups/new` — form to create a group (name + add members by email search).
  - `/groups/:id` — group detail page showing members, their split percentages, and an "Add Member" button.
  - Ability to edit default split percentages from the group detail page.

### Unit tests
- Create group: sets equal splits, creator is auto-added.
- Add member: recalculates splits, rejects non-existent email, rejects duplicate.
- Update splits: validates sum = 100%, updates all member percentages.
- List groups: only returns groups the user is a member of.
- Get group: returns 403 for non-members.

### QA verification
1. Log in → navigate to `/groups` → see empty list.
2. Click "Create Group" → enter name "Trip to Paris" → create → redirected to group detail.
3. See yourself as the only member with 100% split.
4. Register a second user in another browser/incognito tab.
5. Add the second user by email → both members now at 50% split.
6. Edit splits to 60/40 → save → splits update correctly.
7. `curl GET /api/groups` with auth → returns the group in the list.

### Blocked until answered
- None.

---

## Story 4 — Expenses (record with custom or default splits)

As a **user**, I want **to record an expense and specify how it's split**, so that **the group knows who paid for what and who owes whom**.

### Acceptance criteria
- [ ] Database models:
  - `Expense` table: `id` (UUID), `group_id` (FK→groups), `description`, `amount`, `paid_by` (FK→users), `created_by` (FK→users), `created_at`.
  - `ExpenseSplit` table: `id` (UUID), `expense_id` (FK→expenses), `user_id` (FK→users), `amount`.
- [ ] API endpoints:
  - `GET /api/groups/:id/expenses` — list expenses for a group (newest first). Each expense includes split details with user names.
  - `POST /api/groups/:id/expenses` — create expense with `{description, amount, paid_by, splits?}`. If `splits` is omitted, uses the group's default split percentages. If provided, validates split amounts sum to the expense amount (within ±0.01 tolerance).
- [ ] Web:
  - Expense list on the group detail page showing description, amount, payer, and date.
  - "Add Expense" form: description, amount, who paid (dropdown of group members), split method (equal using defaults, or custom per-person amounts).
  - Custom split UI: shows each member with an amount input, live total validation.

### Unit tests
- Create expense with default splits: amounts calculated from group percentages.
- Create expense with custom splits: stored as provided, validates sum.
- Create expense rejects: zero/negative amount, empty description, non-member payer, splits that don't sum correctly.
- List expenses: returns newest first, includes split details.

### QA verification
1. Open group "Trip to Paris" → add expense "Hotel" for £450 paid by Alice with default split.
2. See the expense in the list with correct split amounts (e.g. 50/50 for 2 members = £225 each).
3. Add another expense "Dinner" for £120 paid by Bob with custom split (£80 Alice, £40 Bob).
4. See both expenses in the list ordered by date.
5. `curl POST /api/groups/:id/expenses` with splits that don't sum → 400 error.

### Blocked until answered
- None.

---

## Story 5 — Balances & graph minimisation algorithm

As a **user**, I want **to see how much I owe or am owed, with the minimum number of transfers needed to settle up**, so that **settling debts is simple and efficient**.

### Acceptance criteria
- [ ] Backend algorithm (`app/api/balances.py`):
  - Computes net balance per member: sum of (expenses they paid) minus sum of (their share of all expenses) plus/minus payments.
  - Positive balance = owed money by others. Negative balance = owes money to others.
  - **Graph minimisation**: given N members with various net balances, compute the minimum set of transfers to settle all debts. Uses greedy algorithm: repeatedly match largest debtor with largest creditor.
  - Payments (from Story 6) are factored into net balance calculation.
- [ ] API endpoint:
  - `GET /api/groups/:id/balances` — returns `{balances: [{user_id, name, email, balance}], simplified_debts: [{from_user_id, from_name, to_user_id, to_name, amount}]}`.
- [ ] Web:
  - "Balances" tab/section on the group detail page.
  - Shows each member's net balance (green if positive/owed, red if negative/owes).
  - Shows the simplified debts list: "Alice owes Bob £30", "Charlie owes Bob £15".
  - Visual indicator (colour-coded amounts).

### Unit tests
- Net balance calculation with expenses only: payer is owed, others owe.
- Net balance with payments factored in: payments reduce outstanding balances.
- Graph minimisation:
  - 2 people: single transfer.
  - 3 people with chain debt: minimised to fewer transfers (e.g. A→B→C becomes A→C + A→B or similar optimal).
  - All settled (all balances near zero): no transfers needed.
  - Unequal amounts: correct rounding to 2 decimal places.
- Edge cases: single member group (no debts), zero-amount expenses.

### QA verification
1. In the "Trip to Paris" group with 2 expenses (Hotel £450 by Alice, Dinner £120 by Bob):
   - Alice paid £450, owes £225+£60 = £285 → net +£165.
   - Bob paid £120, owes £225+£60 = £285 → net -£165.
   - Simplified: "Bob owes Alice £165".
2. Add a third member Charlie and more expenses → verify minimisation reduces transfer count.
3. `curl GET /api/groups/:id/balances` → response matches expected calculation.
4. Verify the balances section renders correctly in the browser.

### Blocked until answered
- None.

---

## Story 6 — Settle up (manual payments)

As a **user**, I want **to record a payment I've made to another group member**, so that **the balances update and I can track who has settled their debts**.

### Acceptance criteria
- [ ] Database model:
  - `Payment` table: `id` (UUID), `group_id` (FK→groups), `from_user_id` (FK→users), `to_user_id` (FK→users), `amount`, `note` (optional), `created_at`.
- [ ] API endpoints:
  - `POST /api/groups/:id/payments` — record payment `{to_user_id, amount, note?}`. `from_user_id` is the authenticated user. Validates: positive amount, both users are group members, can't pay yourself.
  - `GET /api/groups/:id/payments` — list all payments in the group (newest first).
- [ ] Web:
  - "Settle Up" button on the group detail page.
  - Settle up form: select who you're paying (dropdown), amount (pre-filled from simplified debts if applicable), optional note.
  - Payment history section on the group page.
  - After recording a payment, balances and simplified debts update automatically.

### Unit tests
- Create payment: stored correctly, updates balances.
- Create payment rejects: zero/negative amount, non-member recipient, self-payment.
- List payments: returns newest first.
- Balance calculation with payments: a £50 payment from A to B reduces A's debt to B by £50.

### QA verification
1. View balances showing "Bob owes Alice £165".
2. Log in as Bob → click "Settle Up" → pay Alice £100 with note "Bank transfer".
3. Balances update: "Bob owes Alice £65".
4. Payment appears in payment history.
5. Bob pays Alice remaining £65 → all balances show £0, no simplified debts.
6. `curl POST /api/groups/:id/payments` for self-payment → 400 error.

### Blocked until answered
- None.

---

## Story 7 — Dashboard

As a **user**, I want **a dashboard showing my overall financial position across all groups**, so that **I can quickly see what I owe and what I'm owed at a glance**.

### Acceptance criteria
- [ ] Web:
  - `/` (home/dashboard) shows:
    - Total amount you owe across all groups.
    - Total amount owed to you across all groups.
    - Net position (positive = others owe you, negative = you owe others).
    - List of groups with your balance in each.
    - Quick links to each group.
  - App shell with navigation sidebar/header: Dashboard, Groups, profile/logout.
- [ ] Responsive layout that works on mobile.

### Unit tests
- None (frontend-only story, covered by QA).

### QA verification
1. Log in → dashboard shows summary of balances across all groups.
2. Navigate to a group from the dashboard → back to dashboard.
3. Log out → redirected to login.
4. Verify layout on mobile viewport (375px wide).

### Blocked until answered
- None.

---

## Story 8 — Cloud deployment (Fly.io)

As a **project owner**, I want **the app deployed and publicly accessible**, so that **users can access it without running anything locally**.

### Acceptance criteria
- [ ] `Dockerfile.fly` — multi-stage build: Stage 1 builds web static files, Stage 2 runs server + nginx.
- [ ] `fly.toml` — configured for `lhr` region, 1GB persistent volume for SQLite, health checks.
- [ ] `fly/nginx.conf` — serves static files, proxies `/api/` and `/health` to uvicorn.
- [ ] `fly/supervisord.conf` — runs uvicorn + nginx.
- [ ] `scripts/fly-setup.sh` — first-time Fly.io setup (create app, volume, set secrets, deploy).
- [ ] Makefile target: `make deploy` → `fly deploy --ha=false`.
- [ ] App is accessible at `https://<app-name>.fly.dev` with working login, groups, expenses, balances, and payments.
- [ ] Seed demo data on first boot (`SEED_DEMO=true`) for easy QA.

### Unit tests
- None (deployment story).

### QA verification
1. Run `make deploy` or `fly deploy --ha=false`.
2. Open `https://<app-name>.fly.dev` → see login page.
3. Register an account → create a group → add expense → view balances → settle up.
4. `curl https://<app-name>.fly.dev/health` → `{"status": "ok"}`.

### Blocked until answered
1. Fly.io account authenticated? `fly auth login` done?
2. App name chosen? (e.g. `fairshare-app`)

**Recorded answers:**
- (to be filled during implementation)
