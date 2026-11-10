# Solution Pitch: Bolti Slip (बोलती स्लिप)

> **"जो बोला, वही लिखा। जो लिखा, वही कन्फ़र्म।"**  
> *(Jo Bola, Wahi Likha. Jo Likha, Wahi Confirm.)*  
> **Submission for the Great Indian AI Internship Challenge by Gnani.ai**  
> **Repository:** [github.com/KankurtiMohammadZiyaouddin/Bolti-Slip](https://github.com/KankurtiMohammadZiyaouddin/Bolti-Slip)

---

## 1. Executive Summary

**Bolti Slip** is a voice-first repair ticket management application created for India's grassroots electronics, appliance, and mobile repair businesses. By pairing **Gnani Prisma v3.0** speech-to-text with **Gnani Timbre v3.0** text-to-speech, Bolti Slip allows shopkeepers to speak repair job details naturally in Hindi, English, or Hinglish, review parsed ticket fields, and play an audible Hindi confirmation to the customer over the counter before issuing a digital job card.

---

## 2. Target Users & The Problem

### Target Audience
Proprietors and technicians at local repair kiosks and independent workshops servicing smartphones, televisions, mixer grinders, washing machines, refrigerators, and consumer electronics.

### The Problem
- **Hands-Busy Workflows:** Technicians frequently work with screwdrivers, soldering equipment, and grease, making mobile keyboard typing awkward, slow, and error-prone.
- **Fragile Paper Slips:** Handwritten chits get smudged, torn, or lost, leading to lost customer records.
- **Customer Disputes:** Verbal agreements on diagnostic estimates and delivery deadlines often result in disagreements when the customer returns for collection.
- **Scattered Records:** Independent repair shops lack a searchable record of past customer visits, previous repairs, and open ticket statuses.

---

## 3. Our Solution

Bolti Slip introduces a fast, voice-assisted intake workflow built around trust and simplicity:

1. **Speak the Job:** The technician taps a single recording button and speaks naturally in conversational Hindi, English, or mixed Hinglish.
2. **Speech Recognition via Gnani Prisma v3.0:** Spoken audio is transcribed using Gnani's code-mixed recognition model (`indic-auto`, `codemix`).
3. **Assistive Rule-Based Extraction:** A transparent, rule-based Python parsing engine extracts candidate fields (device category, brand, reported problem, customer phone number, estimated cost, and delivery date).
4. **Human-in-the-Loop Review:** The shopkeeper reviews the extracted draft on screen, adjusts any misheard details or ambiguous dates, and confirms the ticket.
5. **Audible Confirmation via Gnani Timbre v3.0:** Upon creation, the app synthesizes and plays aloud an audible Hindi confirmation (*"आपका रिपेयर टिकट BLT-XXXX सफलतापूर्वक तैयार हो गया है..."*), confirming the agreement aloud across the counter.
6. **Digital Ticket & CRM:** The ticket is assigned a sequential tracking ID (`BLT-XXXX`), linked to the customer's phone number, and tracked on an interactive dashboard.

---

## 4. How Gnani AI Powers Bolti Slip

Bolti Slip uses Gnani AI directly for speech intelligence:

- **Gnani Prisma v3.0 (STT):**
  - **Endpoint:** `https://api.vachana.ai/stt/v3` (`model=prisma-v3.0`, `language_code=indic-auto`, `format=codemix`)
  - **Function:** Converts colloquial Indian multilingual speech and code-mixed phrasing into structured text.
  - **Audio Pipeline:** Mobile browser WebM/Opus audio recordings are transparently converted to 16 kHz 16-bit mono PCM WAV via backend FFmpeg pre-processing before API transmission.
- **Gnani Timbre v3.0 (TTS):**
  - **Endpoint:** `https://api.vachana.ai/api/v1/tts/inference` (`model=timbre-v3.0`, `language=hi-IN`, Voice: `Devansh`)
  - **Function:** Streams natural, professional Hindi speech to confirm the job card details audibly between technician and customer.
- **Engineering Note on Extraction:** Parsing is performed deterministically by a rule-based engine (`backend/services/ticket_extractor.py`) rather than an external LLM. This design prevents financial or date hallucinations while keeping the draft subject to explicit shopkeeper review.

---

## 5. Key Verified Features

- **Bilingual Voice Intake:** Hindi, Indian English, and Hinglish speech recognition via Gnani Prisma.
- **Assistive Extraction & Review UI:** Extracts 16+ common electronic device types, Indian phone numbers, costs, and dates; highlights ambiguous terms in a dedicated confirmation list for shopkeeper review.
- **Spoken Hindi Ticket Playback:** Real-time audio synthesis via Gnani Timbre.
- **Multi-Tenant Shop Isolation:** Secure PBKDF2-SHA256 password hashing, 64-character hex session tokens, and strict per-shop database query scoping (`shop_id`).
- **Customer Directory & History:** Automatic customer linking by phone number with historical ticket lookup.
- **Ticket Lifecycle Management:** Four clear stages (`open`, `in_progress`, `resolved`, `closed`).
- **Installable Android PWA:** Fast static shell caching for offline application loading. *(Note: Speech recognition, text-to-speech, and database operations enforce `NetworkOnly` and require an active network connection).*
- **Dual-Engine Persistence:** Local SQLite with automated startup snapshots + production Neon PostgreSQL support via asyncpg.

---

## 6. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, TypeScript, Vite 5, Tailwind CSS v4, React Router 6, Vite PWA (Workbox) |
| **Backend** | FastAPI (Python 3.10+ / 3.14), Uvicorn, SlowAPI, Pydantic v2 |
| **AI Voice Services** | Gnani Prisma v3.0 (STT) + Gnani Timbre v3.0 (TTS) via Vachana.ai API |
| **Audio Pipeline** | FFmpeg (transparent WebM/Opus to PCM WAV conversion) |
| **Databases** | SQLite (local dev & auto-backups) / PostgreSQL (Neon serverless production) |
| **Security** | PBKDF2-SHA256 hashing, bearer session tokens, SlowAPI rate limiting, strict CORS |

---

## 7. Submission Details

- **Project Name:** Bolti Slip (बोलती स्लिप)
- **Challenge:** Great Indian AI Internship Challenge by Gnani.ai
- **Developer:** Kankurti Mohammad Ziyaouddin
- **Repository:** [https://github.com/KankurtiMohammadZiyaouddin/Bolti-Slip](https://github.com/KankurtiMohammadZiyaouddin/Bolti-Slip)
- **Deployment Status:** Deployment-ready architecture for Render (FastAPI) and Neon PostgreSQL; local execution fully verified.
