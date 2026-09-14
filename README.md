# QuestHub — new React UI integrated with supplied FastAPI backend

This bundle keeps the supplied FastAPI backend and replaces the frontend with a completely new React/Vite UI. The original frontend is not reused.

## Run backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload
```

## Run frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL (normally http://localhost:5173).

The frontend calls the supplied backend at `http://localhost:8000` by default and sends credentials so the backend's HttpOnly session cookie is used.

You can override it with:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Accounts from the supplied backend README

- admin / ChangeMe123!
- youthworker / ChangeMe123!
- player01 / ChangeMe123!

## Connected endpoints

### Auth
- GET `/api/auth/me`
- POST `/api/auth/login`
- POST `/api/auth/logout`

### Youth worker / admin
- GET `/api/admin/overview`
- GET `/api/admin/players`
- POST `/api/admin/xp/award`
- GET `/api/admin/audit`
- GET `/api/admin/themes`
- GET `/api/admin/phases`
- GET `/api/admin/point-rules`
- GET `/api/admin/rewards`
- GET `/api/admin/jackpot`

### Public
- GET `/api/public/dashboard`
- GET `/api/gamification/leaderboards`

### Player
- GET `/api/player/dashboard`
- GET `/api/reward-games/player`
- POST `/api/reward-games/{play_id}/play`

The Spin the Wheel UI uses the real reward-game play endpoint. The backend chooses the prize server-side, so the frontend never decides the reward amount.

## Important architecture choice

`frontend/src/api.ts` is the only API service layer. The UI components consume normalized backend responses and can be extended with adapters without rewriting the visual system.

The public dashboard is intentionally unauthenticated. Staff/player dashboards require the backend session.
