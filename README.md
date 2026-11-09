# Bolti Slip (बोलती स्लिप)

AI-powered voice-to-repair-ticket SaaS for Indian electronics and appliance repair shops. Features bilingual Hindi/English voice transcription (Gnani Prisma v3.0), rule-based ticket field extraction, audio confirmation playback (Gnani Timbre v3.0), customer directories, and multi-shop data isolation with installable Android PWA support.

---

## Getting Started

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Node.js 18+ & npm
- FFmpeg (for mobile WebM/Opus audio compatibility)

### 2. Environment Configuration
Copy `.env.example` to `.env` in the project root:
```bash
cp .env.example .env
```
Fill in your Gnani AI API credentials:
```ini
GNANI_API_KEY_ID=your_gnani_api_key_here
```

### 3. First-Run Shopkeeper Setup
When launching on a fresh database with zero shops, choose **one** of the following setup options:

#### Option A: Web Interface Registration (Recommended)
1. Start the backend and frontend servers.
2. Open the application in your browser (e.g. `http://localhost:5173`).
3. Click **"नई दुकान जोड़ें (Register Shop)"** at `/register`.
4. Fill in your shop details and choose a secure password (minimum 6 characters).

#### Option B: CLI Setup Script
Run the interactive setup helper:
```bash
.venv\Scripts\python.exe scripts\setup_first_shop.py
```
Or pass arguments directly:
```bash
.venv\Scripts\python.exe scripts\setup_first_shop.py --username admin --shop-name "My Repair Shop" --owner-name "My Name"
```
*(This script only runs when zero shops exist, preventing account takeover or password overwrites.)*

#### Option C: Automated Seed via Environment Variable
Set `BOLTI_SEED_PASSWORD` in your `.env` before running migrations or starting the server:
```ini
BOLTI_SEED_PASSWORD=your_secure_seed_password_here
```
When `init_db()` runs on a completely empty database, it will initialize the default shop (`sharma`) using this password. If this variable is omitted or left blank, no default account is created, preventing silent inaccessible accounts.

---

## Starting the Application

### Backend (FastAPI)
```bash
.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

### Frontend (React + Vite + Tailwind CSS + PWA)
```bash
cd frontend
npm install
npm run dev
```

---

## Running Verification Tests

```bash
# Batch 1 Security & Authentication Suite
.venv\Scripts\python.exe scripts\test_batch1_security.py

# First-Run Seed Setup Suite
.venv\Scripts\python.exe scripts\test_seed_setup.py

# Batch 1.2 Corrections Suite
.venv\Scripts\python.exe scripts\test_batch1_2_fixes.py

# Batch 2 Database Backup & CORS Security Suite
.venv\Scripts\python.exe scripts\test_batch2_security.py

# Frontend Production Build & PWA Generation
npm --prefix frontend run build
```

---

## Production Security & Operations

### 1. Production CORS Configuration
Cross-Origin Resource Sharing is strictly controlled based on the environment mode:
- **Development Mode (`BOLTI_ENV=development`):** Localhost origins (`localhost:5173`, `127.0.0.1:5173`, `localhost:3000`, `127.0.0.1:3000`) are automatically permitted for frontend development.
- **Production Mode (`BOLTI_ENV=production`):** Only origins explicitly configured in `BOLTI_CORS_ORIGINS` are accepted. Wildcards (`*`) are strictly rejected in production to protect authenticated Bearer-token requests.

Configuration in `.env`:
```ini
BOLTI_ENV=production
BOLTI_CORS_ORIGINS=https://your-shop-domain.com,https://app.your-shop-domain.com
```

### 2. Automated Database Backups
Bolti Slip automatically creates an online snapshot of the SQLite database upon application startup using Python's native `sqlite3` Backup API (`Connection.backup()`). This creates a point-in-time consistent backup without locking or taking the database offline.

- **Backup Directory (`BOLTI_BACKUP_DIR`):** Default: `backups/` in project root. Stored outside publicly served frontend directories and excluded from git via `.gitignore`.
- **Retention Period (`BOLTI_BACKUP_RETENTION_DAYS`):** Default: `30` days. Expired backups matching `bolti_slip_backup_*.db` are automatically cleaned up when a new backup is created.
- **Safety Guarantee:** The live database and unrelated files are never deleted or modified during retention cleanup.

Configuration in `.env`:
```ini
BOLTI_BACKUP_DIR=backups
BOLTI_BACKUP_RETENTION_DAYS=30
```

### 3. Manual Database Restore Procedure
Bolti Slip **never** automatically restores or overwrites the live database. In the event of data corruption or disaster recovery, follow this manual restore procedure:

1. **Stop the backend server:**
   ```bash
   # Terminate the uvicorn process (Ctrl+C)
   ```
2. **Back up the current live database for safety:**
   ```powershell
   Copy-Item bolti_slip.db bolti_slip.db.corrupt_copy
   ```
3. **Select your desired backup from `backups/`:**
   ```powershell
   Get-ChildItem backups\bolti_slip_backup_*.db | Sort-Object LastWriteTime -Descending
   ```
4. **Copy the chosen backup over the live database:**
   ```powershell
   Copy-Item backups\bolti_slip_backup_YYYYMMDD_HHMMSS.db bolti_slip.db -Force
   ```
5. **Remove any stale SQLite WAL and shared-memory files:**
   ```powershell
   Remove-Item bolti_slip.db-wal, bolti_slip.db-shm -ErrorAction SilentlyContinue
   ```
6. **Restart the backend server:**
   ```bash
   .venv\Scripts\python.exe -m uvicorn backend.main:app --port 8000
   ```
