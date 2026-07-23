# POC AI Lab — Developer Workflow & Handover Guide

> **Audience:** Developers taking over maintenance of this project.  
> **Last Updated:** March 2026

---

## 1. System Overview Flowchart

```mermaid
graph TB
    subgraph Internet
        QR["📱 QR Code Scan"]
        Browser["🖥️ Browser"]
    end

    subgraph Vercel["☁️ Vercel Platform"]
        Static["📁 Static Assets<br/>(public/)"]
        Serverless["⚡ Serverless Function<br/>(api/main.py)"]
    end

    subgraph ServerData["📦 Server-Side Data"]
        ExpsJSON["📄 data/exps.json<br/>(Experiment Data)"]
        SettingsJSON["⚙️ data/settings.json<br/>(API Key Config)"]
        EnvVars["🔐 Environment Variables<br/>(GKEY, ADMIN_TOKEN)"]
    end

    subgraph External["🌐 External Services"]
        Gemini["🤖 Google Gemini API<br/>(gemini-2.0-flash)"]
    end

    QR --> |"?exp=BKR-01"| Browser
    Browser --> |"GET /*.html, *.css, *.js"| Static
    Browser --> |"GET/POST /api/*"| Serverless
    Serverless --> |"Read/Write"| ExpsJSON
    Serverless --> |"Read/Write"| SettingsJSON
    Serverless --> |"Read"| EnvVars
    Serverless --> |"generate_content()"| Gemini
```

---

## 2. Public User Flow

This is what happens when a **student or visitor** uses the site.

```mermaid
flowchart TD
    A["🌐 User opens website<br/>(or scans QR code)"] --> B{"URL has ?exp= param?"}

    B -- Yes --> C["🔗 Deep-link detected<br/>log: 'QR deep-link detected'"]
    C --> D["📡 GET /api/experiments/{id}<br/>log: 'Fetching experiment detail'"]

    B -- No --> E["📡 GET /api/experiments<br/>log: 'Fetching experiment list'"]
    E --> EE["🎨 Render Hero Carousel<br/>(auto-advancing)"]
    EE --> F{"API responds OK?"}
    F -- No --> G["❌ Show error message<br/>log: 'Failed to load experiments'"]
    G --> G1["Hide Hero Carousel"]
    F -- Yes --> H["🎨 Render experiment cards<br/>log: 'Rendering N experiment cards'"]
    H --> I["👆 User clicks a card<br/>log: 'Card clicked: BKR-XX'"]
    I --> II["🙈 Hide Hero Carousel<br/>(detail view focus)"]
    II --> D

    D --> J{"API responds OK?"}
    J -- No --> K["❌ Show error<br/>log: 'Failed to load detail'"]
    J -- Yes --> L["🎨 Render detail view"]

    L --> L1["🖼️ Build image carousel<br/>log: 'Building carousel with N images'"]
    L --> L2["🔊 Load audio player<br/>log: 'Audio source set'"]
    L --> L3["📝 Show narration text"]
    L --> L4["🤖 Chat window ready<br/>log: 'Chat window reset'"]

    L4 --> M["💬 User types question"]
    M --> N["📡 POST /api/chat<br/>log: 'Sending chat — exp=X, prompt=...'"]
    N --> O{"Gemini responds?"}
    O -- Yes --> P["✅ Show AI reply<br/>log: 'AI replied in Xms — N chars'"]
    O -- No --> Q["⚠️ Show error message<br/>log: 'Chat failed after Xms'"]
    P --> M
    Q --> M
```

---

## 3. Admin Workflow

This is how the **admin** manages data and settings.

```mermaid
flowchart TD
    A["🔐 Admin navigates to<br/>/secret-admin-portal"] --> B["🔑 Enter ADMIN_TOKEN"]
    B --> C["📡 GET /api/admin/settings?token=X<br/>log: 'Admin settings request'"]
    C --> D{"Token valid?"}

    D -- No --> E["🚫 Show 'Invalid token'<br/>log: 'Admin auth FAILED'"]
    E --> B

    D -- Yes --> F["✅ Auth successful<br/>log: 'Admin auth successful'"]
    F --> G["📡 GET /api/experiments<br/>log: 'Loading experiment data'"]
    G --> H["📡 GET /api/experiments/{id}<br/>for each experiment"]
    H --> I["🎨 Show dashboard:<br/>• API Key field<br/>• JSON Editor"]

    I --> J{"Admin action?"}

    J -- Edit JSON --> K["✏️ Modify JSON in editor"]
    J -- Change API Key --> L["🔑 Update API key field"]
    J -- Format JSON --> M["🔧 Click Format<br/>log: 'Formatting JSON'"]

    K --> N["💾 Click Save"]
    L --> N
    M --> J

    N --> O["📡 POST /api/admin/update<br/>log: 'Admin update request'"]
    O --> P{"Save successful?"}
    P -- Yes --> R["✅ Toast: 'Saved!'<br/>log: 'Admin update completed'"]
    P -- No --> S["❌ Toast: Error<br/>log: 'Admin update FAILED'"]
    R --> J
    S --> J
```

---

## 4. Backend Request Lifecycle

Every single HTTP request goes through this pipeline:

```mermaid
flowchart TD
    A["🌐 Incoming HTTP Request"] --> B["📝 Logging Middleware<br/>log: '➡️ METHOD /path from IP'"]
    B --> C["⏱️ Start timer"]
    C --> D{"Route match?"}

    D -- "/api/health" --> E["💓 Return status: ok"]
    D -- "/api/experiments" --> F["📄 Read exps.json<br/>log: 'Listing experiments — N found'"]
    D -- "/api/experiments/{id}" --> G["📄 Read exps.json<br/>Lookup by ID"]
    D -- "/api/chat" --> H["🤖 Gemini Flow"]
    D -- "/api/admin/*" --> I["🛡️ Auth Check"]
    D -- No match --> J["404 Not Found"]

    G --> G1{"Experiment exists?"}
    G1 -- Yes --> G2["✅ Return experiment<br/>log: 'Returning detail for X'"]
    G1 -- No --> G3["❌ 404<br/>log: 'Experiment not found: X'"]

    H --> H1["🔑 get_gemini_key()<br/>log: 'Gemini key loaded from...'"]
    H1 --> H2{"Key available?"}
    H2 -- No --> H3["❌ 500: Key not configured<br/>log: 'No API key configured'"]
    H2 -- Yes --> H4["🤖 genai.configure()"]
    H4 --> H5["📤 model.generate_content()<br/>log: 'Using model: gemini-2.0-flash'"]
    H5 --> H6{"Gemini OK?"}
    H6 -- Yes --> H7["✅ Return reply<br/>log: 'Gemini responded in Xms'"]
    H6 -- No --> H8["❌ 502: Gemini error<br/>log: 'Gemini API error + traceback'"]

    I --> I1{"Token matches ADMIN_TOKEN?"}
    I1 -- No --> I2["🚫 403 Unauthorized<br/>log: 'Admin auth FAILED'"]
    I1 -- Yes --> I3["✅ Process admin request<br/>log: 'Admin auth successful'"]

    E --> Z["⏱️ Stop timer"]
    F --> Z
    G2 --> Z
    G3 --> Z
    H7 --> Z
    H8 --> Z
    H3 --> Z
    I2 --> Z
    I3 --> Z
    J --> Z

    Z --> ZZ["📝 Log response<br/>log: '⬅️ METHOD /path → STATUS (Xms)'"]
```

---

## 5. Data Flow Diagram

Shows how data moves between components:

```mermaid
flowchart LR
    subgraph Client["🖥️ Browser"]
        FE["Frontend (app.js)"]
        Admin["Admin Portal"]
    end

    subgraph API["⚡ FastAPI Backend"]
        ListEP["GET /api/experiments"]
        DetailEP["GET /api/experiments/{id}"]
        ChatEP["POST /api/chat"]
        SettingsEP["GET /api/admin/settings"]
        UpdateEP["POST /api/admin/update"]
    end

    subgraph Storage["📦 Server Files"]
        Exps["exps.json"]
        Settings["settings.json"]
    end

    subgraph External["🌐 External"]
        Gemini["Google Gemini"]
    end

    FE -- "fetch list" --> ListEP
    FE -- "fetch detail" --> DetailEP
    FE -- "send question" --> ChatEP
    Admin -- "authenticate" --> SettingsEP
    Admin -- "save changes" --> UpdateEP

    ListEP -- "read" --> Exps
    DetailEP -- "read" --> Exps
    ChatEP -- "read context" --> Exps
    ChatEP -- "send prompt" --> Gemini
    SettingsEP -- "read" --> Settings
    UpdateEP -- "write" --> Exps
    UpdateEP -- "write" --> Settings
```

---

## 6. File Change Impact Matrix

Use this to understand what to check when you modify a file:

| File Modified | What It Affects | What to Test |
|---|---|---|
| `data/exps.json` | All experiment cards, detail pages, chat context | Refresh main page, check each experiment detail |
| `data/settings.json` | Gemini API key used for chat | Test chat — send a question |
| `api/main.py` | All API endpoints | Run `uvicorn`, hit each endpoint |
| `public/index.html` | Page structure, layout | Visual check in browser |
| `public/style.css` | All visual styling | Visual check — cards, chat, carousels (hero & detail) |
| `public/app.js` | All frontend behavior | Click cards, use carousels (hero class), chat |
| `public/images/` | Hero carousel assets | Verify image links in app.js initHeroCarousel() |
| `public/admin_5502.html` | Admin portal only | Go to `/secret-admin-portal`, login, edit, save |
| `vercel.json` | Routing, deployment | Deploy to Vercel, check all routes |
| `.env` | API keys, admin token | Restart server, test auth and chat |
| `requirements.txt` | Backend dependencies | `pip install -r requirements.txt` |

---

## 7. Log Reference Table

### Backend Logs (Python — `api/main.py`)

| Emoji | Category | Example Log | When It Fires |
|---|---|---|---|
| 🚀 | Startup | `POC AI Lab backend starting up` | Server boots |
| ✅ | Success | `Startup complete — 12 experiments loaded` | After init |
| ➡️ | Request In | `GET /api/experiments from 192.168.1.1` | Every HTTP request |
| ⬅️ | Response Out | `GET /api/experiments → 200 (45ms)` | Every HTTP response |
| 📋 | List | `Listing experiments — 12 found` | GET /api/experiments |
| 🔍 | Detail | `Fetching experiment detail: BKR-01` | GET /api/experiments/{id} |
| 💬 | Chat | `Chat request — exp=BKR-01, prompt_length=42` | POST /api/chat |
| 🤖 | Gemini | `Gemini responded in 1200ms — 350 chars` | After Gemini reply |
| 🔑 | API Key | `Gemini key loaded from settings.json` | On each chat request |
| 🛡️ | Auth | `Admin settings request` | Admin endpoint hit |
| 🚫 | Auth Fail | `Admin auth FAILED — invalid token` | Wrong token |
| 💾 | Write | `Wrote data/exps.json (6455 bytes)` | Admin save |
| 📄 | Read | `Read data/exps.json — 12 top-level keys` | Any file read |
| 🔒 | Permission | `Permission denied — filesystem read-only` | Vercel write attempt |
| 💥 | Error | `Gemini API error after 500ms: ...` | Any exception |
| 🛑 | Shutdown | `Shutting down POC AI Lab backend` | Server stops |

### Frontend Logs (JavaScript — `app.js`)

| Emoji | Category | Example Log | Where to See |
|---|---|---|---|
| ℹ️ | Info | `App script loaded — initializing…` | Browser Console |
| 🌐 | Network | `→ GET /api/experiments` | Browser Console |
| 🌐 | Network | `← GET /api/experiments → 200 (120ms)` | Browser Console |
| 🎨 | UI | `Rendering 12 experiment cards` | Browser Console |
| 🎨 | UI | `Carousel built and ready` | Browser Console |
| 💬 | Chat | `Sending chat — exp=BKR-01...` | Browser Console |
| ✅ | Success | `AI replied in 1500ms — 300 chars` | Browser Console |
| ⚠️ | Warning | `Carousel image failed to load: URL` | Browser Console |
| ❌ | Error | `Failed to load experiments: ...` | Browser Console |
| 🔗 | Deep Link | `QR deep-link detected: exp=BKR-01` | Browser Console |
| 🐛 | Debug | `Carousel slide: 2/3` | Browser Console |

### Admin Logs (JavaScript — `admin_5502.html`)

| Emoji | Category | Example Log | When |
|---|---|---|---|
| 🔐 | Login | `Login attempt…` | Token submitted |
| ✅ | Auth | `Authentication successful` | Valid token |
| 🚫 | Auth | `Login FAILED — invalid token` | Wrong token |
| 📋 | Load | `Found 12 experiments — fetching…` | After login |
| 💾 | Save | `Save initiated…` | Save button clicked |
| 📄 | Parse | `JSON parsed — 12 entries` | Before save |
| 🔧 | Format | `Formatting JSON…` | Format clicked |
| 🍞 | Toast | `Toast [success]: Saved!` | Any notification |

---

## 8. Common Maintenance Scenarios

### Scenario 1: Add a New Experiment
```
1. Open Admin Portal → /secret-admin-portal
2. Login with ADMIN_TOKEN
3. In JSON editor, add a new entry like "BKR-13": { ... }
4. Upload the audio .mp3 to public/audio/
5. Click Save
6. Verify: Check backend logs for "💾 Wrote data/exps.json"
7. Verify: Refresh main page — new card should appear
```

### Scenario 2: Gemini Stops Responding
```
1. Check backend logs for "💥 Gemini API error"
2. Check if API key is valid → Admin Portal → check key field
3. Check Google Cloud Console for API quota/billing
4. Look for: "🔑 No Gemini API key found" in logs
5. If key expired → update via Admin Portal or Vercel env vars
```

### Scenario 3: Images Not Loading
```
1. Check frontend console for "⚠️ Carousel image failed to load: URL"
2. Open the image URL directly in browser — is it a dead link?
3. If dead → update image URLs in exps.json via Admin Portal
4. If CORS issue → images need to be from a CORS-enabled server
```

### Scenario 4: Admin Cannot Login
```
1. Check backend logs for "🚫 Admin auth FAILED"
2. Verify ADMIN_TOKEN in .env (local) or Vercel Dashboard (prod)
3. Make sure no leading/trailing spaces in the token
4. On Vercel: check Environment Variables → Redeploy after changes
```

### Scenario 5: Changes Not Persisting on Vercel
```
1. This is EXPECTED — Vercel has a read-only filesystem
2. Backend log will show: "🔒 Permission denied — filesystem read-only"
3. Solution A: Update env vars in Vercel Dashboard → Redeploy
4. Solution B: Integrate a database (Vercel KV, Redis, MongoDB)
5. For file changes: edit locally → git push → redeploy
```

---

## 9. Deployment Pipeline

```mermaid
flowchart LR
    A["✏️ Edit code locally"] --> B["🧪 Test with<br/>vercel dev"]
    B --> C{"Tests pass?"}
    C -- No --> A
    C -- Yes --> D["📤 git push<br/>(or vercel --prod)"]
    D --> E["☁️ Vercel builds"]
    E --> F{"Build OK?"}
    F -- No --> G["🔍 Check build logs<br/>on Vercel Dashboard"]
    G --> A
    F -- Yes --> H["🌐 Live at<br/>your-app.vercel.app"]
    H --> I["🧪 Smoke test:<br/>1. Load main page<br/>2. Open a card<br/>3. Ask AI a question<br/>4. Check admin portal"]
```

---

## 10. Quick Command Reference

| Task | Command |
|---|---|
| Start local server | `.\.venv\Scripts\Activate; uvicorn api.main:app --reload --port 8000` |
| Start with Vercel emulation | `vercel dev` |
| Install dependencies | `.\.venv\Scripts\pip install -r requirements.txt` |
| Deploy to Vercel | `vercel --prod` |
| View backend logs (local) | Logs print directly to terminal |
| View frontend logs | Browser → F12 → Console → filter `[POC-AI-LAB]` |
| View admin logs | Browser → F12 → Console → filter `[ADMIN]` |
| Check API health | `curl http://localhost:8000/api/health` |
