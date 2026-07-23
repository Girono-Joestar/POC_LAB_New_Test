# AI-Powered Laboratory Assistant
## Proposal for BAKER Metrology Lab — MES College of Engineering, Pune
**Date:** April 12, 2026  
**Prepared by:** POC AI Lab Team  
**Target Traffic:** 120 visitors/day  

---

## What This System Does

Students scan a QR code placed next to any lab apparatus and land on a page with photographs of the equipment, an audio narration, and an AI chatbot that answers questions specific to that experiment — no login, no app install, just a QR scan.

The lab instructor manages everything through a private admin panel: update experiment descriptions, swap the AI key, or add new equipment without touching any code.

---

## Current Setup (As of April 12, 2026)

| Component     | Technology                    |
|---------------|-------------------------------|
| Frontend      | HTML, CSS, JavaScript         |
| Backend       | Python (FastAPI)              |
| AI Model      | Google Gemini 2.0 Flash       |
| Hosting       | Vercel (free tier)            |
| Experiments   | 6 BAKER Lab apparatus         |

The system is live and functional. Six experiments are configured. The site works on mobile and desktop.

---

## Traffic & Usage Assumptions

| Scenario      | Visitors/Day | Chat Sessions/Day | Messages/Day | Monthly Tokens (In / Out)   |
|---------------|--------------|--------------------|--------------|------------------------------|
| Normal        | 120          | 54 (45%)           | 216          | 3.9M input / 1.6M output     |
| Worst Case    | 120          | 120 (100%)         | 1,200        | 28.8M input / 18M output     |

> **Normal case** assumes 45% of visitors use the chatbot, averaging 4 messages each.  
> **Worst case** assumes every visitor uses it heavily — exam week, workshop days, intensive sessions.

---

## AI Model Pricing — All Providers (April 2026)

Prices in USD per 1 million tokens.

### Google Gemini

| Model                         | Input $/M | Output $/M | Free Tier                        |
|-------------------------------|-----------|------------|----------------------------------|
| Gemini 1.5 Flash-8B           | $0.0375   | $0.15      | None                             |
| Gemini 2.0 Flash Lite         | $0.075    | $0.30      | None                             |
| Gemini 1.5 Flash              | $0.075    | $0.30      | None                             |
| **Gemini 2.0 Flash** ← in use | **$0.10** | **$0.40**  | **1,500 req/day free**           |
| Gemini 2.5 Flash              | $0.15     | $0.60      | None                             |
| Gemini 2.5 Flash (thinking)   | $0.15     | $3.50      | None                             |
| Gemini 1.5 Pro                | $1.25     | $5.00      | None                             |
| Gemini 2.5 Pro                | $1.25     | $10.00     | None                             |

### OpenAI / ChatGPT

| Model           | Input $/M | Output $/M | Notes                              |
|-----------------|-----------|------------|------------------------------------|
| GPT-4.1 nano    | $0.10     | $0.40      | Fastest, cheapest                  |
| GPT-4o mini     | $0.15     | $0.60      | Good budget option                 |
| GPT-4.1 mini    | $0.40     | $1.60      | Balanced quality/cost              |
| o4-mini         | $1.10     | $4.40      | Reasoning model                    |
| GPT-4.1         | $2.00     | $8.00      | Current flagship, 1M context       |
| GPT-4o          | $2.50     | $10.00     | Previous flagship                  |
| o3              | $10.00    | $40.00     | Advanced reasoning                 |
| o1              | $15.00    | $60.00     | Deep reasoning, very expensive     |

### Anthropic / Claude

| Model               | Input $/M | Output $/M | Notes                            |
|---------------------|-----------|------------|----------------------------------|
| Claude 3 Haiku      | $0.25     | $1.25      | Older generation, cheapest       |
| Claude Haiku 4.5    | $0.80     | $4.00      | Current fast model               |
| Claude 3.5 Haiku    | $0.80     | $4.00      | Same price as Haiku 4.5          |
| Claude Sonnet 4.6   | $3.00     | $15.00     | Strong all-rounder               |
| Claude 3.5 Sonnet   | $3.00     | $15.00     | Previous Sonnet generation       |
| Claude Opus 4.6     | $15.00    | $75.00     | Most capable, most expensive     |
| Claude 3 Opus       | $15.00    | $75.00     | Previous Opus generation         |

---

## Monthly AI Cost Estimates

### Normal Case (~3.9M input / 1.6M output tokens/month)

| Provider & Model              | Monthly Cost | Recommendation                          |
|-------------------------------|--------------|------------------------------------------|
| Gemini 2.0 Flash (free tier)  | **$0.00**    | Best choice for pilot/zero-budget       |
| Gemini 1.5 Flash-8B           | $0.39        |                                          |
| Gemini 2.0 Flash Lite         | $0.77        |                                          |
| Gemini 2.0 Flash (paid)       | $1.03        | If usage exceeds free tier              |
| GPT-4.1 nano                  | $1.03        |                                          |
| Gemini 2.5 Flash              | $1.55        | Best value upgrade from 2.0 Flash       |
| GPT-4o mini                   | $1.55        |                                          |
| Claude 3 Haiku                | $2.98        |                                          |
| GPT-4.1 mini                  | $4.12        |                                          |
| Gemini 2.5 Flash (thinking)   | $6.19        |                                          |
| Claude Haiku 4.5              | $9.52        |                                          |
| o4-mini                       | $11.33       |                                          |
| Gemini 1.5 Pro                | $12.88       |                                          |
| GPT-4.1                       | $20.60       |                                          |
| Gemini 2.5 Pro                | $20.88       |                                          |
| GPT-4o                        | $25.75       |                                          |
| Claude Sonnet 4.6             | $35.70       |                                          |
| o3                            | $103.00      | Not suitable for this use case          |
| o1                            | $154.50      | Not suitable for this use case          |
| Claude Opus 4.6               | $178.50      | Not suitable for this use case          |

### Worst Case (~28.8M input / 18M output tokens/month)

| Provider & Model              | Monthly Cost  |
|-------------------------------|---------------|
| Gemini 1.5 Flash-8B           | $3.78         |
| Gemini 2.0 Flash Lite         | $7.56         |
| Gemini 1.5 Flash              | $7.56         |
| **Gemini 2.0 Flash** ← in use | **$10.08**    |
| GPT-4.1 nano                  | $10.08        |
| Gemini 2.5 Flash              | $15.12        |
| GPT-4o mini                   | $15.12        |
| Claude 3 Haiku                | $29.70        |
| GPT-4.1 mini                  | $40.32        |
| Gemini 2.5 Flash (thinking)   | $67.32        |
| Claude Haiku 4.5              | $95.04        |
| o4-mini                       | $110.88       |
| Gemini 1.5 Pro                | $126.00       |
| GPT-4.1                       | $201.60       |
| Gemini 2.5 Pro                | $216.00       |
| GPT-4o                        | $252.00       |
| Claude Sonnet 4.6             | $356.40       |
| o3                            | $1,008.00     |
| o1                            | $1,512.00     |
| Claude Opus 4.6               | $1,782.00     |

---

## Deployment Options & Hosting Costs

| Platform              | Monthly Cost | Notes                                                       |
|-----------------------|--------------|-------------------------------------------------------------|
| **Vercel Hobby**      | **$0**       | Current setup. Free tier covers 120 visitors/day easily.   |
| Digital Ocean Basic   | $5           | Good alternative, simple pricing                           |
| Railway Hobby         | $5           | Persistent server process                                  |
| Render Starter        | $7           | Always-on (free tier spins down, not usable for students)  |
| AWS Lambda            | ~$0.10       | Pay-per-request. Complex to set up.                        |
| AWS EC2 t3.micro      | $8.47        | Full virtual machine, more control                         |
| Google Cloud Run      | $0           | 2M free requests/month. Good if using GCP already.        |
| Azure Container Apps  | ~$0–$3       | Free tier available. Higher mid-tier cost than others.     |
| Vercel Pro            | $20          | Adds team access, more serverless headroom                 |

**Recommended:** Stay on **Vercel Hobby ($0)**. It handles this traffic level without any configuration changes.

### Free Add-On Services (All ₹0)

| Service           | Purpose                              |
|-------------------|--------------------------------------|
| MongoDB Atlas Free | Persistent database (512MB free)    |
| Cloudinary Free   | CDN for audio/images (25GB free)    |
| Sentry Free       | Error monitoring (5,000 events/mo)  |
| UptimeRobot Free  | Uptime alerts (50 monitors free)    |

---

## Total Cost of Ownership — Three Scenarios

Exchange rate: ₹84 = $1 (April 2026)

### Option 1 — Cheapest (₹0/year)

| Component                  | Cost       |
|----------------------------|------------|
| Hosting (Vercel Hobby)     | $0/month   |
| AI (Gemini 2.0 Flash free) | $0/month   |
| Database (MongoDB Atlas)   | $0/month   |
| Monitoring & CDN           | $0/month   |
| **Total**                  | **$0/month — ₹0/year** |

Gemini 2.0 Flash's free tier allows 1,500 requests/day. Normal usage (216 messages/day) stays within this limit. If a workshop or exam day spikes usage past 1,500, the extra requests are billed at $0.10/M tokens — a spike of 3× normal use for one day would cost under $0.05.

**Best for:** Pilot semester, trial run, budget approval stage.

---

### Option 2 — Medium (~₹21,700/year normal, ₹35,300/year worst case)

| Component                     | Cost          |
|-------------------------------|---------------|
| Hosting (Vercel Pro)          | $20/month     |
| AI (Gemini 2.5 Flash, normal) | $1.55/month   |
| AI (worst case buffer)        | up to $15/month |
| Database + monitoring         | $0/month      |
| **Total (normal)**            | **~$21.55/month — ₹21,700/year** |
| **Total (worst case)**        | **~$35/month — ₹35,300/year** |

Gemini 2.5 Flash gives noticeably better answers for technical engineering topics compared to 2.0 Flash. Vercel Pro adds team deployment access, which matters if multiple people maintain the system.

**Best for:** Full academic year deployment with faculty sign-off and at least one dedicated maintainer.

---

### Option 3 — Premium (~₹1,24,600/year normal, ₹3,07,700/year worst case)

| Component                  | Cost           |
|----------------------------|----------------|
| Hosting (Vercel Pro)       | $20/month      |
| AI (GPT-4.1, normal)       | $20.60/month   |
| AI (GPT-4.1, worst case)   | $201.60/month  |
| MongoDB Atlas M10          | $57/month      |
| Sentry Team                | $26/month      |
| **Total (normal)**         | **~$123.60/month — ₹1,24,600/year** |
| **Total (worst case)**     | **~$305/month — ₹3,07,700/year** |

GPT-4.1 handles multilingual queries better and has a 1M token context window. This tier makes sense if the system expands to cover 10+ labs across the college.

**Best for:** Multi-department rollout, institution-wide deployment.

---

### Summary

| Option   | Normal (Monthly) | Worst Case (Monthly) | Annual INR (Normal) | Annual INR (Worst) |
|----------|-----------------|----------------------|---------------------|--------------------|
| Cheapest | **$0**          | **~$10**             | **₹0**              | **₹10,000**        |
| Medium   | **~$22**        | **~$35**             | **₹21,700**         | **₹35,300**        |
| Premium  | **~$124**       | **~$305**            | **₹1,24,600**       | **₹3,07,700**      |

---

## What Needs Work Before Full Launch

The current POC is functional. Four things need to be fixed before deploying for a full semester of daily use:

| Priority | Issue                            | Impact                                                     | Fix                                    | Cost |
|----------|----------------------------------|-------------------------------------------------------------|----------------------------------------|------|
| Critical | Admin changes don't persist      | Experiment updates are lost after every redeploy            | Add MongoDB Atlas (free)               | ₹0   |
| Critical | No rate limiting on chatbot      | A single user could exhaust the day's free API quota        | Limit to 10 requests/minute per IP     | ₹0   |
| Critical | No error monitoring              | If the AI goes down, nobody is alerted                      | Add Sentry free tier                   | ₹0   |
| High     | Audio files stored in the repo   | Slows deployments; large Git history over time              | Move to Cloudinary (free)              | ₹0   |

Estimated fix time: **2 days of development work.** No additional budget required.

---

## Recommendation

**For the pilot semester:** Deploy as-is with MongoDB Atlas added for data persistence. Keep Gemini 2.0 Flash on the free tier. Total cost: ₹0.

**For a full year:** Upgrade to Gemini 2.5 Flash and Vercel Pro. Budget ₹22,000–₹35,000 for the year, which covers normal use and worst-case spikes.

**AI model to use:** Gemini 2.5 Flash. It gives meaningfully better answers for metrology and instrumentation topics than the current 2.0 Flash, costs about $1.55/month at normal use, and stays on Google's infrastructure alongside the existing API key.

**Avoid:** Reasoning models (o1, o3, Claude Opus). They think before answering, take 5–30 seconds per response, and cost 10–50x more than what's needed for a student asking "how does a dead weight tester work?"

---

*All pricing as of April 12, 2026. AI provider rates change frequently — confirm at each provider's pricing page before submitting a formal budget.*
