# tests-legacy

These tests were written against fairshare's pre-parbaked structure
(`app/main.py`, `app/auth.py`, `app/db/models.py`, etc.). The parbaked-native
migration ripped that scaffolding out — these tests no longer import.

They're preserved here as a porting reference. To re-enable a test:

1. Replace `from app.auth import …` with `from parbaked import current_user`.
2. Replace `from app.db.session import get_session` with `from parbaked import get_session`.
3. Replace `from app.db.models import …` with the right path: domain tables (`Group`, `Expense`, `Payment`, …) live in `models.py`; `User` lives at `parbaked.auth.models`.
4. Drop any `app.limiter`, `app.config.settings`, `REGISTRATION_INVITE_CODE`, or `app.main`-touching code — parbaked owns rate limits, config, and the FastAPI app.
5. Use parbaked's signup flow: `POST /auth/signup` then admin-approve via the `/auth/admin` dashboard (no invite codes). Tests typically fixture-up an active user via `parbaked.auth.service.approve_user` or by writing rows directly.
