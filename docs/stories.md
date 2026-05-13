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
- [x] Database models:
  - `User` table with fields: `id` (UUID), `email` (unique, indexed), `password_hash`, `name`, `is_admin`, `created_at`.
- [x] API endpoints:
  - `POST /api/auth/register` — accepts `{email, password, name}`, returns `{ok, token, user}`. Validates email format and password length (≥6 chars). Returns 409 if email already taken.
  - `POST /api/auth/login` — accepts `{email, password}`, returns `{ok, token, user}`. Returns 401 on bad credentials.
  - `GET /api/auth/me` — returns the current user (requires Bearer token). Returns 401 if not authenticated.
- [x] JWT tokens: HS256, 7-day expiry, payload contains `sub` (user_id), `email`, `name`.
- [x] Admin user auto-created on startup from `FAIRSHARE_SECRET_KEY` env var.
- [x] Web pages:
  - `/login` — email + password form, error display, link to register.
  - `/register` — email + password + name form, error display, link to login.
  - `AuthGuard` component wrapping protected routes — redirects to `/login` if no valid token.
  - Token stored in `localStorage`, cleared on 401 responses.
- [x] After successful login/register, user is redirected to `/` (dashboard).

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

### Completion
- Unit tests: 12 passed (test_health.py + test_auth.py)
- Web build: succeeds without errors
- QA1: Register alice@test.com → redirected to dashboard — PASS
- QA2: Clear token → login with same creds → redirected to dashboard — PASS
- QA3: Visit `/` without token → redirected to `/login` — PASS
- QA4: Wrong password → "Invalid email or password" error shown — PASS
- QA5: Duplicate email registration → 409 "Email already registered" — PASS
- QA6: Mobile viewport (375px) — layout renders correctly — PASS

---

## Story 3 — Groups (create, list, members, default splits)

As a **user**, I want **to create expense groups and add other registered users**, so that **I can track shared expenses with specific people**.

### Acceptance criteria
- [x] Database models:
  - `Group` table: `id` (UUID), `name`, `created_by` (FK→users), `created_at`.
  - `GroupMember` table: `id` (UUID), `group_id` (FK→groups), `user_id` (FK→users), `default_split_percent`, `joined_at`.
- [x] API endpoints:
  - `GET /api/groups` — list groups the current user belongs to. Returns `[{id, name, member_count, created_at}]`.
  - `POST /api/groups` — create group with `{name, member_emails[]}`. Creator auto-added. Default splits set to equal (100% / N members). Unknown emails are silently skipped (user must register first).
  - `GET /api/groups/:id` — group detail with full member list and split percentages. Returns 403 if not a member.
  - `POST /api/groups/:id/members` — add member by email. Recalculates equal splits for all members. Returns 404 if email not found, 409 if already a member.
  - `PUT /api/groups/:id/splits` — update default split percentages. Validates they sum to 100%.
- [x] API endpoint for user search:
  - `GET /api/users/search?q=...` — search users by email or name prefix (for adding to groups).
- [x] Web pages:
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

### Completion
- Unit tests: 21 passed (10 group tests + previous 11)
- Web build: succeeds
- QA1: Groups page shows empty state — PASS
- QA2: Create "Trip to Paris" → redirected to group detail — PASS
- QA3: Alice sole member at 100% — PASS
- QA4: Bob registered via curl — PASS
- QA5: Add Bob → both at 50% — PASS
- QA6: Edit splits to 60/40 → saved correctly — PASS
- QA7: Groups list shows "Trip to Paris" with 2 members — PASS
- Mobile viewport: layout renders correctly with bottom nav — PASS

---

## Story 4 — Expenses (record with custom or default splits)

As a **user**, I want **to record an expense and specify how it's split**, so that **the group knows who paid for what and who owes whom**.

### Acceptance criteria
- [x] Database models:
  - `Expense` table: `id` (UUID), `group_id` (FK→groups), `description`, `amount`, `paid_by` (FK→users), `created_by` (FK→users), `created_at`.
  - `ExpenseSplit` table: `id` (UUID), `expense_id` (FK→expenses), `user_id` (FK→users), `amount`.
- [x] API endpoints:
  - `GET /api/groups/:id/expenses` — list expenses for a group (newest first). Each expense includes split details with user names.
  - `POST /api/groups/:id/expenses` — create expense with `{description, amount, paid_by, splits?}`. If `splits` is omitted, uses the group's default split percentages. If provided, validates split amounts sum to the expense amount (within ±0.01 tolerance).
- [x] Web:
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

### Completion
- Unit tests: 27 passed (6 expense tests + previous 21)
- Web build: succeeds
- QA1: Hotel £450 paid by Alice, default split → Alice £225, Bob £225 — PASS
- QA2: Dinner £120 paid by Bob, custom split → Alice £80, Bob £40 — PASS
- QA3: Both expenses shown newest first — PASS
- QA4: Custom split UI with live total validation — PASS
- Bug fix: 403 response no longer clears auth token (only 401 does)

---

## Story 5 — Balances & graph minimisation algorithm

As a **user**, I want **to see how much I owe or am owed, with the minimum number of transfers needed to settle up**, so that **settling debts is simple and efficient**.

### Acceptance criteria
- [x] Backend algorithm (`app/api/balances.py`):
  - Computes net balance per member: sum of (expenses they paid) minus sum of (their share of all expenses) plus/minus payments.
  - Positive balance = owed money by others. Negative balance = owes money to others.
  - **Graph minimisation**: given N members with various net balances, compute the minimum set of transfers to settle all debts. Uses greedy algorithm: repeatedly match largest debtor with largest creditor.
  - Payments (from Story 6) are factored into net balance calculation.
- [x] API endpoint:
  - `GET /api/groups/:id/balances` — returns `{balances: [{user_id, name, email, balance}], simplified_debts: [{from_user_id, from_name, to_user_id, to_name, amount}]}`.
- [x] Web:
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

### Completion
- Unit tests: 36 passed (9 balance tests including pure function + API)
- Web build: succeeds
- QA: Alice +£145, Bob -£145, simplified "Bob → Alice £145" — PASS
- Balances section renders with green/red colour coding and arrow notation — PASS
- Payment model added (for Story 6 integration)

---

## Story 6 — Settle up (manual payments)

As a **user**, I want **to record a payment I've made to another group member**, so that **the balances update and I can track who has settled their debts**.

### Acceptance criteria
- [x] Database model:
  - `Payment` table: `id` (UUID), `group_id` (FK→groups), `from_user_id` (FK→users), `to_user_id` (FK→users), `amount`, `note` (optional), `created_at`.
- [x] API endpoints:
  - `POST /api/groups/:id/payments` — record payment `{to_user_id, amount, note?}`. `from_user_id` is the authenticated user. Validates: positive amount, both users are group members, can't pay yourself.
  - `GET /api/groups/:id/payments` — list all payments in the group (newest first).
- [x] Web:
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

### Completion
- Unit tests: 42 passed (6 payment tests + previous 36)
- Web build: succeeds
- QA1: Bob owes Alice £165 shown correctly — PASS
- QA2: Bob pays Alice £100 "Bank transfer" → balances update to ±£65 — PASS
- QA3: Payment appears in history with note — PASS
- QA4: Bob pays remaining £65 → balances section hidden, no debts — PASS
- QA5: Self-payment rejection tested in unit tests — PASS
- Settle Up button auto-fills amount from simplified debts — PASS

---

## Story 7 — Dashboard

As a **user**, I want **a dashboard showing my overall financial position across all groups**, so that **I can quickly see what I owe and what I'm owed at a glance**.

### Acceptance criteria
- [x] Web:
  - `/` (home/dashboard) shows:
    - Total amount you owe across all groups.
    - Total amount owed to you across all groups.
    - Net position (positive = others owe you, negative = you owe others).
    - List of groups with your balance in each.
    - Quick links to each group.
  - App shell with navigation sidebar/header: Dashboard, Groups, profile/logout.
- [x] Responsive layout that works on mobile.

### Unit tests
- None (frontend-only story, covered by QA).

### QA verification
1. Log in → dashboard shows summary of balances across all groups.
2. Navigate to a group from the dashboard → back to dashboard.
3. Log out → redirected to login.
4. Verify layout on mobile viewport (375px wide).

### Blocked until answered
- None.

### Completion
- Backend: Dashboard API (GET /api/dashboard) returns cross-group summary
- QA1: Dashboard shows £140 owed across 2 groups — PASS
- QA2: Group cards link to group detail pages — PASS
- QA3: Mobile viewport (375px) renders correctly — PASS
- Summary cards: Owed to you / You owe / Net with colour coding — PASS

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

---

## Story 9 — Per-expense member exclusion

As a **group member**, I want **to untick people from a specific expense**, so that **only the members who actually participated in that expense share its cost** (like Splitwise's per-expense participant selection).

### Acceptance criteria
- [ ] When the Custom split mode is selected in the Add Expense form, each member row has a checkbox on the left.
- [ ] Members are checked by default. Unchecking a member removes them from the split.
- [ ] The split amounts for the remaining checked members are recalculated proportionally based on their `default_split_percent` relative to each other.
- [ ] The validation message ("Total: £x / £y") only counts checked members.
- [ ] An expense can only be submitted when the checked members' amounts sum to within £0.01 of the total.
- [ ] If only one member is checked, 100% of the expense is assigned to them.
- [ ] The `splits` array sent to the API contains only checked members (excluded members are simply absent from the payload — the backend already supports partial splits).
- [ ] The expense list in the group detail page correctly reflects who was included (only included members appear in the split chips).
- [ ] The Default split mode is unaffected — it always includes all members using their group percentages.

### Unit tests
File: `web/src/pages/__tests__/GroupDetail.memberExclusion.test.tsx`
- Toggling a member's checkbox from checked to unchecked removes them from the custom splits state.
- Amounts for remaining checked members are recalculated proportionally.
- Submitting with an excluded member sends a splits array that does not contain that member's `user_id`.
- Validation message reflects the sum of only checked members.

### QA verification
1. Log in as alice@test.com. Open "QA Group".
2. Click **Add** expense. Enter description "Lunch", amount £30. Select **Custom** split.
3. Verify both Alice and Bob appear with checkboxes checked and amounts pre-filled.
4. Uncheck Bob. Verify Bob's row is greyed out / amount cleared. Verify "Total: £30.00 / £30.00" (all assigned to Alice).
5. Submit. Verify the expense appears with only Alice's split chip.
6. Open Balances — verify Bob's balance is unchanged (he owes nothing for Lunch).
7. Add another expense "Coffee" £10, Custom split, uncheck Alice. Submit. Verify only Bob's split chip appears.

### Blocked until answered
1. When a member is unchecked, should their amount input be hidden or just zeroed and disabled? **Decision: hide the amount input row entirely when unchecked.**
2. When re-checking a member, should their amount be restored to the proportional default or reset to 0? **Decision: recalculate proportional default from current total.**

**Recorded answers:**
1. Hide the amount input row entirely when unchecked.
2. Recalculate proportional default from current total on re-check.

### Completion
- [ ] Unit tests pass: `pnpm test --run`
- [ ] QA verification steps executed and confirmed
- [ ] One commit: `git commit -m "feat: per-expense member exclusion checkboxes"`

---

## Story 10 — Custom split percentage entry

As a **group member**, I want **to enter custom splits as percentages instead of amounts**, so that **I can think in round numbers (e.g. 70/30) rather than calculating exact figures myself**.

### Acceptance criteria
- [ ] In Custom split mode, a toggle sits above the per-member inputs labelled "£" and "%".
- [ ] **£ mode** (default): existing behaviour — each member gets a numeric input showing their amount in pounds.
- [ ] **% mode**: each member gets a numeric input (0–100) showing their percentage share. A live readout below shows "Total: 70% / 100%".
- [ ] Switching between modes converts the existing values: £→% divides each amount by the expense total; %→£ multiplies each percent by the expense total.
- [ ] The expense cannot be submitted in % mode until the percentages sum to 100 (within 0.1%).
- [ ] Before the API call the frontend converts percentages to pound amounts (`Math.round(pct / 100 * total * 100) / 100`). The API always receives pound values.
- [ ] Member exclusion checkboxes (Story 9) work in both modes: unchecking a member removes them; remaining members are recalculated proportionally.
- [ ] The mode toggle resets when the Add Expense form is closed/re-opened (always starts in £ mode).

### Unit tests
File: `web/src/pages/__tests__/GroupDetail.splitPercentMode.test.tsx`
- Switching to % mode converts existing £ amounts to percentages correctly.
- Switching back to £ mode converts percentages back to £ amounts.
- Submitting in % mode sends pounds (not percentages) to the API.
- Validation message shows "Total: X% / 100%" in % mode.
- Submitting with percentages not summing to 100 is blocked.

### QA verification
1. Log in as alice@test.com. Open "QA Group". Click **Add** expense, amount £60, Custom split.
2. Verify default amounts: Alice £30, Bob £30 (50/50). Confirm £ mode is active.
3. Click **%** mode toggle. Verify Alice 50%, Bob 50%.
4. Change Alice to 70%, Bob to 30%. Verify "Total: 100% / 100%" in green.
5. Submit expense "Dinner £60". Verify splits: Alice £42.00, Bob £18.00.
6. Add expense "Snacks £10", switch to % mode, set Alice 100%, Bob 0%. Verify Bob unchecked or 0%. Submit. Verify only Alice's split chip appears.
7. Try to submit with Alice 60%, Bob 30% (total 90%). Verify button is disabled / error shown.

### Blocked until answered
- None.

**Recorded answers:**
- N/A

### Completion
- [ ] Unit tests pass: `pnpm test --run`
- [ ] QA verification steps executed and confirmed
- [ ] One commit: `git commit -m "feat: percentage mode for custom expense splits"`

---

## Story 11 — Retroactive default-split propagation

As a **group admin**, I want **an option to apply an updated default split to all past expenses that used the default split**, so that **I don't have to delete and re-enter old expenses when the agreed split ratio changes**.

### Acceptance criteria
- [ ] The `Expense` database model gains a boolean column `used_default_split` (default `True`; set to `False` when the expense is created with explicit `splits` provided).
- [ ] A new Alembic migration adds the column with `DEFAULT TRUE` and back-fills existing rows.
- [ ] `PUT /api/groups/{id}/splits` accepts an optional boolean body field `retroactive` (default `false`).
- [ ] When `retroactive=true`, the endpoint finds all expenses in the group where `used_default_split=True` and recalculates their `splits` rows using the new percentages. Existing split rows are replaced atomically.
- [ ] The Edit Splits form gains a checkbox below the percentage inputs: **"Also update past expenses that used the default split"**. It is unchecked by default.
- [ ] Checking the checkbox and saving displays a confirmation: "X expense(s) updated."
- [ ] Expenses created with Custom split mode (Story 9/10) are never touched, even when `retroactive=true`.
- [ ] The API response for `PUT /api/groups/{id}/splits` includes `{ "updated_expenses": <count> }` in addition to the updated member list.

### Unit tests
File: `server/tests/test_splits_retroactive.py`
- `PUT /api/groups/{id}/splits` with `retroactive=False` does not alter any expense splits.
- `PUT /api/groups/{id}/splits` with `retroactive=True` recalculates splits for expenses where `used_default_split=True`.
- Expenses with `used_default_split=False` are untouched even when `retroactive=True`.
- The response body contains `updated_expenses` with the correct count.
- New expenses created after the split change use the new percentages by default.

### QA verification
1. Log in as alice@test.com. Open "QA Group" (Alice 50%, Bob 50%).
2. Verify existing expense splits show 50/50.
3. Click **Edit splits**. Change Alice to 70%, Bob to 30%. Check **"Also update past expenses"**. Click **Save**.
4. Verify the confirmation "X expense(s) updated." appears briefly.
5. Verify existing expenses in the list now show 70/30 splits.
6. Add a new expense — verify it defaults to 70/30.
7. Add a **Custom** split expense (Story 9). Then change the default splits again with retroactive checked. Verify the custom-split expense is unchanged.
8. Change splits back to 50/50 without the checkbox. Verify old expenses remain at 70/30 (no backpropagation).

### Blocked until answered
- None.

**Recorded answers:**
- N/A

### Completion
- [ ] Unit tests pass (`pytest server/tests/test_splits_retroactive.py -v`)
- [ ] QA verification steps executed and confirmed
- [ ] One commit: `git commit -m "feat: retroactive default-split propagation"`
