# QuestHub React Prototype

This is a completely new React/Vite frontend for the QuestHub concept. It does not reuse the frontend from the supplied repository.

## Run

```bash
npm install
npm run dev
```

Open the Vite URL shown in the terminal.

## What is included

- Youth Worker dashboard
- Admin dashboard
- Public dashboard
- Responsive desktop/tablet/mobile layouts
- Role switcher
- Player management
- Points/rewards flow
- Community nomination triage
- Public visibility toggle
- Positive-only Spin the Wheel modal
- Toasts
- Mock data
- API service boundary in `src/api.ts`

## API integration

The UI intentionally uses mock data. Replace functions in `src/api.ts` with your endpoints later.

Set:

```bash
VITE_API_BASE_URL=http://your-api
```

Then replace the mock functions with `fetch()` calls.

The design intentionally keeps the UI independent from the API response shape so you can add adapters later.
