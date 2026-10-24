# Cold Call Guide

A screen a caller keeps open during a cold call. It follows the eight stages of a call, shows what prospects tend to say at each stage, saves what happened and the prospect's own words, and lists past calls with the stage each one reached.

## Live links

- Vercel app (frontend): https://coldcall-screen-frontend.vercel.app
- Render backend health check: https://coldcall-backend-hema.onrender.com/health

The backend runs on Render's free plan and sleeps when idle, so the first request can take up to a minute.

## Stack

- Supabase: database (tables calls, stage_results, stages). The SQL is in schema.sql
- Render: Flask backend in the backend folder
- Vercel: plain HTML, CSS and JavaScript frontend in the frontend folder
- LLM: Groq, model openai/gpt-oss-20b, on a free key

## What the LLM does

When the caller ends a call, the backend sends the outcome they picked and the notes they recorded to the LLM. It answers MATCH or MISMATCH with one short reason. This is because callers sometimes log an outcome that does not match what was said on the call.

## Backend endpoints

- GET /health: answers when the backend is up
- GET /stages: the eight stages
- POST /calls: start a call
- GET /calls: list calls
- GET /calls/id: one call with its stage results
- POST /calls/id/stage: save a stage result
- POST /calls/id/check: ask the LLM if the outcome fits the notes
- POST /calls/id/close: close a call with an outcome

## Environment variables (set on Render, not in the repo)

SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY, GROQ_MODEL