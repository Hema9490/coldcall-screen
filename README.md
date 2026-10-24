# Cold Call Screen

A screen a caller keeps open during a cold call. It shows the current stage of the call, what prospects tend to say, quick taps for what happened, and a box for the prospect's own words. After the call, it is saved and listed under Past calls.

## Live links

- Frontend (Vercel): https://coldcall-screen-frontend.vercel.app
- Backend (Render): https://coldcall-backend-hema.onrender.com
- Health check: https://coldcall-backend-hema.onrender.com/health

Note: the Render server is on the free plan and sleeps when idle, so the first request can take about 50 seconds.

## How it works

1. The caller opens the Vercel page and starts a call.
2. The page calls the Render backend (Flask).
3. The backend reads and writes data in Supabase (Postgres).
4. When the call ends, the backend asks an LLM to check whether the outcome the caller chose matches the notes saved during the call.

## Which LLM is used and for what

Groq (free key), model `openai/gpt-oss-20b`. It is used for one job only: after the call, it compares the outcome the caller selected with the notes saved during the call and answers MATCH or MISMATCH with one sentence of reason. Callers sometimes log an outcome that does not match what happened, so this check happens before the call is saved.

## Stack

- Frontend: plain HTML, CSS and JavaScript (Vercel)
- Backend: Python Flask with gunicorn (Render)
- Database: Supabase Postgres, schema in `schema.sql`

## Backend endpoints

- `GET /` and `GET /health`: health check
- `GET /stages`: the 8 call stages
- `GET /calls` and `POST /calls`: list calls and start a call
- `GET /calls/<id>`: one call
- `POST /calls/<id>/stage`: save a stage result
- `POST /calls/<id>/check`: LLM check of the chosen outcome
- `POST /calls/<id>/close`: close the call with its outcome

## Folders

- `frontend/`: the screen
- `backend/`: the API
- `schema.sql`: Supabase tables

The sample call transcripts were used only for this task and are not included in this repository.