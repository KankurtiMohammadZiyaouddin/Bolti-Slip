# Bolti Slip (बोलती स्लिप)

<div align="center">

![Bolti Slip Banner](https://img.shields.io/badge/Bolti_Slip-बोलती_स्लिप-4F46E5?style=for-the-badge&logoColor=white)

**"जो बोला, वही लिखा। जो लिखा, वही कन्फ़र्म।"**  
*(Jo Bola, Wahi Likha. Jo Likha, Wahi Confirm.)*

### AI-Powered Voice-to-Repair Ticket SaaS for Indian Local Repair Shops

[![Gnani.ai Challenge](https://img.shields.io/badge/Challenge-Gnani.ai_Great_Indian_AI_Internship-8B5CF6?style=flat-square)](https://gnani.ai)
[![Gnani Prisma](https://img.shields.io/badge/Gnani_Prisma-v3.0_STT_(indic--auto)-7C3AED?style=flat-square)](https://vachana.ai)
[![Gnani Timbre](https://img.shields.io/badge/Gnani_Timbre-v3.0_TTS_(Devansh)-6366F1?style=flat-square)](https://vachana.ai)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-v4.0-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![PWA Ready](https://img.shields.io/badge/PWA-Installable_Android-purple?style=flat-square&logo=pwa&logoColor=white)](#key-features)
[![Database](https://img.shields.io/badge/Database-SQLite_%7C_PostgreSQL-336791?style=flat-square&logo=postgresql&logoColor=white)](#key-features)
[![Regression Tests](https://img.shields.io/badge/Tests-156%2B_Passing-emerald?style=flat-square&logo=checkmarx&logoColor=white)](#automated-testing--verification)

[**📄 Solution Pitch (1-Pager)**](SOLUTION_PITCH.md) • [Overview](#the-problem--our-solution) • [Workflow](#how-it-works) • [Features](#key-features) • [Gnani AI Integration](#gnani-ai-integration) • [Architecture](#system-architecture) • [Getting Started](#getting-started) • [Deployment](#production-readiness--deployment)

</div>

> 📄 **Looking for the competition pitch document?**  
> Read the concise executive summary in [**SOLUTION_PITCH.md**](SOLUTION_PITCH.md), designed specifically for Gnani.ai challenge evaluators.

---

## 📋 Project Information

| Attribute | Details |
| :--- | :--- |
| **Project Name** | **Bolti Slip (बोलती स्लिप)** |
| **Challenge** | **Great Indian AI Internship Challenge by Gnani.ai** |
| **Official Tagline** | *"Jo Bola, Wahi Likha. Jo Likha, Wahi Confirm."* |
| **Developer** | **Kankurti Mohammad Ziyaouddin** ([GitHub Profile](https://github.com/KankurtiMohammadZiyaouddin)) |
| **Repository** | [github.com/KankurtiMohammadZiyaouddin/Bolti-Slip](https://github.com/KankurtiMohammadZiyaouddin/Bolti-Slip) |
| **Speech-to-Text (STT)** | **Gnani Prisma v3.0** (`indic-auto`, `codemix`) via `https://api.vachana.ai/stt/v3` |
| **Text-to-Speech (TTS)** | **Gnani Timbre v3.0** (`hi-IN`, Voice: `Devansh`) via `https://api.vachana.ai/api/v1/tts/inference` |
| **Frontend Stack** | React 18, TypeScript, Vite 5, Tailwind CSS v4, Workbox PWA |
| **Backend Stack** | FastAPI (Python 3.10+ / 3.14), Uvicorn, SlowAPI, Pydantic v2 |
| **Database Engines** | Dual-Engine: **SQLite** (Local Dev & Automated Backups) + **Neon PostgreSQL** (Cloud Production) |
| **Verified Execution** | Local: `http://localhost:5173` (Frontend) & `http://127.0.0.1:8000` (Backend API) |
| **Cloud Target** | Deployment-ready configurations prepared for Render (FastAPI) and Neon PostgreSQL |

---

## 💡 The Problem & Our Solution

### The Challenge Faced by Local Repair Shops

India's local electronics, smartphone, and home appliance repair shops operate in fast-paced, high-friction environments:
- **Manual, Fragile Paper Slips:** Shopkeepers write estimates and customer complaints on paper chits that get oil-stained, torn, or misplaced, leading to lost customer records.
- **Typing Friction with Busy Hands:** Technicians frequently handle dirty components, screwdrivers, and soldering irons. Typing customer names, serial numbers, and fault descriptions on tiny touchscreens with busy hands is awkward and slow.
- **Cost and Delivery Date Disputes:** Verbal agreements on repair estimates (*"₹350 me ho jayega"*) or delivery timelines (*"Friday tak ready milega"*) often result in customer disagreements during pick-up.
- **Scattered Customer History:** Without a lightweight, searchable record system, shopkeepers cannot look up repeat customers, previous repairs, or open ticket statuses.

### The Bolti Slip Solution

**Bolti Slip** transforms any smartphone or browser into an intelligent, voice-assisted repair ticket clerk:

1. **Speak Naturally in Hindi or Hinglish:** The shopkeeper taps one button and speaks the repair details:  
   > *"Customer ka Samsung refrigerator cooling nahi kar raha. Compressor check karna hai, advance 500 rupaye liya aur Friday tak ready karke dena hai."*
2. **Bilingual Speech-to-Text via Gnani Prisma v3.0:** Spoken audio is transcribed using Gnani's **Prisma v3.0** engine with code-mixed recognition (`indic-auto`, `codemix`), handling mixed Hindi and English repair terminology.
3. **Deterministic Rule-Based Extraction:** A transparent, pure-Python regex and rule engine identifies candidate ticket fields (device category, brand, reported problem, customer phone number, estimated cost, advance, and promised delivery date) directly from explicitly stated phrases.
4. **Interactive Review & Verification:** Because real-world speech may have dialect variations or ambient shop noise, the parsed fields are presented as an editable draft. Ambiguous dates (e.g. named weekdays) are flagged in `needs_confirmation` for the technician to review and correct before saving.
5. **Audible Hindi Confirmation via Gnani Timbre v3.0:** As soon as the ticket is saved, Gnani's **Timbre v3.0** voice synthesis plays an audible confirmation over the counter:  
   > *"आपका रिपेयर टिकट BLT-0005 सफलतापूर्वक तैयार हो गया है। ग्राहक Sharma ji। उपकरण: Samsung Refrigerator। अनुमानित लागत: 500 रुपये। धन्यवाद!"*
6. **Digital Job Card & Customer History:** The ticket is assigned a sequential number (`BLT-XXXX`), automatically linked to the customer's phone number, and tracked on an interactive dashboard.

---

## 🔄 How It Works

```mermaid
flowchart TD
    subgraph S1["1. Audio Capture"]
        A["Shopkeeper Taps Mic"] --> B["Record Audio in Hindi / Hinglish"]
        B --> C["MediaRecorder (WebM / Opus)"]
    end

    subgraph S2["2. Audio Normalization & STT"]
        C --> D["FastAPI POST /api/transcribe"]
        D --> E["FFmpeg Audio Converter<br/>(Converts WebM to 16kHz Mono PCM WAV)"]
        E --> F["Gnani Prisma v3.0 STT<br/>(model=prisma-v3.0, indic-auto, codemix)"]
        F --> G["Bilingual Transcript Text"]
    end

    subgraph S3["3. Assistive Extraction & Review"]
        G --> H["TicketExtractor (Rule-Based Engine)"]
        H --> I["Candidate Fields: Device, Brand, Issue, Cost, Date, Phone"]
        H -.-> J["Flags Ambiguous Dates & Missing Fields in needs_confirmation"]
        I --> K["Interactive Review Screen"]
        J --> K
        K --> L["Technician Verifies & Edits Draft"]
    end

    subgraph S4["4. Ticket Creation & CRM"]
        L --> M["POST /api/tickets (Generates BLT-XXXX)"]
        M --> N["Auto-Link / Create Customer in Directory"]
        M --> O["POST /api/tickets/:id/confirm"]
        O --> P["Gnani Timbre v3.0 TTS<br/>(model=timbre-v3.0, Devansh voice, hi-IN)"]
        P --> Q["Spoken Confirmation Played Over Counter"]
        M --> R["Dashboard & Ticket Lifecycle Tracker"]
    end
```

### Detailed Workflow Step-by-Step

1. **Shopkeeper Authentication:** The technician logs in with their credentials. Sessions are protected via cryptographic bearer tokens and per-shop data isolation.
2. **One-Tap Voice Recording:** The technician taps the mic icon. Bolti Slip records the spoken details.
3. **Automated Audio Conversion:** Browser recordings (typically WebM/Opus) are automatically detected and converted by the backend via FFmpeg to 16 kHz 16-bit mono PCM WAV before forwarding to Gnani Prisma.
4. **Bilingual Transcription:** Gnani Prisma v3.0 returns the recognized text with detected language metadata.
5. **Deterministic Field Parsing:** The extractor searches for 16+ consumer electronics categories (Mixer Grinder, TV, Laptop, Fridge, Washing Machine, Geyser, Fan, etc.), top Indian brands, 10-digit mobile numbers, currency values, and delivery dates. Ambiguous dates (such as named weekdays) are placed into `needs_confirmation`.
6. **Technician Review & Adjustment:** The extracted draft is shown in a structured form. The technician checks the values, makes any needed adjustments, and confirms the slip.
7. **Ticket Creation & Global Numbering:** The ticket is committed to the database with a sequential tracking identifier (`BLT-0001`, `BLT-0002`) and linked to the customer's phone number.
8. **Spoken Audio Confirmation:** The backend synthesizes a natural Hindi confirmation via Gnani Timbre v3.0 and streams raw WAV audio to the client, providing audible confirmation across the counter.
9. **Dashboard Management:** Job cards are tracked on the dashboard, where technicians update statuses from `open` to `in_progress`, `resolved`, and `closed`.

---

## ✨ Key Features

### 🎙️ 1. Bilingual Voice Intake & Transcription
- Native support for Hindi, Indian English, and conversational Hinglish code-mixing.
- Powered directly by the **Gnani Prisma v3.0** STT API (`https://api.vachana.ai/stt/v3`).
- Automatic audio container inspection and transparent conversion of WebM/Opus audio to PCM WAV via FFmpeg.

### ⚙️ 2. Assistive Rule-Based Extraction with Review Workflow
- Pure-Python regex and pattern extraction engine (`TicketExtractor`).
- Designed to extract only explicitly stated values without generative AI speculation or cost hallucinations.
- Recognizes 16+ electronic equipment categories, popular brands, Indian phone numbers, problem keywords, costs, and dates.
- Flags ambiguous relative dates (e.g., *"Friday"*) in `needs_confirmation` and leaves unmapped phrases in `unresolved_phrases`, giving technicians clear oversight to review and correct drafts.

### 🔊 3. Spoken Ticket Confirmation (TTS)
- Closes the agreement loop between technician and customer.
- Powered by **Gnani Timbre v3.0** TTS (`https://api.vachana.ai/api/v1/tts/inference`) using the natural Hindi voice **Devansh**.
- Streams linear PCM WAV audio confirming ticket number, customer name, device, and quoted estimate aloud across the counter.

### 🏪 4. Multi-Tenant Shop Isolation & Security
- Isolated tenant workspaces: Every ticket, customer profile, and session query is strictly filtered by `shop_id`.
- PBKDF2-SHA256 password hashing with unique salts and iterations.
- Cryptographically secure 64-character hex session tokens (`secrets.token_hex(32)`).
- Session management allowing shopkeepers to view active sessions and revoke secondary devices.
- IP-based brute-force protection using SlowAPI rate limiting (10 attempts/minute on login).

### 👥 5. Customer Directory & Repair History
- Automatic customer resolution: creating a ticket with a phone number automatically links or registers the customer profile under the active shop.
- Customer search by name or mobile number.
- Historical record of all past repairs, devices, and statuses for each customer.

### 📊 6. Job Card Lifecycle Management
- Sequential global ticket identification (`BLT-XXXX`).
- Four lifecycle stages: `open`, `in_progress`, `resolved`, `closed`.
- Status updates with responsive status badges.

### 📱 7. Installable Android PWA (Progressive Web App)
- W3C Web App Manifest configured for standalone display on Android (`display: standalone`, `theme_color: #4F46E5`).
- Complete icon suite: 192×192, 512×512, maskable icons, and SVG.
- Offline static shell caching via Vite PWA and Workbox for fast application startup.
- **Strict Privacy Rule:** All `/api/*` routes (speech, transcription, tickets, auth) enforce `NetworkOnly` and require an active network connection; sensitive customer data is never cached in browser storage.

### 🗄️ 8. Dual-Engine Async Database Architecture
- **Development & Testing:** Zero-configuration local **SQLite** via `aiosqlite`.
- **Automated SQLite Backups:** Point-in-time database snapshots created at startup using Python's native `sqlite3.Connection.backup()` API with configurable retention cleanup (default: 30 days).
- **Cloud Production:** Automatic switch to **Neon PostgreSQL** via `asyncpg` when `DATABASE_URL` is configured.
- Safe query rewriting and parameter tokenization (`?` to `$1`, `$2`, ...).

---

## 🤖 Gnani AI Integration

Bolti Slip integrates the official **Gnani.ai (Vachana.ai)** developer APIs:

```
                                  +---------------------------------------+
                                  |            GNANI.AI CLOUD             |
                                  |                                       |
    [ Audio File / WAV ] -------->|  Prisma v3.0 Speech-to-Text API       |
                                  |  Endpoint: /stt/v3                    |
                                  |  Model: prisma-v3.0                   |
                                  |  Language: indic-auto                 |
                                  |  Format: codemix                      |
                                  +---------------------------------------+
                                                     |
                                            (Recognized Transcript)
                                                     v
                                  +---------------------------------------+
                                  |         BOLTI SLIP BACKEND            |
                                  |  - Rule-Based Extraction              |
                                  |  - Human Review & DB Commit           |
                                  +---------------------------------------+
                                                     |
                                           (Confirmation Sentence)
                                                     v
                                  +---------------------------------------+
                                  |            GNANI.AI CLOUD             |
                                  |                                       |
    [ WAV Audio Stream ] <--------|  Timbre v3.0 Text-to-Speech API       |
                                  |  Endpoint: /api/v1/tts/inference      |
                                  |  Model: timbre-v3.0                   |
                                  |  Language: hi-IN                      |
                                  |  Voice: Devansh                       |
                                  +---------------------------------------+
```

### 1. Speech-to-Text: Gnani Prisma v3.0

- **API Endpoint:** `https://api.vachana.ai/stt/v3`
- **Authentication:** `X-API-Key-ID` header loaded from `GNANI_API_KEY_ID`
- **Model:** `prisma-v3.0`
- **Language Code:** `indic-auto` (automatic Indian language detection)
- **Format:** `codemix` (critical for colloquial Hindi-English mixed vocabulary)
- **Accepted Formats:** WAV, MP3, M4A, FLAC, OGG, AAC
- **Implementation File:** [`backend/services/prisma.py`](backend/services/prisma.py)
- **Audio Pre-processing:** [`backend/services/audio_converter.py`](backend/services/audio_converter.py) handles WebM/Opus detection and FFmpeg conversion.

### 2. Text-to-Speech: Gnani Timbre v3.0

- **API Endpoint:** `https://api.vachana.ai/api/v1/tts/inference`
- **Authentication:** `X-API-Key-ID` header loaded from `GNANI_API_KEY_ID`
- **Model:** `timbre-v3.0`
- **Selected Voice:** `Devansh` (natural male Hindi voice)
- **Language Code:** `hi-IN`
- **Output Container:** Linear PCM WAV (48,000 Hz, 16-bit, mono)
- **Implementation File:** [`backend/services/timbre.py`](backend/services/timbre.py)
- **Audio Route:** [`backend/routers/speech.py`](backend/routers/speech.py) (`POST /api/tickets/{id}/confirm`)

### 3. Engineering Transparency: Extraction vs. AI Speech

> [!NOTE]
> **Engineering Note for Evaluators:**  
> Bolti Slip utilizes Gnani AI for its core speech capabilities: **speech-to-text recognition via Prisma v3.0** and **text-to-speech synthesis via Timbre v3.0**. Ticket parsing is handled by an internal rule-based Python module (`backend/services/ticket_extractor.py`) rather than a generative LLM. This prevents generative hallucinations of repair costs, phone numbers, or dates, while presenting the technician with an editable draft to verify before confirming the ticket.

---

## 💻 Technology Stack

| Layer | Technology | Version | Purpose in Bolti Slip |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | **React** | `18.3.1` | Component-based reactive user interface |
| **Language** | **TypeScript** | `5.6.2` | Type-safe models, API clients, and state contracts |
| **Build & Tooling** | **Vite** | `5.4.9` | Development server and production bundler |
| **Styling** | **Tailwind CSS** | `v4.3.5` | Modern utility-first CSS styling |
| **Routing** | **React Router DOM** | `6.27.0` | Client-side routing with protected route guards |
| **PWA Engine** | **Vite Plugin PWA** | `2.0.0` | Service Worker generation and manifest integration |
| **Backend Framework** | **FastAPI** | `0.115+` | Asynchronous ASGI REST API framework |
| **ASGI Server** | **Uvicorn** | `0.30+` | High-performance asynchronous HTTP server |
| **Data Validation** | **Pydantic** | `v2.10+` | Strict request/response schema validation |
| **Speech-to-Text** | **Gnani Prisma v3.0** | REST API | Bilingual Hindi/Hinglish speech transcription |
| **Text-to-Speech** | **Gnani Timbre v3.0** | REST API | Spoken Hindi ticket confirmation synthesis |
| **Audio Processing** | **FFmpeg** | Binary CLI | Transparent WebM/Opus to 16 kHz PCM WAV conversion |
| **Rate Limiting** | **SlowAPI** | `0.1.10+` | Rate limiting on authentication endpoints |
| **Local Database** | **aiosqlite / SQLite3** | Python 3 stdlib | Async SQLite driver for local development & testing |
| **Cloud Database** | **asyncpg / PostgreSQL**| `>=0.30.0` | High-throughput async PostgreSQL client for Neon |
| **Database Abstraction**| **Bolti Adapter** | Custom | Unified multi-engine query abstraction layer |
| **Automated Testing** | **Pytest / Custom Suites**| Python 3 | 13 unit tests + 156 integration/security tests |

---

## 🏗️ System Architecture

```mermaid
flowchart LR
    subgraph ClientLayer["Frontend Client (Browser / Android PWA)"]
        UI["React 18 SPA"]
        REC["MediaRecorder Audio API"]
        PLAYER["HTML5 Audio Player"]
        SW["Workbox Service Worker<br/>(Static Assets Cached; API NetworkOnly)"]
    end

    subgraph APILayer["FastAPI Application Server"]
        MAIN["FastAPI Core (main.py)"]
        CORS["Strict CORS Middleware"]
        LIMITER["SlowAPI Rate Limiter"]
        AUTH_ROUTER["/api/auth (Login/Register/Me)"]
        TICKETS_ROUTER["/api/tickets (CRUD & Status)"]
        SPEECH_ROUTER["/api/speech & /api/transcribe"]
        CUSTOMERS_ROUTER["/api/customers (CRM)"]
        CONVERTER["FFmpeg Audio Converter"]
        EXTRACTOR["TicketExtractor (Rule-Based)"]
    end

    subgraph GnaniServices["Gnani.ai Voice Cloud"]
        PRISMA_API["Prisma v3.0 STT API<br/>(/stt/v3)"]
        TIMBRE_API["Timbre v3.0 TTS API<br/>(/api/v1/tts/inference)"]
    end

    subgraph DataLayer["Multi-Engine Persistence"]
        ADAPTER["Database Adapter (adapter.py)"]
        SQLITE_DB[("Local SQLite3 DB<br/>(bolti_slip.db)")]
        BACKUP_SVC["Automated Backup Engine<br/>(Connection.backup())"]
        NEON_PG[("Neon Serverless PostgreSQL<br/>(Cloud Production)")]
    end

    UI -->|"User Actions & Audio"| MAIN
    MAIN --> CORS --> LIMITER
    LIMITER --> AUTH_ROUTER
    LIMITER --> TICKETS_ROUTER
    LIMITER --> SPEECH_ROUTER
    LIMITER --> CUSTOMERS_ROUTER

    SPEECH_ROUTER --> CONVERTER
    CONVERTER -->|"PCM WAV"| PRISMA_API
    PRISMA_API -->|"Transcript"| SPEECH_ROUTER
    SPEECH_ROUTER --> EXTRACTOR
    SPEECH_ROUTER -->|"Synthesize Hindi"| TIMBRE_API
    TIMBRE_API -->|"WAV Audio"| PLAYER

    AUTH_ROUTER --> ADAPTER
    TICKETS_ROUTER --> ADAPTER
    CUSTOMERS_ROUTER --> ADAPTER

    ADAPTER -.->|"Local Dev (Default)"| SQLITE_DB
    ADAPTER -.->|"DATABASE_URL set"| NEON_PG
    SQLITE_DB --> BACKUP_SVC
```

---

## 🎨 User Interface Previews

Bolti Slip uses a Material-inspired layout styled in an **Indigo & Deep Navy** palette (`primary: #4F46E5`, `surface: #F8F9FF`), built for readability on repair shop counters.

| Voice Intake & Ticket Creation | Dashboard & Ticket Overview |
| :---: | :---: |
| ![Voice Intake Desktop](design-references/desktop/voice_intake_bolti_slip/screen.png) | ![Dashboard Desktop](design-references/desktop/dashboard_bolti_slip/screen.png) |
| *Tap-to-speak voice recording with live transcription and structured review* | *Real-time statistics, active repair statuses, and customer search* |

| Ticket History & Management | Mobile PWA Viewport |
| :---: | :---: |
| ![Ticket History Desktop](design-references/desktop/ticket_history_bolti_slip/screen.png) | ![Mobile Voice Intake](design-references/mobile/voice_intake_bolti_slip_mobile_1/screen.png) |
| *Sequential BLT-XXXX tracking with status filtering and cost summaries* | *Optimized for one-handed operation on mobile screens* |

---

## 🚀 Getting Started

Follow these instructions to run Bolti Slip locally.

### 1. Prerequisites

- **Python:** 3.10 or newer (tested on Python 3.10, 3.11, 3.12, 3.14 on Windows & Linux)
- **Node.js:** v18.0 or newer & `npm`
- **FFmpeg:** Installed and available in system `PATH` (converts browser WebM/Opus audio to PCM WAV)
- **Gnani AI API Key:** Obtain from [vachana.ai](https://vachana.ai)

### 2. Clone Repository & Setup Virtual Environment

```bash
# Clone the repository
git clone https://github.com/KankurtiMohammadZiyaouddin/Bolti-Slip.git
cd Bolti-Slip

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt
```

### 3. Environment Configuration

Copy the example environment configuration:
```bash
cp .env.example .env
```

Edit `.env` and add your Gnani API key:
```ini
# Gnani AI API Key (required for voice features)
GNANI_API_KEY_ID=your_gnani_api_key_here

# Environment Mode
BOLTI_ENV=development

# Optional: Seed password for first-time database initialization
BOLTI_SEED_PASSWORD=YourSecurePassword123
```

### 4. Start the Application

Start the backend and frontend in two separate terminals:

#### Terminal 1 — FastAPI Backend:
```bash
# From project root with .venv activated:
uvicorn backend.main:app --reload --port 8000
```
*API will run at `http://127.0.0.1:8000`. Interactive OpenAPI documentation available at `http://127.0.0.1:8000/docs`.*

#### Terminal 2 — React Frontend (Vite):
```bash
cd frontend
npm install
npm run dev
```
*Frontend will run at `http://localhost:5173`.*

---

## 🔑 First-Run Shopkeeper Setup

When starting on a fresh database with zero shops, choose any one of the following methods:

### Method A: Web Interface Registration (Recommended)
1. Open `http://localhost:5173/register` in your web browser.
2. Enter your shop name, owner name, username, and password (minimum 6 characters).
3. Click **"नई दुकान जोड़ें (Register Shop)"** to log in immediately.

### Method B: CLI Helper Script
Run the interactive setup helper in your terminal:
```bash
python scripts/setup_first_shop.py --username admin --shop-name "City Repair Center" --owner-name "Aakash Verma"
```
*(The script exits safely without making changes if a shop already exists, preventing account takeovers.)*

### Method C: Environment Seed
Set `BOLTI_SEED_PASSWORD` in `.env`. When `init_db()` runs on a completely empty database, it provisions the default initial shop (`sharma`) with that password.

---

## 🧪 Automated Testing & Verification

Bolti Slip includes automated test suites covering rule-based extraction, database engine switching, multi-shop security, migration scripts, and PWA criteria.

```bash
# 1. Run ticket extractor unit tests (13 test scenarios)
pytest tests/test_ticket_extractor.py -v

# 2. Run database abstraction adapter tests (29 tests)
python scripts/test_adapter.py

# 3. Run first-run shop seed tests (16 tests)
python scripts/test_seed_setup.py

# 4. Run multi-shop security and authentication test suite (31 tests)
python scripts/test_batch2_security.py

# 5. Run PostgreSQL schema & migration validation (29 tests total)
python scripts/test_postgres_schema.py
python scripts/test_migration_script.py

# 6. Run PWA compliance audit
python tests/verify_pwa_readiness.py

# 7. Run frontend production build
npm --prefix frontend run build
```

### Verified Test Suite Summary

| Test Category | Suite File | Tests | Status | Scope |
| :--- | :--- | :---: | :---: | :--- |
| **Deterministic Extraction** | `tests/test_ticket_extractor.py` | 13 | ✅ Passed | Hindi, English, Hinglish, delivery dates, device types |
| **Database Adapter** | `scripts/test_adapter.py` | 29 | ✅ Passed | SQLite & PostgreSQL parity, query sanitization, `?` conversion |
| **First-Run Seed** | `scripts/test_seed_setup.py` | 16 | ✅ Passed | Zero-shop detection, seed password fallback, idempotency |
| **Security & Auth** | `scripts/test_batch2_security.py` | 31 | ✅ Passed | Multi-tenant isolation, session tokens, password rotation, CORS |
| **PostgreSQL Schema** | `scripts/test_postgres_schema.py` | 18 | ✅ Passed | Neon foreign keys, triggers, constraints, precision |
| **Data Migration** | `scripts/test_migration_script.py` | 11 | ✅ Passed | SQLite-to-PostgreSQL sequence sync and data fidelity |
| **Bugfix Regressions** | `scripts/test_batch1_2_fixes.py` | 18 | ✅ Passed | Session longevity, customer phone linking, edge cases |
| **Batch 1 Security** | `scripts/test_batch1_security.py` | 33 | ✅ Passed | Auth route guards, rate limiting, password rotation |
| **PWA Readiness** | `tests/verify_pwa_readiness.py` | 4 checks | ✅ Passed | Manifest keys, maskable icons, Service Worker rules |
| **Frontend Production** | `npm run build` | — | ✅ Passed | TypeScript check, asset minification, Workbox compilation |

---

## 🛡️ Production Readiness & Deployment

### 1. Dual-Engine Deployment Architecture

- **Local / Single-Server Deployment:** Runs on SQLite. Every backend startup triggers an automated online snapshot via `sqlite3.Connection.backup()`, written to `backups/` and retained for 30 days.
- **Cloud Scale (Render + Neon PostgreSQL):** Setting `DATABASE_URL=postgresql://...` automatically engages the `asyncpg` connection pool. SQLite backup routines are safely skipped in PostgreSQL mode to avoid disk errors.

### 2. Strict Production CORS Enforcement

- When `BOLTI_ENV=production`:
  - Wildcard `*` origins are rejected and logged as critical security alerts.
  - Only trusted origins listed in `BOLTI_CORS_ORIGINS` are accepted.
  - Vercel preview environments are protected by a scoped regex pattern (`BOLTI_CORS_ORIGIN_REGEX`).

### 3. Deploying to Render & Vercel

#### Backend Web Service (Render):
- **Runtime:** Python 3
- **Build Command:** `pip install -r backend/requirements.txt`
- **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path:** `/api/health` (returns `{"status": "ok", "version": "1.0.0"}`)
- **Environment Variables Required:**
  - `DATABASE_URL` = Your Neon PostgreSQL connection string
  - `BOLTI_ENV` = `production`
  - `BOLTI_CORS_ORIGINS` = Your frontend URL
  - `GNANI_API_KEY_ID` = Your Gnani API key

#### Frontend Application (Vercel / Render Static Site):
- **Framework Preset:** Vite
- **Root Directory:** `frontend`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Environment Variable:**
  - `VITE_API_BASE_URL` = Your backend URL

---

## 🌍 Real-World Impact

| Traditional Repair Shop Process | Bolti Slip Voice Workflow | Practical Business Benefit |
| :--- | :--- | :--- |
| Handwrite paper slips while holding tools and handling greasy equipment | Speak details aloud while inspecting the unit; review the draft on screen | **Reduces typing and handwriting friction during active workbench repair tasks** |
| Customer disputes verbal quotes or delivery dates at pick-up time | Spoken confirmation in Hindi plays aloud across the counter immediately upon saving | **Establishes mutual verbal clarity and customer trust across the counter** |
| Customer phone numbers scribbled illegibly or lost on chits | Phone numbers extracted and confirmed on screen | **Preserves legible, organized customer contact records** |
| Paper slips lost, damaged, or misplaced in the shop | Digital job cards indexed with sequential `BLT-XXXX` numbers | **Organized, searchable repair history accessible at any time** |
| Repeat customers have no past repair history recorded | Phone number auto-links to complete customer repair history | **Provides instant context on past device issues and warranty history** |

---

## 👥 Authors & Acknowledgments

- **Developer:** [Kankurti Mohammad Ziyaouddin](https://github.com/KankurtiMohammadZiyaouddin)
- **Challenge:** Developed for the **Great Indian AI Internship Challenge** organized by [Gnani.ai](https://gnani.ai).
- **Core Speech Technologies:** Powered by **Gnani AI Prisma v3.0 STT** and **Gnani AI Timbre v3.0 TTS**.

---

<div align="center">

**Bolti Slip (बोलती स्लिप)**  
*Bringing Voice AI to India's Grassroots Repair Economy.*

</div>
