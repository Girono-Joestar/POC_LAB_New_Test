# MQC AI Lab — Knowledge Base

This document provides a technical and academic overview of the Metrology and Quality Control Laboratory experiments and the AI agent's logic.

## 1. Laboratory Overview (MQC)
The Metrology and Quality Control Lab at MES College of Engineering, Pune, focuses on precision measurement and quality assurance techniques.

### Experiments (Current)
| ID | Apparatus / Experiment Title | Key Concepts |
|---|---|---|
| **MQC-01** | Vernier Caliper & Micrometer | Least count, zero error, radial/axial measurement |
| **MQC-02** | Height Gauge & Bevel Protractor | Linear height, angular measurement to 5 arc minutes |
| **MQC-03** | Dial Gauge & Surface Plate | Flatness, parallelism, plunger vs lever types |
| **MQC-04** | Slip Gauges & Sine Bar | Angular measurement, gauge block wringing, trigonometry |
| **MQC-05** | Floating Carriage Micrometer | Thread metrology, effective diameter, 3-wire method |
| **MQC-07** | Gear Measurement & Sine Bar | Chordal thickness, addendum, circular pitch |

---

## 2. System Architecture

### Backend: FastAPI
- **File:** `api/main.py`
- **Logic:** Multi-lab support via `data/labs.json`. Each lab can have its own Gemini API key or use a universal one.
- **RAG:** Powered by `api/rag_builder.py`.

### AI Agent: LangChain
- **Files:** `api/agent.py`, `api/rag_builder.py`
- **Model:** `gemini-2.0-flash`
- **Memory:** `ConversationBufferWindowMemory` (6-message window).
- **Retrieval:** FAISS vector store with MMR (Maximal Marginal Relevance) to prevent repetitive AI responses.
- **Context:** Agent has access to `Procedure.md`, DOCX lab manuals, and structured experiment JSON data.

### Admin Panel
- **File:** `public/admin_5502.html`
- **Features:** 
  - Dynamic form for adding/editing experiments.
  - Lab manager for multi-lab setup.
  - Interactive API key management.
  - Server-side audio generation trigger using `gTTS`.

---

## 3. Data Flow
1. **Startup:** `rag_builder.py` reads all laboratory documents and builds a FAISS index in memory.
2. **User Interaction:** Student selects an experiment → `app.js` fetches rich JSON data.
3. **Chat:** Student asks a question → `api/chat` calls the LangChain agent.
4. **Reasoning:** Agent decides to use `SearchLabKnowledge` (RAG) or `GetExperimentDetail` (JSON data) to answer.
5. **Response:** Friendly, educational response returned to the UI.

## 4. Maintenance
- **Adding Experiments:** Use the Admin Panel or edit `data/exps.json`.
- **Audio:** After adding an experiment, run `python generate_audio.py` locally to create the MP3 narration before deploying.
- **RAG Updates:** New files in `data/LAB/Word/` are automatically picked up on the next server restart.
