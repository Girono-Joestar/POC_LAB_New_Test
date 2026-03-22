# POC AI Lab — Developer Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Project Structure](#project-structure)
4. [Backend API Reference](#backend-api-reference)
5. [Frontend Design System](#frontend-design-system)
6. [Admin Portal](#admin-portal)
7. [Security Model](#security-model)
8. [Deployment Guide](#deployment-guide)
9. [Local Development](#local-development)
10. [Troubleshooting](#troubleshooting)

---

## Overview

POC AI Lab is an interactive web application for a university metrology and instrumentation laboratory. Students scan QR codes placed next to lab equipment and are taken to a page with:

- **Thumbnail cards** for each experiment (admin-configurable URL or gradient placeholder)
- **Images** of the apparatus (carousel)
- **Audio narration** describing the experiment
- **AI chatbot** (LangChain + NVIDIA NIM) that answers questions in context

An **admin portal** is hidden from public access and allows the administrator to:
- Add / edit / delete experiments via a form-based UI
- Manage labs (multi-lab support)
- Set thumbnail URLs for experiment cards
- Update API keys (universal or per-lab)
- Generate audio narrations

---

## Architecture

```
┌──────────────────────────────────────────┐
│               Browser (Client)           │
│  ┌────────────────┐  ┌────────────────┐  │
│  │  Public Site    │  │  Admin Portal  │  │
│  │  index.html     │  │  admin_5502    │  │
│  │  style.css      │  │  (hidden URL)  │  │
│  │  app.js         │  │                │  │
│  └───────┬────────┘  └───────┬────────┘  │
└──────────┼───────────────────┼───────────┘
           │  HTTP / JSON      │
┌──────────▼───────────────────▼───────────┐
│           FastAPI Backend (api/main.py)   │
│  ┌─────────────────────────────────────┐ │
│  │ GET  /api/experiments               │ │
│  │ GET  /api/experiments/{id}          │ │
│  │ POST /api/chat                      │ │
│  │ GET  /api/admin/settings  (auth)    │ │
│  │ POST /api/admin/update    (auth)    │ │
│  └─────────────────────────────────────┘ │
│              │               │           │
│     ┌────────▼──┐    ┌───────▼────┐      │
│     │ exps.json │    │ Gemini API │      │
│     │ settings  │    └────────────┘      │
│     └───────────┘                        │
└──────────────────────────────────────────┘
```

**Stack:**
| Layer    | Technology                  |
|----------|-----------------------------|
| Frontend | HTML5, CSS3, Vanilla JS     |
| Backend  | Python 3.10+, FastAPI       |
| AI       | LangChain + NVIDIA NIM      |
| RAG      | FAISS vector store          |
| Hosting  | Vercel (Serverless)         |
| Design   | Material 3 Expressive       |

---

## Project Structure

```
POC_AI_LAB/
├── api/
│   ├── main.py              # FastAPI backend (serverless function on Vercel)
│   ├── agent.py             # LangChain AI agent with tools
│   ├── rag_builder.py       # FAISS RAG vector store builder
│   └── rate_limiter.py      # API rate limiting utility
├── data/
│   ├── exps.json             # Experiment data (with thumbnail field)
│   ├── labs.json             # Lab registry (multi-lab support)
│   ├── settings.json         # Runtime settings (API key config)
│   └── *.mp3                 # Source audio files
├── public/                   # Served as static assets by Vercel
│   ├── index.html            # Main public page
│   ├── style.css             # Material 3 Expressive design system
│   ├── app.js                # Frontend logic (experiments, carousel, chat)
│   ├── admin_5502.html       # Hidden admin portal (form-based)
│   └── audio/                # Audio files served to browser
│       └── MQC-*.mp3
├── tests/
│   └── smoke_test.py         # Endpoint smoke tests
├── generate_audio.py         # gTTS audio generation script
├── .env                      # Local env vars (NVIDIA_API_KEY, ADMIN_TOKEN)
├── requirements.txt          # Python dependencies
└── vercel.json               # Vercel config (rewrites, functions)
```

---

## Backend API Reference

### `GET /api/health`
Health check.  
**Response:** `{ "status": "ok" }`

### `GET /api/experiments`
Returns a lightweight list of all experiments. Supports `?lab=MQC` filter.  
**Response:**
```json
[
  {
    "id": "MQC-01",
    "apparatus": "Linear Measurement Instruments",
    "short_desc": "Measure component dimensions…",
    "lab_id": "MQC",
    "thumbnail": "https://example.com/image.jpg"
  }
]
```
> **Note:** `thumbnail` prefers the dedicated `thumbnail` field, falls back to `images[0]`, or returns `""` if neither is set.

### `GET /api/experiments/{exp_id}`
Returns full detail for one experiment.  
**404** if `exp_id` not found.

### `POST /api/chat`
Send a student question, get an AI response in experiment context.  
**Body:**
```json
{
  "prompt": "How does this work?",
  "experiment_id": "BKR-01"
}
```
**Response:** `{ "reply": "The dead weight tester works by…" }`

### `GET /api/admin/settings?token=<TOKEN>`
Returns settings and lab config. **403** if token is wrong.

### `POST /api/admin/settings`
Update universal API key or per-lab key overrides.

### `PUT /api/admin/experiments/{exp_id}`
Update experiment data (including `thumbnail`, `images`, etc.).

### `POST /api/admin/labs/{lab_id}/experiments`
Create a new experiment under a lab.

### `DELETE /api/admin/experiments/{exp_id}`
Delete an experiment.

### `POST /api/admin/experiments/{exp_id}/generate-audio`
Generate audio narration using gTTS.

---

## Frontend Design System

The CSS follows **Material 3 Expressive** guidelines:

| M3 Token                     | Value                        | Usage                      |
|------------------------------|------------------------------|----------------------------|
| `--md-sys-color-primary`     | `#cfbcff` (Violet 80)       | Buttons, links, accents    |
| `--md-sys-color-surface`     | `#141218` (Neutral 6)       | Page background            |
| `--md-sys-shape-corner-xl`   | `28px`                       | Cards, containers          |
| `--md-sys-motion-emphasized` | `0.4s cubic-bezier(0.2,0,0,1)` | Transitions, animations |

**Typography** uses Google Sans for headlines and Roboto for body text, matching M3 type scale.

**Components implemented:**
- Top App Bar (sticky)
- Hero section with animated gradient blob
- Experiment cards with staggered fade-in
- Image carousel with prev/next buttons and dot indicators
- Chat window with typing indicator
- FAB (Floating Action Button)
- Responsive grid (3-col → 1-col on mobile)

---

## Admin Portal

**Access URL:** `/secret-admin-portal`  
This URL is not linked from any public page. It is mapped via `vercel.json` to `admin_5502.html`.

**Features:**
1. Token-based authentication (matches `ADMIN_TOKEN` env var)
2. **Experiments** — Card grid with Edit/Delete per card + form-based Add/Edit
3. **Labs** — Create/delete labs, set lab name and description
4. **Settings** — Universal API key + per-lab API key overrides
5. **Thumbnail URL** — Dedicated field per experiment for card images
6. **Image URLs** — Carousel image management
7. **Audio** — Preview player + server-side generation trigger
8. Toast notifications for success/error feedback
9. Confirmation dialogs for delete operations

**Security:**
- `<meta name="robots" content="noindex, nofollow">` prevents search engine indexing
- The page title is generic ("Lab Admin Panel") to avoid discoverability
- No links point to this page from anywhere in the codebase

---

## Security Model

| Threat                          | Mitigation                                                       |
|---------------------------------|------------------------------------------------------------------|
| JSON data exposed via browser   | `data/` folder is outside `public/`; data served only via API    |
| Admin page discoverable         | Hidden URL, noindex meta, no links from public pages             |
| API key leaked client-side      | Key stored server-side in `settings.json` / env vars only        |
| Unauthorized admin access       | Token-based auth on all admin endpoints                          |
| Brute-force token guessing      | Use long, random `ADMIN_TOKEN` in production                     |
| XSS via experiment data         | Frontend uses `textContent` (not `innerHTML`) for user data      |

---

## Deployment Guide

### Prerequisites
- Node.js (for Vercel CLI)
- Python 3.10+
- A NVIDIA NIM API key

### Steps

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Set environment variables** in Vercel Dashboard:
   | Variable       | Description                    | Example                          |
   |----------------|--------------------------------|----------------------------------|
   | `NVIDIA_API_KEY`| NVIDIA NIM API key             | `nvapi-…`                        |
   | `ADMIN_TOKEN`  | Secret token for admin access  | `my-very-long-random-string-42` |

3. **Deploy:**
   ```bash
   cd POC_AI_LAB
   vercel
   ```

4. **Access:**
   - Public site: `https://your-project.vercel.app/`
   - Admin portal: `https://your-project.vercel.app/secret-admin-portal`

### Important: Vercel Filesystem
Vercel serverless functions have a **read-only filesystem**. Changes made via the admin portal (updating JSON/API key at runtime) will persist only until the next cold start or redeploy. For persistent runtime changes, consider integrating a database (e.g., Vercel KV, Redis, or a free MongoDB Atlas tier).

---

## Local Development

1. **Activate the virtual environment:**
   ```powershell
   .\.venv\Scripts\Activate
   ```

2. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Set environment variables** (already in `.env`):
   ```
   NVIDIA_API_KEY=nvapi-…
   ADMIN_TOKEN=supersecret
   ```

4. **Run the dev server:**
   ```powershell
   uvicorn api.main:app --reload --port 8000
   ```
   > **Note:** This serves only the API. To serve static files too, use a local proxy or open `public/index.html` directly while pointing fetch calls to `http://localhost:8000`.

5. **Or use Vercel locally:**
   ```powershell
   vercel dev
   ```
   This emulates the full Vercel environment including static file serving and rewrites.

---

## Troubleshooting

| Problem                        | Solution                                                      |
|--------------------------------|---------------------------------------------------------------|
| "No API key configured"        | Set `NVIDIA_API_KEY` in `.env` or update via admin portal     |
| Carousel shows no images       | Check that image URLs in `exps.json` are valid and accessible |
| Card shows gradient instead    | Set a thumbnail URL via Admin → Edit experiment → Thumbnail URL |
| Audio doesn't play             | Ensure `audio/*.mp3` files exist in `public/audio/`           |
| Admin page returns 404         | Verify `vercel.json` has the rewrite for `/secret-admin-portal` |
| Chat returns 502               | API error — check key validity or rate limits                 |
| Changes lost after redeploy    | Expected on Vercel — use env vars for permanent config        |
| Admin save returns 500         | Filesystem may be read-only (Vercel) — run admin locally      |
