# MQC AI Lab — Full Overhaul Implementation Plan

## Background

The lab currently shows 12 BKR experiments with short narration scripts. The goal is to completely replace them with 6 MQC experiments extracted from [data/LAB/Word/Procedure.md](file:///i:/Rishab/Programming/mahajan%20sir/POC_AI_LAB/data/LAB/Word/Procedure.md) and the 6 DOCX files, upgrade the AI agent to a deep LangChain + RAG agent, rebuild the admin panel into a proper form-based manager, generate natural-sounding audio per experiment, and make the public view show rich, tabbed procedure content.

The site is deployed on **Vercel** (Python serverless + static files).

> [!IMPORTANT]
> Vercel has a **read-only filesystem** at runtime. [exps.json](file:///i:/Rishab/Programming/mahajan%20sir/POC_AI_LAB/data/exps.json) and [settings.json](file:///i:/Rishab/Programming/mahajan%20sir/POC_AI_LAB/data/settings.json) writes at runtime will **fail silently** or throw `PermissionError`. The existing code already warns about this in comments. To support runtime data updates, we will add an endpoint that returns a 501 on Vercel but works locally/ngrok. For now, the admin panel will write to GitHub/local and remind the user to redeploy. Alternatively the admin can update settings via env vars on Vercel. 
> This is the same limitation that exists today — we keep the same pattern and add a clear admin notice.

> [!IMPORTANT]
> Audio files are **statically deployed**. Pre-generated audio will be committed alongside the code. When admin adds a new experiment locally, the `generate_audio.py` script must be re-run and files committed before re-deploying.

---

## Proposed Changes

### Component 1 — Data Layer

#### [MODIFY] [exps.json](file:///i:/Rishab/Programming/mahajan%20sir/POC_AI_LAB/data/exps.json)
Replace all 12 BKR entries with 6 MQC entries (MQC-01 to MQC-05, MQC-07). Each entry will include:
- `apparatus` — full instrument name
- `lab_id` — `"MQC"` (supports future multi-lab)
- `short_desc` — 1-sentence teaser
- `narration_script` — rich, paragraph-form narration (~200 words, suitable for audio)
- `objectives` — list of objectives
- `theory` — markdown-style theory sections
- `procedure` — ordered step-by-step instructions per method
- `key_points` — bullet list of takeaways
- `formulas` — key formulas
- `images` — placeholder Unsplash image URLs
- `audio_loc` — `"audio/MQC-01.mp3"`
- `qr_addr` — updated URL with new IDs

#### [NEW] [data/labs.json](file:///i:/Rishab/Programming/mahajan%20sir/POC_AI_LAB/data/labs.json)
New file holding lab registry:
```json
{
  "MQC": {
    "name": "Metrology & Quality Control Lab",
    "api_key_override": "",
    "use_universal_key": true,
    "exp_ids": ["MQC-01","MQC-02","MQC-03","MQC-04","MQC-05","MQC-07"]
  }
}
```

#### [MODIFY] [data/settings.json](file:///i:/Rishab/Programming/mahajan%20sir/POC_AI_LAB/data/settings.json)
Add `universal_api_key` and move `GEMINI_API_KEY` under `universal_api_key`.

---

### Component 2 — Audio Generation Script

#### [NEW] generate_audio.py (project root)
Standalone script (run locally before deploy). Uses `gTTS` for natural-sounding narrations. Features:
- Reads [data/exps.json](file:///i:/Rishab/Programming/mahajan%20sir/POC_AI_LAB/data/exps.json)
- For each experiment, generates a well-paced narration MP3 using the `narration_script` field
- Uses `gTTS` with `slow=False` and pauses between paragraphs (by splitting on `\n\n`)
- Saves as `public/audio/{exp_id}.mp3`
- Skips if file already exists unless `--force` flag used

---

### Component 3 — RAG Knowledge Base

#### [NEW] api/rag_builder.py
Called at app startup. Uses:
- `langchain_community.document_loaders.UnstructuredMarkdownLoader` for [Procedure.md](file:///i:/Rishab/Programming/mahajan%20sir/POC_AI_LAB/data/LAB/Word/Procedure.md)
- `langchain_community.document_loaders.Docx2txtLoader` for each DOCX file
- `langchain.text_splitter.RecursiveCharacterTextSplitter` (chunk size 800, overlap 100)
- `langchain_google_genai.GoogleGenerativeAIEmbeddings` for embeddings (model: `models/embedding-001`)
- `langchain_community.vectorstores.FAISS` for in-memory vector store
- **MMR retrieval** (`vectorstore.as_retriever(search_type="mmr", k=5, fetch_k=20)`)
- One FAISS index per lab (keyed by `lab_id`) for scoped retrieval

#### [NEW] api/agent.py
LangChain agent using:
- `langchain_google_genai.ChatGoogleGenerativeAI` (`gemini-2.0-flash`, `temperature=0.3`)
- `langchain.memory.ConversationBufferWindowMemory` (last 6 turns, keeps token cost low)  
- **Tools:**
  - `ExperimentDetailTool`: returns the full structured experiment dict for the active exp
  - `KnowledgeSearchTool`: queries the lab's FAISS MMR retriever with the question
- Agent type: `CONVERSATIONAL_REACT_DESCRIPTION` (structured-chat-zero-shot from `langchain.agents`)
- System prompt: friendly lab explainer, NOT a bot. Uses student's name context if available.
- Output parsing: raw `AgentExecutor.run()` → string reply

**Token Optimization:**
- MMR limits to 5 diverse chunks (avoids repetitive context)
- ConversationBufferWindowMemory limits history to 6 messages
- Experiment JSON injected only on first message, then referenced by tool
- Prompt truncated to 4000 chars max before tool call

---

### Component 4 — Backend API Overhaul

#### [MODIFY] [main.py](file:///i:/Rishab/Programming/mahajan%20sir/POC_AI_LAB/api/main.py)

**New endpoints:**
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/labs` | List all labs (from `labs.json`) |
| POST | `/api/admin/labs` | Create new lab |
| PUT | `/api/admin/labs/{lab_id}` | Update lab config |
| DELETE | `/api/admin/labs/{lab_id}` | Delete lab |
| GET | `/api/admin/labs/{lab_id}/experiments` | List experiments for lab |
| POST | `/api/admin/labs/{lab_id}/experiments` | Add experiment to lab |
| PUT | `/api/admin/experiments/{exp_id}` | Update experiment |
| DELETE | `/api/admin/experiments/{exp_id}` | Delete experiment |
| POST | `/api/admin/experiments/{exp_id}/generate-audio` | Trigger gTTS audio gen |

**Modified:**
- `/api/chat` — now invokes `agent.py` `AgentExecutor` instead of raw Gemini call
- `/api/experiments` — adds `lab_id` filter param (`?lab=MQC`)
- [get_gemini_key()](file:///i:/Rishab/Programming/mahajan%20sir/POC_AI_LAB/api/main.py#162-175) — checks per-lab override, then universal key, then env var

**Startup:**
- `rag_builder.build_all()` called in lifespan startup — builds FAISS indexes
- Agent instances cached per lab

---

### Component 5 — Admin UI Overhaul

#### [MODIFY] [admin_5502.html](file:///i:/Rishab/Programming/mahajan%20sir/POC_AI_LAB/public/admin_5502.html)

Complete rewrite of the panel section (login remains). New layout:

**Sidebar:** Lab switcher (tabs for each lab + "＋ New Lab" button)

**Main Panel tabs:**
1. **Settings** — Universal API key + per-lab API key override, toggle between global/per-lab
2. **Experiments** — Card grid of experiments with Edit/Delete per card + "＋ Add Experiment" button
3. **Add/Edit Experiment Form** (slide-in panel) with fields:
   - Experiment ID (auto-generated, editable)
   - Apparatus / Title
   - Short Description
   - Narration Script (textarea with live word count)
   - Objectives (dynamic list add/remove)
   - Theory (rich textarea with section support)
   - Procedure Steps (ordered dynamic list)
   - Key Points (tag-style add/remove)
   - Images (URL inputs + preview)
   - Audio (preview player + "Generate Audio" button)
4. **Labs** — Create/delete labs, set lab name and description

**UX features:**
- Changes saved via `POST /api/admin/update` (same endpoint, enhanced)
- Audio generation triggers `POST /api/admin/experiments/{id}/generate-audio`
- Toast notifications for save/delete/error
- Confirmation dialogs for delete operations
- Responsive grid layout

---

### Component 6 — Frontend View Overhaul

#### [MODIFY] [index.html](file:///i:/Rishab/Programming/mahajan%20sir/POC_AI_LAB/public/index.html)
- Add tab navigation: **Overview | Procedure | Theory | Key Points**
- Remove raw narration text div → replace with tabbed panels
- Add `<div id="procedure-steps">` with numbered step cards
- Add formula rendering section

#### [MODIFY] [app.js](file:///i:/Rishab/Programming/mahajan%20sir/POC_AI_LAB/public/app.js)
- [showDetails()](file:///i:/Rishab/Programming/mahajan%20sir/POC_AI_LAB/public/app.js#136-177) now populates tabs from new experiment fields
- Audio player shows step-by-step narration text highlighted as audio plays (using rough 1 sentence/5s estimate)
- Chat greeting changes per experiment: `"I'm your MQC Lab assistant — feel free to ask me anything about [apparatus]!"`
- Placeholder image: `https://placehold.co/600x400?text=MQC+Lab` when no image

#### [MODIFY] [style.css](file:///i:/Rishab/Programming/mahajan%20sir/POC_AI_LAB/public/style.css)
- Add tab strip styles
- Add procedure step card styles (numbered, accent left border)
- Add formula block styles (monospace, highlighted background)

---

### Component 7 — Requirements

#### [MODIFY] [requirements.txt](file:///i:/Rishab/Programming/mahajan%20sir/POC_AI_LAB/requirements.txt)
Add:
```
langchain
langchain-google-genai
langchain-community
faiss-cpu
docx2txt
gtts
unstructured
```

---

## Verification Plan

### Automated Tests
No existing test files found. We will write a lightweight smoke-test script:

**Script:** `tests/smoke_test.py`  
Run: `python tests/smoke_test.py` (with server running on localhost:8000)
- Checks `/api/health` → 200
- Checks `/api/experiments` → 200, contains MQC-01
- Checks `/api/experiments/MQC-01` → 200, contains `procedure` field
- Checks `/api/chat` with a test question → 200, non-empty reply
- Checks `/api/admin/settings?token=supersecret` → 200

### Audio Generation Test
Run: `.\.venv\Scripts\python.exe generate_audio.py`
- Verify `public/audio/MQC-01.mp3` through `MQC-07.mp3` (skip 6) exist and are >0 bytes

### Browser Verification (Manual, via browser tool)
1. Start server: `.\.venv\Scripts\uvicorn.exe api.main:app --reload --port 8000`
2. Open `http://localhost:8000` → experiment grid shows 6 MQC cards
3. Click any card → tabbed view (Overview / Procedure / Theory / Key Points) appears
4. Click Play on audio → sound plays
5. Type question in chat → friendly response from agent
6. Navigate to `http://localhost:8000/secret-admin-portal`
7. Login with token → interactive panel appears (not JSON textarea)
8. Click "Add Experiment" → form slides in
9. Fill form and save → experiment appears on main page after refresh
