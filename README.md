LearnPal – Execution-Ready Project Plan (Multi-Tenant SaaS · July 2025 MVP)

1 · Vision & Non-negotiables
Pillar
Definition
Outcome
A cloud-hosted, voice-plus-text AI tutor that any parent/teacher can use to create unlimited child profiles (“learners”) and track their personalised progress.
Pedagogy
Zone of Proximal Development · Spaced Repetition · Interleaved Practice · Metacognition · Growth-Mindset feedback.
Safety
COPPA / GDPR-K compliance, explicit parental consent per learner, OpenAI Moderation filter before speech output, no secrets in repo.
Modularity
Every sprint ships an isolated, testable slice; no sprint depends on future emotion-AI or vision features.
Low-friction UX
Voice first with instant text fallback; child login in one tap; parent dashboard for oversight.


2 · Feature Set for MVP (8-week runway)
Category
Must-have features
Accounts & Tenancy
• Multi-tenant SaaS: each tenant = one family or classroom.
• Parent (user) can add any number of learners.
• JWT auth via Supabase.
Consent & Compliance
COPPA consent wizard per learner; data-processing notice.
Tutoring Loop
• Voice ↔ text chat with GPT-4o-mini.
• Age-appropriate system prompts pulled from learner profile.
• Item bank JSON (20 math items for early elementary, 20 reading comprehension items for upper elementary).
Adaptive Logic
Rolling %-correct mastery model (≥80 % over last 10 attempts ⇒ concept mastered).
Safety Layer
Moderation API check of every LLM reply; if flagged, safe fallback response.
Fallback & Resilience
Seamless switch to text input if STT fails twice within 10 s.
Motivation
Badges & XP tied to mastery milestones (not time-on-task).
Parent Dashboard
Heat-map progress per learner, badge log, CSV export.


3 · System Architecture (MVP)
mermaid
CopyEdit
graph TD
    subgraph Browser / PWA
        A[Mic / Text Box] -->|voice| WS((WebSocket))
        WS -->|text| API[/FastAPI/]
        API --> WS
        WS -->|audio| A
    end

    API --> Engine[engine.py<br>adaptive + prompt]
    Engine -->|invoke| GPT[(GPT-4o-mini)]
    Engine -->|moderate| MOD[Moderation API]
    Engine -->|SQL| DB[(PostgreSQL)]
    API --> DB
    API <-->|JWT| Auth[Supabase]

    classDef infra fill:#fafafa,stroke:#bbb;
    class DB,GPT,MOD,Auth infra;


Key Tech Choices
Layer
Stack / Rationale
Frontend
React + Vite → fast dev, installs as PWA.
Voice
Web Speech API mic stream → /api/stt (local Whisper tiny) · TTS via Edge/ElevenLabs.
API
FastAPI + Pydantic.
DB
PostgreSQL (row-level tenant_id security).
Hosting
Docker-compose → Fly.io or Render (TLS + autoscale).


4 · Data Model
sql
CopyEdit
tenants(id, name, plan)                          -- one per family/class
users(id, tenant_id, email, pw_hash, role)       -- parent / admin
learners(id, tenant_id, name, dob, persona_json) -- many per tenant
concepts(id, grade, domain, label)               -- math/reading concepts
items(id, concept_id, json_blob)                 -- prompt + answers
progress(learner_id, concept_id, correct, attempts, last_seen)
badges(id, learner_id, type, awarded_at)

persona_json keys: voice, tone_style, reading_level, math_level, emoji.

5 · Sprint Roadmap
Sprint
Deliverable
Lead files
Definition-of-Done
0 – Scaffold
Repo structure, Docker, CI (pytest)
docker-compose.yml, GitHub Action
Containers build & “hello world” test passes.
1 – Auth & Tenancy
Supabase JWT auth, tenants, users, learners CRUD
auth.py, models.py
Parent can sign up, add learner profile.
2 – Consent & Dashboard v0
COPPA form & consent flag; parent list of learners
consent.vue, /api/consent
Learner locked until consent given.
3 – Voice + Text I/O
Voice bridge, STT endpoint, TTS streaming
voice.js, stt.py, tts.py
Child hears echo bot round-trip < 2 s; text fallback works.
4 – Tutoring Engine & Item Bank
engine.py, items.json (40 starter Qs)
Accuracy tracked; engine selects next item.


5 – Mastery & Badges
Badge service, XP bar UI
badge.py, child.vue
Badge awarded on first mastered concept.
6 – Safety Layer
moderation.py filter + retry logic
Any flagged output replaced with template; tests stub flagged case.


7 – Parent Heat-map
/api/progress, parent.vue chart, CSV
Shows %-correct per concept per learner.


8 – Pilot + Hardening
Real sessions with at least 2 learners; load + security tests
—
20-min runs without critical errors; LAT ≤ 250 ms 95th percentile.


6 · Token & Cost Guardrails
Max tokens: 150 per tutor reply, 60 per hint.


Context window: last 12 messages or 2 k tokens.


Cost alert email if monthly usage > $25/tenant.



7 · Safety & Privacy Checklist
No voice files stored after STT; discard raw audio buffer.


PII limited to learner first-name & DOB month/year.


Parental controls: delete learner, export data, revoke consent.


OpenAI Moderation → fallback templates only (no raw flagged content).


No secret keys in repo; .env + Render secrets store.



8 · Post-MVP Backlog (priority order)
Bayesian mastery model (Knowledge Tracing).


Explain-back checks (structured “teach me” prompts).


Sibling co-op quests.


Emotion/engagement sensing v1 (explicit emoji + latency).


Native Flutter shell for offline mode & app-store reach.



9 · Immediate Next Steps
You: push scaffold (backend/app/main.py empty FastAPI, frontend/ Vite init) to https://github.com/rsm0508/learnpal.


Me: provide patch for Sprint 0 (models.py, CI config).


Start Sprint 1 Monday; daily commits + “pushed” ping for reviews.



This plan incorporates unlimited learner personas per tenant while keeping the MVP lean, safe, and testable. We can now begin coding.

