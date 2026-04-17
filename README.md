# CLOS AI

CLOS AI is an AI-assisted cloud optimising solution tool. It turns a natural-language workload description into a generic architecture blueprint, scores cloud options, and maps the result to native services for AWS, GCP, or Azure. The app includes a protected workspace, a visual canvas, live market intelligence, and a backend that continuously refreshes cloud policy and pricing data.

## Why this project exists

Choosing a cloud platform is usually a mix of architecture design, budget tradeoffs, service mapping, and compliance checks. This project is meant to reduce that manual work by giving engineers a single place to:

- describe a workload in plain language,
- get a generic architecture plan,
- compare providers across scoring dimensions,
- map generic components to native cloud services,
- estimate cost and feasibility,
- and keep the recommendations current with crawled provider intel.

## What it does

The product has two major parts:

- A Next.js frontend that provides the public landing page, authentication screens, and the protected architecture workspace.
- A FastAPI backend that handles auth, chat-driven blueprint generation, provider scoring, native service mapping, database persistence, and background market-intel refresh jobs.

## Key features

- Conversational architecture design for cloud workloads.
- Login and signup with JWT-based authentication.
- Protected workspace that loads chat history and prior blueprints.
- Visual architecture canvas for the generated generic blueprint.
- Provider scoring and comparison view for cloud selection.
- Native mapping for AWS, GCP, and Azure services.
- Live pricing and market-intelligence enrichment from backend services.
- Deployment plan reporting for the generated architecture.
- Background sync that crawls cloud provider docs and distills policy updates into MongoDB.
- Local knowledge-base/RAG support for architecture guidance.

## Tech stack

- Frontend: Next.js 16, React 19, Framer Motion, Lucide Icons, React Markdown.
- Backend: FastAPI, Uvicorn, Pydantic, Motor, MongoDB, LangChain, Gemini, Tavily, FAISS, FastEmbed.
- Deployment/runtime support: Dockerfiles for backend execution, Vercel cron configuration, and a combined production script in `package.json`.

## Project structure

- `src/app` contains the Next.js app routes for the landing page, login, signup, and workspace.
- `src/components` contains the workspace UI, including the canvas, chat sidebar, decision matrix, and report view.
- `backend` contains the FastAPI application, services, routes, schemas, and test files.
- `data` and `backend/dataset` store the cloud registry and training/reference data used by the backend services.

## Prerequisites

- Node.js 18 or newer.
- Python 3.13 or newer.
- MongoDB, either local or hosted.
- A Gemini API key for LLM features.
- A Tavily API key if you want live web search and extraction.

## Environment variables

Create `backend/.env` for the backend settings. The app also reads `NEXT_PUBLIC_API_URL` on the frontend when the API is hosted separately.

Backend variables:

- `GEMINI_API_KEY`
- `TAVILY_API_KEY`
- `MONGODB_URI`
- `MONGODB_USER`
- `MONGODB_PASSWORD`
- `MONGODB_CLUSTER`
- `MONGODB_DB`
- `FRONTEND_URL`
- `CRON_SECRET`

Frontend variable:

- `NEXT_PUBLIC_API_URL`

If `MONGODB_URI` is not set, the backend falls back to a local MongoDB connection at `mongodb://localhost:27017/cloud_compare`.

## Setup

Install the frontend dependencies from the project root:

```bash
npm install
```

Install the backend dependencies using your preferred Python workflow. The repository is set up for `uv`, and the backend dependencies are also listed in `backend/requirements.txt`:

```bash
cd backend
uv sync
```

If you are not using `uv`, create a virtual environment and install `backend/requirements.txt` manually.

## Run locally

Run the frontend in one terminal:

```bash
npm run dev
```

Run the backend in another terminal:

```bash
uv run uvicorn main:app --app-dir backend --reload --port 8000
```

If the frontend and backend are hosted on different ports or domains, set `NEXT_PUBLIC_API_URL` to the backend base URL before starting the frontend.

Open the app at:

- Frontend: `http://localhost:3000`
- Backend health check: `http://localhost:8000/health`

## Production run

The root `package.json` includes a combined production command that starts the Next.js app and the FastAPI backend together:

```bash
npm run complete:prod
```

This expects `uv` to be available on your machine.

## Main routes

Frontend routes:

- `/` landing page
- `/login`
- `/signup`
- `/workspace`

Backend routes:

- `GET /` service status
- `GET /health` dependency health summary
- `POST /api/auth/signup`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/chat`
- `GET /api/chats`
- `GET /api/chat/{chat_id}`
- `POST /api/chat/refine`
- `GET /api/blueprint/{blueprint_id}`
- `GET /api/blueprints/chat/{chat_id}`
- `POST /api/blueprint/update`
- `POST /api/blueprint/map-native`
- `POST /api/cron/sync`

## Notes

- The backend initializes a local knowledge base on startup and can run a background sync loop outside serverless mode.
- The app uses bearer-token authentication, so the workspace requires a successful login before accessing the chat and blueprint views.
- The backend is designed to work with MongoDB persistence, but still exposes a local fallback URI for development.

## Deployment

- The repository includes Dockerfiles for backend container execution.
- A `vercel.json` file is present for Vercel-specific routing and cron scheduling.

## Development references

- Frontend landing page: `src/app/page.js`
- Protected workspace: `src/app/workspace/page.js`
- Authentication screens: `src/app/login/page.js`, `src/app/signup/page.js`
- Backend entry point: `backend/main.py`

