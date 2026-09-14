QUESTHUB — PLAYER QUEST QR / EXTRA XP REQUESTS

This implementation changes the personal Player QR flow:

Player Dashboard
  -> My Quest QR
  -> another person scans the QR
  -> QuestHub opens /request-points?token=...
  -> requester enters requested XP + reason
  -> request is PENDING
  -> youth worker/admin reviews
       APPROVE -> XP is written to the normal XP ledger
       REJECT  -> no XP is awarded
  -> decision is recorded in the audit log

The existing staff attendance workflow remains separate.

BACKEND
1. cd into your backend directory.
2. Copy backend/apply_backend_points_request_patch.py there.
3. Run:
       python3 apply_backend_points_request_patch.py
4. Restart FastAPI.

FRONTEND
1. Back up your current frontend src/App.tsx, src/api.ts, src/styles.css and package.json.
2. Replace those four files with the versions in frontend/.
3. Also copy frontend/src/vite-env.d.ts into src/.
4. Run:
       npm install
       npm run build

IMPORTANT
- Do not run the old questhub_frontend_patch.py again.
- The QR contains an opaque token, not the player's name.
- The QR opens the frontend's current origin. For a real phone-to-phone/deployed setup,
  use the real reachable frontend URL rather than localhost.
