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

- **Hero Carousel** on the main page showcasing the lab and equipment
- **Images** of the apparatus (carousel) in the detail view
- **Audio narration** describing the experiment
- **AI chatbot** (Google Gemini) that answers questions in context

An **admin portal** is hidden from public access and allows the administrator to:
- Edit experiment data (JSON)
- Update the Gemini API key at runtime

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
| AI       | Google Gemini 2.0 Flash     |
| Hosting  | Vercel (Serverless)         |
| Design   | Material 3 Expressive       |

---

## Project Structure

```
POC_AI_LAB/
├── api/
│   └── main.py              # FastAPI backend (serverless function on Vercel)
├── data/
│   ├── exps.json             # Experiment data (server-side only, not in public/)
│   ├── settings.json         # Runtime settings (API key override)
│   └── *.mp3                 # Source audio files
├── public/                   # Served as static assets by Vercel
│   ├── index.html            # Main public page
│   ├── style.css             # Material 3 Expressive design system
│   ├── app.js                # Frontend logic (refactored Carousel system, chat, etc.)
│   ├── admin_5502.html       # Hidden admin portal
│   ├── images/               # Hero carousel images (IMG_1.jpeg, etc.)
│   └── audio/                # Audio files served to browser
│       └── BKR-*.mp3
├── prototype_backup/         # Old Streamlit code (archived, not deployed)
│   ├── main.py
│   ├── audio_narr_gen.py
│   ├── gen_qr.py
│   └── ngrok_watchdog.ps1
├── .env                      # Local env vars (GKEY, ADMIN_TOKEN)
├── requirements.txt          # Python dependencies
└── vercel.json               # Vercel config (rewrites, functions)
```

---

## Backend API Reference

### `GET /api/health`
Health check.  
**Response:** `{ "status": "ok" }`

### `GET /api/experiments`
Returns a lightweight list of all experiments.  
**Response:**
```json
[
  {
    "id": "BKR-01",
    "apparatus": "BAKER Dead Weight Tester",
    "narration_script": "The BAKER Dead Weight Tester…",
    "thumbnail": "https://…/H6900.webp"
  }
]
```

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
Returns `settings.json` contents. **403** if token is wrong.

### `POST /api/admin/update`
Update experiment data and/or API key.  
**Body:**
```json
{
  "secret_token": "<ADMIN_TOKEN>",
  "data": { "BKR-01": { … } },
  "api_key": "AIza…"
}
```
**Response:** `{ "status": "success" }`

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
- **Hero Carousel** (auto-advancing, main page)
- Experiment cards with staggered fade-in
- **Generic Carousel System** (reusable class for hero and details)
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
2. View/edit the Gemini API key
3. View/edit the full experiment JSON
4. Format JSON button for readability
5. Toast notifications for success/error feedback

**Security:**
- `<meta name="robots" content="noindex, nofollow">` prevents search engine indexing
- The page title is generic ("System Panel") to avoid discoverability
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
- A Google Gemini API key

### Steps

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Set environment variables** in Vercel Dashboard:
   | Variable       | Description                    | Example                          |
   |----------------|--------------------------------|----------------------------------|
   | `GKEY`         | Gemini API key (fallback)      | `AIzaSy…`                       |
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
   GKEY=AIza…
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
| "Gemini API key not configured"| Set `GKEY` in `.env` or update via admin portal               |
| Carousel shows no images       | Check that image URLs in `exps.json` are valid and accessible |
| Audio doesn't play             | Ensure `audio/*.mp3` files exist in `public/audio/`           |
| Admin page returns 404         | Verify `vercel.json` has the rewrite for `/secret-admin-portal` |
| Chat returns 502               | Gemini API error — check key validity or rate limits          |
| Changes lost after redeploy    | Expected on Vercel — use env vars for permanent config        |
