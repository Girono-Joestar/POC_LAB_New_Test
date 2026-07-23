# AI-Powered Laboratory Assistant — BAKER LAB
## Proposal & Cost Analysis
**Institution:** MES College of Engineering, Pune  
**Lab:** BAKER Metrology & Instrumentation Laboratory  
**Date:** April 12, 2026  
**Prepared for:** Faculty Review & Administrative Approval  
**Scope:** 120 daily visitors, academic year deployment

---

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [What the System Does](#2-what-the-system-does)
3. [Current Technical Architecture](#3-current-technical-architecture)
4. [Traffic & Usage Model](#4-traffic--usage-model)
5. [AI Provider Pricing — All Models](#5-ai-provider-pricing--all-models)
   - [Google Gemini](#51-google-gemini)
   - [OpenAI / ChatGPT](#52-openai--chatgpt)
   - [Anthropic / Claude](#53-anthropic--claude)
6. [Monthly AI Cost Estimates](#6-monthly-ai-cost-estimates)
7. [Deployment Options & Hosting Costs](#7-deployment-options--hosting-costs)
8. [Total Cost of Ownership: Three Scenarios](#8-total-cost-of-ownership-three-scenarios)
9. [Production Readiness Gap Analysis](#9-production-readiness-gap-analysis)
10. [Recommended Path Forward](#10-recommended-path-forward)
11. [Appendix: Pricing Methodology](#11-appendix-pricing-methodology)

---

## 1. Executive Summary

The BAKER Lab AI Assistant is a working proof-of-concept (POC) that gives students instant, experiment-specific AI help. They scan a QR code next to any apparatus, land on a mobile-friendly page, see images and hear a narration, and can ask the chatbot anything about that experiment.

This document answers the three practical questions before a college commits:

1. **What does it actually cost to run?**
2. **Which AI provider makes the most sense?**
3. **What work remains before this is production-ready?**

**Short answer on cost:** For 120 daily visitors at normal engagement, the AI model cost runs between **$0 and $2/month** using the current Google Gemini 2.0 Flash setup. Even in a worst-case scenario where every visitor has an extended conversation, monthly AI costs stay under **$11** with Gemini 2.0 Flash. Hosting on Vercel is **free** at this traffic level.

The total budget needed for a full year of production-grade operation — including persistent storage, monitoring, and a mid-tier AI model — is approximately **₹3,500–₹12,000/year** depending on the choices made.

---

## 2. What the System Does

Students walk into the BAKER Lab. Each apparatus has a QR code printed on a label. Scanning it opens a web page with:

- A carousel of photographs of that specific apparatus
- An audio narration explaining what it measures and how it works
- An AI chatbot that answers questions in the context of that particular experiment

Separately, an admin panel (hidden URL, token-authenticated) lets the lab instructor update experiment data, swap the AI key, and manage content without touching code.

The system currently has **6 experiments** configured:
- Dead Weight Tester (BKR-01 through BKR-06 range)
- Instruments covering pressure calibration, dead weight testing, and related metrology apparatus

---

## 3. Current Technical Architecture

```
Browser (Student's Phone or Lab PC)
         │
         ▼
    Vercel CDN  ─────────────────────────────────────────────
    (Static Files)                                           │
    index.html                                               │
    style.css                                                │
    app.js                                                   │
    public/audio/*.mp3                                       │
    public/images/*.jpeg                                     │
         │                                                   │
         │  HTTP/JSON                                        │
         ▼                                                   │
    Vercel Serverless Function (api/main.py)                 │
    ┌────────────────────────────────────────┐               │
    │  GET  /api/experiments                 │               │
    │  GET  /api/experiments/{id}            │               │
    │  POST /api/chat          ──────────────┼──► Gemini API │
    │  GET  /api/admin/settings (auth)       │               │
    │  POST /api/admin/update  (auth)        │               │
    └────────────────────────────────────────┘               │
         │                                                   │
    data/exps.json  (experiment content)                     │
    data/settings.json  (API key override)                   │
    .env  (GKEY, ADMIN_TOKEN)                                │
```

**Stack summary:**

| Layer      | Technology                        | Version / Notes                    |
|------------|-----------------------------------|------------------------------------|
| Frontend   | HTML5, CSS3, Vanilla JavaScript   | Material 3 Expressive design       |
| Backend    | Python + FastAPI                  | 3.10+, serverless function         |
| AI Model   | Google Gemini 2.0 Flash           | `gemini-2.0-flash` via REST API    |
| AI Library | LangChain + FAISS                 | RAG with MMR retrieval             |
| Hosting    | Vercel                            | Hobby tier (free)                  |
| Audio      | gTTS (Google Text-to-Speech)      | Pre-generated MP3, served static   |
| Admin      | Token-authenticated HTML page     | Hidden URL `/secret-admin-portal`  |

**Known architectural limitation:** Vercel's serverless filesystem is read-only at runtime. Admin changes (experiment data, API key) made through the portal do not survive a redeploy. This is fine for a POC but must be solved before production use.

---

## 4. Traffic & Usage Model

All cost calculations use two scenarios.

### 4.1 Normal / Expected Case

| Metric                        | Assumption                          | Value                   |
|-------------------------------|-------------------------------------|-------------------------|
| Daily visitors                | Given                               | 120                     |
| % who use the chatbot         | ~45% (lab sessions, not all browse) | 54 sessions/day         |
| Messages per chat session     | Average 4 messages                  | 216 messages/day        |
| Input tokens per message      | System prompt + context + question  | ~600 tokens             |
| Output tokens per message     | Educational explanation             | ~250 tokens             |
| **Monthly input tokens**      | 6,480 msgs × 600                   | **~3.9M tokens**        |
| **Monthly output tokens**     | 6,480 msgs × 250                   | **~1.6M tokens**        |

### 4.2 Worst Case

| Metric                        | Assumption                          | Value                   |
|-------------------------------|-------------------------------------|-------------------------|
| Daily visitors                | Given                               | 120                     |
| % who use the chatbot         | 100% (exam week, intensive use)     | 120 sessions/day        |
| Messages per chat session     | 10 messages (deep study sessions)   | 1,200 messages/day      |
| Input tokens per message      | Longer history + more context       | ~800 tokens             |
| Output tokens per message     | Detailed, multi-step answers        | ~500 tokens             |
| **Monthly input tokens**      | 36,000 msgs × 800                  | **~28.8M tokens**       |
| **Monthly output tokens**     | 36,000 msgs × 500                  | **~18M tokens**         |

---

## 5. AI Provider Pricing — All Models

Prices are in USD per **1 million tokens** (both input and output). All figures are as of **April 2026**.

---

### 5.1 Google Gemini

Google's pricing is the most competitive for educational use. The free tier on Gemini 2.0 Flash (1,500 requests/day) means the normal case scenario costs literally zero.

| Model                   | Input $/M  | Output $/M | Notes                                           |
|-------------------------|------------|------------|-------------------------------------------------|
| Gemini 2.5 Pro          | $1.25      | $10.00     | Best reasoning. 1M context window.             |
| Gemini 2.5 Flash        | $0.15      | $0.60      | Fast, cheap, strong. Good for lab Q&A.         |
| Gemini 2.5 Flash (thinking) | $0.15  | $3.50      | Activates chain-of-thought reasoning.           |
| **Gemini 2.0 Flash** ← current | **$0.10** | **$0.40** | **Free: 1,500 req/day. Current model.** |
| Gemini 2.0 Flash Lite   | $0.075     | $0.30      | Lighter version. Good for simple Q&A.          |
| Gemini 1.5 Pro          | $1.25      | $5.00      | Previous generation pro model.                 |
| Gemini 1.5 Flash        | $0.075     | $0.30      | Solid for factual Q&A tasks.                   |
| Gemini 1.5 Flash-8B     | $0.0375    | $0.15      | Cheapest option. Weaker on complex topics.     |

> **Free tier detail:** Gemini 2.0 Flash allows 1,500 free requests/day and 1M free tokens/minute. The normal case generates 216 messages/day — well within the free tier. For a college lab, this may stay free indefinitely at normal usage.

---

### 5.2 OpenAI / ChatGPT

OpenAI has more models at various price-performance tradeoffs. GPT-4.1 (released April 2025) is currently the flagship production model.

| Model           | Input $/M  | Output $/M | Notes                                                    |
|-----------------|------------|------------|----------------------------------------------------------|
| o1              | $15.00     | $60.00     | Deep reasoning. Overkill for lab Q&A.                   |
| o3              | $10.00     | $40.00     | Advanced reasoning. Very expensive.                     |
| GPT-4o          | $2.50      | $10.00     | Multimodal. Strong. Previous flagship.                  |
| GPT-4.1         | $2.00      | $8.00      | Current flagship. 1M context window.                    |
| o4-mini         | $1.10      | $4.40      | Reasoning model, cost-optimized.                        |
| GPT-4.1 mini    | $0.40      | $1.60      | Good balance of quality and cost.                       |
| GPT-4o mini     | $0.15      | $0.60      | Fast and cheap. Comparable to Gemini 2.5 Flash pricing. |
| GPT-4.1 nano    | $0.10      | $0.40      | Fastest, cheapest GPT option.                           |

> **Note on reasoning models (o1, o3, o4-mini):** These think before responding. Good for engineering problem-solving, but excessive for a chatbot that answers "what does a Dead Weight Tester measure?" Adds latency (5–30 seconds) and cost.

---

### 5.3 Anthropic / Claude

Anthropic's Claude family offers some of the strongest instruction-following and context-handling, which matters for experiment-specific Q&A with structured data.

| Model                   | Input $/M  | Output $/M | Notes                                              |
|-------------------------|------------|------------|----------------------------------------------------|
| Claude Opus 4.6         | $15.00     | $75.00     | Most capable. Extended thinking available.        |
| Claude 3 Opus           | $15.00     | $75.00     | Previous Opus generation. Same price.             |
| Claude Sonnet 4.6       | $3.00      | $15.00     | Strong, fast, practical for most tasks.           |
| Claude 3.5 Sonnet       | $3.00      | $15.00     | Previous Sonnet generation. Same price.           |
| Claude Haiku 4.5        | $0.80      | $4.00      | Fast, cheap. Good for structured Q&A.             |
| Claude 3.5 Haiku        | $0.80      | $4.00      | Previous Haiku generation. Same price.            |
| Claude 3 Haiku          | $0.25      | $1.25      | Cheapest Claude option. Older generation.         |

> **Note:** Anthropic does not have a public free tier for API access. Claude is the most expensive at the premium end ($75/M output for Opus 4.6) and competitive at the budget end with Claude 3 Haiku ($1.25/M output).

---

## 6. Monthly AI Cost Estimates

All figures in **USD/month**. Rows are sorted cheapest to most expensive within each provider.

### 6.1 Normal Case (~3.9M input tokens, ~1.6M output tokens/month)

#### Google Gemini

| Model                    | Monthly Cost | Notes                                              |
|--------------------------|--------------|----------------------------------------------------|
| Gemini 2.0 Flash (free)  | **$0.00**    | 1,500 req/day free. Normal use stays in free tier. |
| Gemini 1.5 Flash-8B      | **$0.39**    | Cheapest paid option. Quality is limited.          |
| Gemini 2.0 Flash Lite    | **$0.77**    | Slightly better than 8B. Good default.             |
| Gemini 1.5 Flash         | **$0.77**    | Same price as Flash Lite, similar quality.         |
| **Gemini 2.0 Flash** ← current | **$1.03** | Slightly above free tier. Best value.          |
| Gemini 2.5 Flash         | **$1.55**    | Noticeably better reasoning than 2.0 Flash.       |
| Gemini 2.5 Flash thinking | **$6.19**   | Overkill for simple lab Q&A.                      |
| Gemini 1.5 Pro           | **$12.88**   | Older pro model. Outclassed by 2.5 Flash.         |
| Gemini 2.5 Pro           | **$20.88**   | Best quality available. Output cost is steep.     |

#### OpenAI / ChatGPT

| Model           | Monthly Cost | Notes                                               |
|-----------------|--------------|-----------------------------------------------------|
| GPT-4.1 nano    | **$1.03**    | Cheapest. Response quality may feel thin.          |
| GPT-4o mini     | **$1.55**    | Solid for basic Q&A. Good ChatGPT budget option.   |
| GPT-4.1 mini    | **$4.12**    | Better quality than nano. Reasonable for education.|
| o4-mini         | **$11.33**   | Reasoning model. Unnecessary for this use case.   |
| GPT-4.1         | **$20.60**   | Flagship model. Comparable to Gemini 2.5 Pro cost.|
| GPT-4o          | **$25.75**   | Previous flagship. Outclassed by 4.1.             |
| o3              | **$103.00**  | Extremely expensive for a lab chatbot.            |
| o1              | **$154.50**  | Highest quality reasoning. Far too expensive.     |

#### Anthropic / Claude

| Model               | Monthly Cost | Notes                                               |
|---------------------|--------------|-----------------------------------------------------|
| Claude 3 Haiku      | **$2.98**    | Cheapest Claude. Older but capable for Q&A.        |
| Claude Haiku 4.5    | **$9.52**    | Current-gen Haiku. Better quality than 3 Haiku.   |
| Claude 3.5 Haiku    | **$9.52**    | Same price as Haiku 4.5. Previous generation.     |
| Claude Sonnet 4.6   | **$35.70**   | Strong all-rounder. Expensive for a lab chatbot.  |
| Claude 3.5 Sonnet   | **$35.70**   | Same price as Sonnet 4.6.                         |
| Claude Opus 4.6     | **$178.50**  | Most capable. Not justified for student Q&A.      |
| Claude 3 Opus       | **$178.50**  | Same price. Previous generation.                  |

---

### 6.2 Worst Case (~28.8M input tokens, ~18M output tokens/month)

#### Google Gemini

| Model                    | Monthly Cost  | Notes                                       |
|--------------------------|---------------|---------------------------------------------|
| Gemini 1.5 Flash-8B      | **$3.78**     | Still very cheap even under load.           |
| Gemini 2.0 Flash Lite    | **$7.56**     |                                             |
| Gemini 1.5 Flash         | **$7.56**     |                                             |
| **Gemini 2.0 Flash** ← current | **$10.08** | Under $11 even in worst case.          |
| Gemini 2.5 Flash         | **$15.12**    | Manageable. Noticeably better quality.     |
| Gemini 2.5 Flash thinking | **$67.32**   | Thinking tokens get expensive at scale.    |
| Gemini 1.5 Pro           | **$126.00**   |                                             |
| Gemini 2.5 Pro           | **$216.00**   | $216/month for a college lab is high.      |

#### OpenAI / ChatGPT

| Model           | Monthly Cost  | Notes                                          |
|-----------------|---------------|------------------------------------------------|
| GPT-4.1 nano    | **$10.08**    | Cheapest OpenAI option under load.            |
| GPT-4o mini     | **$15.12**    | Reasonable.                                   |
| GPT-4.1 mini    | **$40.32**    | Gets expensive fast at high volume.           |
| o4-mini         | **$110.88**   | Reasoning models become cost-prohibitive.     |
| GPT-4.1         | **$201.60**   |                                               |
| GPT-4o          | **$252.00**   |                                               |
| o3              | **$1,008.00** | Budget-breaking at scale.                    |
| o1              | **$1,512.00** | Not viable for a college budget.             |

#### Anthropic / Claude

| Model               | Monthly Cost  | Notes                                          |
|---------------------|---------------|------------------------------------------------|
| Claude 3 Haiku      | **$29.70**    | Cheapest Claude at scale.                     |
| Claude Haiku 4.5    | **$95.04**    | Approaches ₹8,000/month in worst case.       |
| Claude 3.5 Haiku    | **$95.04**    | Same as above.                                |
| Claude Sonnet 4.6   | **$356.40**   | Not practical for a student lab at this scale.|
| Claude 3.5 Sonnet   | **$356.40**   |                                               |
| Claude Opus 4.6     | **$1,782.00** | Extreme cost. Not applicable here.           |
| Claude 3 Opus       | **$1,782.00** |                                               |

---

## 7. Deployment Options & Hosting Costs

These are the costs for running the FastAPI backend and serving the static frontend. AI costs above are separate.

### 7.1 Option A — Vercel (Current, Recommended)

| Tier   | Monthly Cost | Limits                                            | Verdict                              |
|--------|--------------|---------------------------------------------------|--------------------------------------|
| Hobby  | **$0**       | 100GB bandwidth, 100GB-Hours serverless           | Sufficient for 120 visitors/day      |
| Pro    | **$20**      | 1TB bandwidth, team access, password protection   | Only needed if multiple devs deploy  |

For 120 visitors/day: ~3,600 requests/month to the API. Vercel Hobby tier allows hundreds of thousands of function invocations/month. This site fits comfortably at $0.

**What Vercel gives you for free:**
- Global CDN for static files (fast loads anywhere in India)
- Automatic HTTPS
- Zero-config deployments from Git
- Serverless Python functions (the FastAPI backend)
- Custom domains

**Vercel's one real limitation:** The filesystem is read-only during function execution. Any data written by the admin panel at runtime disappears on the next cold start or redeploy. Fix: use a free external database (see Section 9).

---

### 7.2 Option B — Railway

| Plan    | Monthly Cost | Compute                  | Notes                                     |
|---------|--------------|--------------------------|-------------------------------------------|
| Hobby   | **$5**       | Shared, ~512MB RAM       | Includes $5 compute credit                |
| Pro     | **$20+**     | Dedicated, scales up     | Overkill for this use case                |

Railway runs the FastAPI server as a persistent process (unlike Vercel's serverless). Better for complex backends. Not needed here unless the LangChain + FAISS setup requires persistent in-memory state.

---

### 7.3 Option C — Render

| Plan             | Monthly Cost | Notes                                           |
|------------------|--------------|-------------------------------------------------|
| Free             | **$0**       | Spins down after 15 min. Bad for students.     |
| Starter (always-on) | **$7**    | 512MB RAM, 0.5 CPU. Enough for this workload.  |
| Standard         | **$25**      | 1GB RAM, 1 CPU. More headroom.                 |

The free tier is unsuitable — students scanning a QR code will hit a 30-second cold start, which breaks the experience. Starter at $7 is fine.

---

### 7.4 Option D — Digital Ocean

| Plan                    | Monthly Cost | Notes                                      |
|-------------------------|--------------|--------------------------------------------|
| App Platform Basic      | **$5**       | 512MB RAM, 1 vCPU                          |
| App Platform Pro        | **$12**      | 1GB RAM, 1 vCPU                            |
| Droplet (VPS, 1GB RAM)  | **$6**       | More control, requires manual server setup |

Clean pricing. The App Platform is the managed equivalent to Railway. Good option if the college prefers a non-US vendor relationship.

---

### 7.5 Option E — AWS

| Service                         | Monthly Cost     | Notes                                         |
|---------------------------------|------------------|-----------------------------------------------|
| Lambda + API Gateway            | **~$0.10**       | Pay per invocation. 18k reqs/month ≈ free.    |
| EC2 t3.micro (on-demand)        | **~$8.47**       | 1 vCPU, 1GB RAM.                             |
| EC2 t3.micro (1-yr reserved)    | **~$5.50**       | Commit for a year, save 35%.                 |
| EC2 t3.small (on-demand)        | **~$16.94**      | More RAM for the LangChain/FAISS workload.   |
| S3 (static file hosting)        | **~$0.50**       | Negligible for audio/image assets.           |

AWS Lambda is technically the cheapest option for 120 visitors/day, but the setup complexity — IAM roles, API Gateway config, S3 buckets — adds significant overhead that isn't worth it for a college project.

---

### 7.6 Option F — Google Cloud

| Service              | Monthly Cost | Notes                                              |
|----------------------|--------------|----------------------------------------------------|
| Cloud Run (serverless) | **$0**     | 2M req/month free. Scales to zero. Ideal.          |
| App Engine Standard  | **~$0–$5**   | Similar free tier, more managed.                   |
| Compute Engine e2-micro | **~$6.11** | Shared-core VM. May struggle with FAISS in memory. |

Google Cloud Run is a strong alternative to Vercel if there's already a Google Cloud account for the Gemini API. The free tier covers this traffic comfortably.

---

### 7.7 Option G — Azure

| Service                     | Monthly Cost | Notes                                        |
|-----------------------------|--------------|----------------------------------------------|
| Azure Container Apps        | **~$0–$3**   | Serverless containers. Generous free tier.  |
| App Service B1              | **~$13.14**  | Always-on, 1 Core, 1.75GB RAM.             |

Azure is the most expensive mid-tier option. Not recommended unless the institution has an existing Azure campus license.

---

### 7.8 Add-On Services (Production Setup)

These are free or near-free and needed for a production deployment:

| Service              | Use Case                        | Cost                         |
|----------------------|---------------------------------|------------------------------|
| MongoDB Atlas Free   | Persistent experiment data      | **$0** (512MB free forever)  |
| Vercel KV            | Redis-based key/value store     | **$0** (30MB, 30k req/month) |
| Cloudinary Free      | CDN for audio and images        | **$0** (25GB/month free)     |
| Sentry Free          | Error tracking and monitoring   | **$0** (5,000 events/month)  |
| UptimeRobot Free     | Uptime monitoring, alerts       | **$0** (50 monitors free)    |
| Cloudflare Free      | DDoS protection, edge caching   | **$0**                       |

---

## 8. Total Cost of Ownership: Three Scenarios

Costs per month in USD. Hosting + AI + Add-ons. Annual total in INR at ₹84/USD.

---

### 8.1 Cheapest Option — Free Tier Everything

**Setup:** Vercel Hobby (free) + Gemini 2.0 Flash (free tier) + MongoDB Atlas Free

| Component         | Monthly Cost |
|-------------------|--------------|
| Hosting (Vercel)  | $0.00        |
| AI (Gemini 2.0 Flash free) | $0.00 |
| Database (MongoDB Atlas) | $0.00 |
| Monitoring (UptimeRobot) | $0.00 |
| CDN (Cloudinary)  | $0.00        |
| **Total**         | **$0.00**    |

**Annual cost (INR):** ₹0

**What you get:** Fully functional lab assistant at zero recurring cost. The 1,500 free req/day on Gemini 2.0 Flash covers the normal case comfortably (216 messages/day). The only risk is that free tiers can change their limits, and if usage spikes beyond 1,500 req/day, there's no billing buffer.

**Best for:** Pilot semester, proof of concept, budget-constrained setup.

**Risk:** If the college gets featured, goes viral internally, or runs an intensive workshop, traffic could spike above the free tier in a single day.

---

### 8.2 Medium Option — Paid Hosting, Smart AI Choice

**Setup:** Vercel Pro ($20/month) + Gemini 2.5 Flash (paid, better quality) + MongoDB Atlas Free

| Component              | Monthly Cost |
|------------------------|--------------|
| Hosting (Vercel Pro)   | $20.00       |
| AI (Gemini 2.5 Flash) — normal case | $1.55 |
| AI (Gemini 2.5 Flash) — worst case buffer | +$15 max |
| Database (MongoDB Atlas) | $0.00      |
| Monitoring + CDN       | $0.00        |
| **Total (normal)**     | **$21.55**   |
| **Total (worst case)** | **$35.00**   |

**Annual cost (INR):**  
- Normal: ~₹21,700  
- Worst case: ~₹35,300

**What you get:** Team deployment access, more serverless compute headroom, better AI quality than 2.0 Flash, and a small cost buffer for heavy usage. Gemini 2.5 Flash gives noticeably better answers for technical engineering topics.

**Best for:** Full academic year deployment with faculty oversight and multiple administrators.

---

### 8.3 Most Expensive Option — Premium Everything

**Setup:** Vercel Pro ($20/month) + GPT-4.1 or Claude Sonnet 4.6 (best quality) + paid database + monitoring

| Component                  | Monthly Cost |
|----------------------------|--------------|
| Hosting (Vercel Pro)       | $20.00       |
| AI (GPT-4.1) — normal case | $20.60       |
| AI (GPT-4.1) — worst case  | $201.60 max  |
| MongoDB Atlas M10 (paid)   | $57.00       |
| Sentry Team                | $26.00       |
| **Total (normal)**         | **$123.60**  |
| **Total (worst case)**     | **~$305.00** |

**Annual cost (INR):**  
- Normal: ~₹1,24,600  
- Worst case: ~₹3,07,700

**What you get:** GPT-4.1's 1M context window, stronger multilingual handling, a properly indexed production database, and full error monitoring. This setup would be appropriate if the system scales to multiple labs across the college.

**Best for:** Institution-wide deployment covering 10+ labs, multiple departments, concurrent maintenance by a team.

---

### 8.4 Side-by-Side Summary

| Scenario     | Monthly (Normal) | Monthly (Worst) | Annual INR (Normal) | Annual INR (Worst) |
|--------------|-----------------|-----------------|---------------------|--------------------|
| **Cheapest** | **$0**          | **$10.08**      | **₹0**              | **₹10,160**        |
| **Medium**   | **$21.55**      | **$35.00**      | **₹21,700**         | **₹35,300**        |
| **Premium**  | **$123.60**     | **~$305**       | **₹1,24,600**       | **₹3,07,700**      |

---

## 9. Production Readiness Gap Analysis

The current POC works and is deployable today. These are the gaps between "it works" and "it's ready for 120 daily students all year."

### 9.1 Critical (Must Fix Before Full Launch)

| Gap                             | Problem                                                              | Fix                                              | Cost    |
|---------------------------------|----------------------------------------------------------------------|--------------------------------------------------|---------|
| Read-only filesystem on Vercel  | Admin changes to experiment data don't survive redeploy              | Migrate exps.json to MongoDB Atlas or Vercel KV  | $0      |
| No rate limiting on /api/chat   | A single student could spam the chatbot and exhaust API quota        | Add IP-based rate limit (10 req/min)             | $0      |
| No error monitoring             | If Gemini goes down or a bug hits production, nobody knows           | Add Sentry free tier                             | $0      |
| Admin token is static           | The ADMIN_TOKEN in environment variables never rotates               | Document rotation procedure; use long random key | $0      |

### 9.2 Important (Fix Within First Month)

| Gap                             | Problem                                                              | Fix                                              | Cost    |
|---------------------------------|----------------------------------------------------------------------|--------------------------------------------------|---------|
| Audio files in the repo         | Large MP3s slow down deployments and eat Git storage                 | Move to Cloudinary or similar CDN                | $0      |
| No usage analytics              | Can't tell which experiments get used, which chatbot questions recur | Add Google Analytics 4 or Plausible              | $0      |
| Single AI provider, no fallback | If Gemini's API is down, the chat silently fails                     | Add retry logic and a user-facing error message  | $0      |
| No input length validation      | Very long student inputs could inflate token usage unexpectedly      | Cap input at 500 characters on frontend + backend | $0     |

### 9.3 Nice to Have (Before Second Semester)

| Gap                             | Problem                                                              | Fix                                              | Cost    |
|---------------------------------|----------------------------------------------------------------------|--------------------------------------------------|---------|
| No chat history persistence     | Students can't pick up a previous conversation                       | Store sessions in MongoDB with session ID        | $0      |
| Audio regeneration is manual    | Adding a new experiment requires running a local Python script       | Trigger gTTS generation from the Admin panel     | $0      |
| No multi-lab support in UI      | Knowledge base supports multiple labs but the UI only shows BAKER    | Add lab selector to the main page                | Dev time|
| No offline support              | No internet = no site for students with poor connectivity in lab     | Add a basic service worker for offline caching   | Dev time|

### 9.4 Production Readiness Score

| Area                  | Current State | Production-Ready Target |
|-----------------------|---------------|-------------------------|
| Functionality         | 8/10          | 9/10                    |
| Data persistence      | 3/10          | 9/10 (add DB)           |
| Security              | 6/10          | 8/10 (add rate limiting)|
| Monitoring            | 2/10          | 8/10 (add Sentry)       |
| Reliability           | 7/10          | 9/10 (add fallback msg) |
| Scalability           | 8/10          | 9/10                    |
| **Overall**           | **5.7/10**    | **8.7/10**              |

The gaps are all solvable without spending money and without major architectural changes. Estimated development time to close all critical and important gaps: **2–3 days of focused work**.

---

## 10. Recommended Path Forward

### For a one-semester pilot (Budget: ₹0)

1. Add MongoDB Atlas Free for persistent admin data
2. Add IP-rate limiting to `/api/chat`
3. Add Sentry free tier for error visibility
4. Keep Gemini 2.0 Flash — it's within the free tier at normal usage
5. Deploy on Vercel Hobby — zero cost, zero configuration

**Total cost: ₹0/month.** The free tiers on all services cover this traffic level.

### For a full academic year deployment (Budget: ₹2,000–₹5,000/month)

1. Switch to Gemini 2.5 Flash — better answers for engineering concepts, minimal cost increase
2. Upgrade to Vercel Pro if the lab has more than one developer — adds team access and deployment protections
3. Add all production readiness fixes in Section 9
4. Set a monthly API spend cap of $20 in Google Cloud Console to prevent runaway costs

**Total cost: ~$1–22/month depending on AI tier chosen.**

### AI Model Recommendation (by priority for a college lab)

| Priority          | Model                       | Reason                                          |
|-------------------|-----------------------------|-------------------------------------------------|
| Best for ₹0 budget | Gemini 2.0 Flash (free tier) | Free up to 1,500 req/day. Currently in use.    |
| Best value paid    | Gemini 2.5 Flash            | Meaningfully better answers, $1.55/month normal|
| Best quality paid  | GPT-4.1 mini                | Strong, multilingual, $4.12/month normal case  |
| If budget allows   | GPT-4.1 or Gemini 2.5 Pro  | Best answers for complex metrology questions   |
| Avoid for this use | o1, o3, Claude Opus         | Expensive reasoning models. Overkill here.     |

---

## 11. Appendix: Pricing Methodology

### Token Calculation Basis

Each chat message sent by a student goes through this pipeline:

```
System prompt (what the AI is told it is)       ~150 tokens
Experiment context (JSON data for that expt.)   ~200 tokens  
Chat history (last 3 turns, window memory)      ~150 tokens
Student's question                              ~100 tokens
─────────────────────────────────────────────────────────
Total input per message                         ~600 tokens

AI's response (educational explanation)         ~250 tokens
```

### Free Tier Limits Reference (April 2026)

| Provider         | Free Tier                                       |
|------------------|-------------------------------------------------|
| Google Gemini    | 2.0 Flash: 1,500 req/day, 1M tokens/min        |
| OpenAI           | No API free tier. $5 trial credit for new accounts |
| Anthropic        | No API free tier                               |
| Vercel           | 100GB bandwidth/month, 100GB-Hours serverless  |
| MongoDB Atlas    | 512MB storage, shared cluster, forever free    |
| Cloudinary       | 25GB storage + 25GB bandwidth/month free       |
| Sentry           | 5,000 error events/month free                  |
| UptimeRobot      | 50 monitors, 5-min check interval free         |

### Currency Conversion

All figures in USD converted at **₹84 = $1** (approximate April 2026 rate). Final INR figures should be verified against current exchange rates at time of budget submission.

---

*Document prepared April 12, 2026. Pricing reflects published API rates as of this date. AI provider pricing changes frequently — verify at each provider's pricing page before finalizing a budget proposal.*
