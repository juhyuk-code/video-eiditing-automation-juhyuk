# Product Requirements Document (PRD)
# Stream Automation - Web Service Edition

**Version:** 2.0
**Author:** Juhyuk
**Last Updated:** 2025-01-22
**Status:** Draft

---

## 1. Executive Summary

### 1.1 Problem Statement (Revised)

The CLI-based approach requires:
- Manual execution after each stream
- Local machine to be running
- Technical knowledge to operate
- Manual file management

A web-based service with Google Drive integration would:
- Automatically detect new recordings
- Process without user intervention
- Work from any device
- Organize outputs automatically

### 1.2 Solution

A web application that:
1. **Watches** a Google Drive folder for new OBS recordings
2. **Automatically processes** detected files (transcription, analysis, Premiere export)
3. **Uploads outputs** to organized Google Drive folders
4. **Notifies** the user when processing is complete

### 1.3 Target User

- **Primary:** Juhyuk (solo creator)
- **Content Type:** Market analysis, trading insights, financial commentary
- **Languages:** Korean and English
- **Workflow:** Records with OBS → Files sync to Google Drive → Service handles the rest

---

## 2. Goals and Non-Goals

### 2.1 Goals

| ID | Goal | Success Metric |
|----|------|----------------|
| G1 | Zero-touch processing | No manual intervention after OBS recording |
| G2 | Cloud-based workflow | Process from any device, anywhere |
| G3 | Automatic file organization | Inputs/outputs organized in Google Drive |
| G4 | Real-time status updates | Know processing status without checking |
| G5 | Minimum 10 viral clips | At least 10 short-form clips per stream |

### 2.2 Non-Goals (v2.0)

| ID | Non-Goal | Reason |
|----|----------|--------|
| NG1 | Multi-user support | Single-user service for now |
| NG2 | Mobile app | Web app is sufficient |
| NG3 | Direct YouTube/TikTok upload | Keep human in the loop for final review |
| NG4 | Real-time streaming processing | Focus on post-stream workflow |
| NG5 | Self-hosted option | Cloud-first approach |

---

## 3. User Stories

### 3.1 Primary Workflow

```
AS A content creator
I WANT my recordings to be automatically processed when I upload them to Google Drive
SO THAT I can focus on creating content while the tedious editing work happens automatically
```

### 3.2 Detailed User Stories

| ID | User Story | Priority |
|----|------------|----------|
| US1 | As a creator, I want to drop my OBS recordings into a Google Drive folder and have them auto-processed | P0 |
| US2 | As a creator, I want to see the processing status on a web dashboard | P0 |
| US3 | As a creator, I want outputs automatically organized in my Google Drive | P0 |
| US4 | As a creator, I want to be notified (email/push) when processing is complete | P1 |
| US5 | As a creator, I want to review and re-process clips if needed | P1 |
| US6 | As a creator, I want to customize viral detection settings | P2 |
| US7 | As a creator, I want to see a history of all processed streams | P1 |

---

## 4. System Architecture

### 4.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER'S ENVIRONMENT                              │
│  ┌─────────────┐         ┌─────────────────────────────────────────────┐    │
│  │  OBS Studio │ ──────► │              Google Drive                    │    │
│  │  (Records)  │  sync   │  ┌─────────────────────────────────────┐    │    │
│  └─────────────┘         │  │ 📁 StreamAutomation/                │    │    │
│                          │  │   📁 Input/                         │    │    │
│                          │  │     📁 2025-01-15_market_analysis/  │    │    │
│                          │  │       📄 full_stream.mp4            │    │    │
│                          │  │       📄 webcam.mp4                 │    │    │
│                          │  │       📄 screen.mp4                 │    │    │
│                          │  │   📁 Output/                        │    │    │
│                          │  │     📁 2025-01-15_market_analysis/  │    │    │
│                          │  │       📁 longform/                  │    │    │
│                          │  │       📁 shortform/                 │    │    │
│                          │  └─────────────────────────────────────┘    │    │
│                          └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          │ Google Drive API
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WEB SERVICE (Cloud)                                │
│                                                                              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐       │
│  │   Web Frontend   │    │   API Backend    │    │  Background      │       │
│  │   (Next.js)      │◄──►│   (FastAPI)      │◄──►│  Worker          │       │
│  │                  │    │                  │    │  (Celery/Redis)  │       │
│  │  • Dashboard     │    │  • Auth (OAuth)  │    │                  │       │
│  │  • Job status    │    │  • Job queue     │    │  • File watcher  │       │
│  │  • Settings      │    │  • Google Drive  │    │  • Transcription │       │
│  │  • History       │    │  • Webhooks      │    │  • Analysis      │       │
│  └──────────────────┘    └──────────────────┘    │  • XML export    │       │
│                                   │              │  • Upload        │       │
│                                   │              └──────────────────┘       │
│                                   ▼                        │                │
│                          ┌──────────────────┐              │                │
│                          │    Database      │              │                │
│                          │   (PostgreSQL)   │◄─────────────┘                │
│                          │                  │                               │
│                          │  • Jobs          │                               │
│                          │  • User settings │                               │
│                          │  • History       │                               │
│                          └──────────────────┘                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          │ API Calls
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL SERVICES                                  │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐       │
│  │  Return Zero     │    │  Claude API      │    │  Google Drive    │       │
│  │  (Transcription) │    │  (Analysis)      │    │  (Storage)       │       │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PROCESSING PIPELINE                                │
└─────────────────────────────────────────────────────────────────────────────┘

 1. DETECT                2. DOWNLOAD              3. PROCESS
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│ Watch Google  │       │ Download 3    │       │ • Extract     │
│ Drive /Input  │──────►│ video files   │──────►│   audio       │
│ folder        │       │ to temp       │       │ • Detect      │
│               │       │ storage       │       │   silences    │
└───────────────┘       └───────────────┘       │ • Transcribe  │
                                                │ • Analyze     │
                                                │ • Generate    │
                                                │   XMLs        │
                                                └───────┬───────┘
                                                        │
 4. UPLOAD               5. NOTIFY                      │
┌───────────────┐       ┌───────────────┐              │
│ Upload to     │       │ Send email/   │              │
│ Google Drive  │◄──────│ push          │◄─────────────┘
│ /Output       │       │ notification  │
└───────────────┘       └───────────────┘
```

---

## 5. Google Drive Folder Structure

### 5.1 Required Folder Structure

```
📁 StreamAutomation/
│
├── 📁 Input/
│   │
│   ├── 📁 2025-01-15_market_analysis/     ← User creates this folder
│   │   ├── 📄 full_stream.mp4             ← Required
│   │   ├── 📄 webcam.mp4                  ← Required
│   │   └── 📄 screen.mp4                  ← Required
│   │
│   └── 📁 2025-01-16_crypto_update/       ← Another stream
│       ├── 📄 full_stream.mp4
│       ├── 📄 webcam.mp4
│       └── 📄 screen.mp4
│
└── 📁 Output/                              ← Auto-created by service
    │
    ├── 📁 2025-01-15_market_analysis/
    │   ├── 📁 longform/
    │   │   ├── 📄 timeline.xml
    │   │   ├── 📄 captions.srt
    │   │   ├── 📄 captions.vtt
    │   │   ├── 📄 chapters.txt
    │   │   └── 📄 suggestions.md
    │   │
    │   ├── 📁 shortform/
    │   │   ├── 📄 timeline.xml
    │   │   ├── 📄 clips_metadata.json
    │   │   ├── 📁 captions/
    │   │   └── 📄 suggestions.md
    │   │
    │   └── 📁 transcript/
    │       ├── 📄 full_transcript.json
    │       └── 📄 full_transcript.txt
    │
    └── 📄 _processing_log.json            ← Processing history
```

### 5.2 File Detection Rules

A folder in `/Input` is ready for processing when:
1. Folder contains exactly 3 video files
2. Files are named: `full_stream.*`, `webcam.*`, `screen.*` (mp4, mov, mkv)
3. All files have finished uploading (file size stable for 60 seconds)
4. Folder has not been processed before (not in history)

### 5.3 Naming Convention

**Input folder naming:** `{YYYY-MM-DD}_{stream_title}`
- Example: `2025-01-15_market_analysis`
- Example: `2025-01-16_bitcoin_crash_reaction`

The folder name becomes the stream name in the system.

---

## 6. Web Application Specification

### 6.1 Pages

#### 6.1.1 Dashboard (Home)

```
┌─────────────────────────────────────────────────────────────────┐
│  Stream Automation                              [Settings] [?]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 📊 Current Status                                        │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                         │   │
│  │  🔄 Processing: "2025-01-15 Market Analysis"            │   │
│  │     Step 3/5: Transcribing... (45%)                     │   │
│  │     ████████████░░░░░░░░░░░░░░                          │   │
│  │                                                         │   │
│  │  ⏳ Queued: 1 stream                                    │   │
│  │  ✅ Completed today: 2 streams                          │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 📁 Recent Streams                                        │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                         │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │ ✅ 2025-01-14 Crypto Weekly Review              │   │   │
│  │  │    12 clips • 8 chapters • Completed 2h ago     │   │   │
│  │  │    [View Output] [Re-process]                   │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │                                                         │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │ ✅ 2025-01-13 Bitcoin Analysis                  │   │   │
│  │  │    15 clips • 10 chapters • Completed yesterday │   │   │
│  │  │    [View Output] [Re-process]                   │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 6.1.2 Settings Page

```
┌─────────────────────────────────────────────────────────────────┐
│  Settings                                            [← Back]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🔗 Google Drive Connection                               │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  Status: ✅ Connected as juhyuk@gmail.com               │   │
│  │  Input folder: /StreamAutomation/Input                  │   │
│  │  Output folder: /StreamAutomation/Output                │   │
│  │  [Reconnect] [Change Folders]                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🔊 Silence Detection                                     │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  Threshold: [-40] dB                                    │   │
│  │  Minimum duration: [0.5] seconds                        │   │
│  │  Padding: [0.1] seconds                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🎬 Short-form Settings                                   │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  Minimum clips: [10]                                    │   │
│  │  Maximum clip duration: [180] seconds                   │   │
│  │                                                         │   │
│  │  Viral signals (what to look for):                      │   │
│  │  [x] Bold market predictions                            │   │
│  │  [x] Contrarian takes                                   │   │
│  │  [x] Price calls                                        │   │
│  │  [x] "I told you so" moments                            │   │
│  │  [x] Surprising insights                                │   │
│  │  [ ] Custom: [________________]  [Add]                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🔔 Notifications                                         │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  [x] Email when processing completes                    │   │
│  │  [ ] Email when new files detected                      │   │
│  │  Email: juhyuk@gmail.com                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│                                          [Save Settings]        │
└─────────────────────────────────────────────────────────────────┘
```

#### 6.1.3 Job Detail Page

```
┌─────────────────────────────────────────────────────────────────┐
│  2025-01-15 Market Analysis                      [← Back]       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Status: ✅ Completed                                           │
│  Duration: 1:32:45 → 1:18:22 (14 min silences removed)         │
│  Processed: 2 hours ago                                         │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 📺 Long-form Output                                      │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  Chapters: 8                                            │   │
│  │  00:00 Introduction                                     │   │
│  │  02:34 Market Overview                                  │   │
│  │  15:22 Bitcoin Analysis                                 │   │
│  │  ...                                                    │   │
│  │                                                         │   │
│  │  [📥 Download timeline.xml] [📂 Open in Drive]          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 📱 Short-form Clips (12)                                 │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                         │   │
│  │  Clip 1 • bold_prediction • Score: 0.95                 │   │
│  │  "Bitcoin will hit $100K this month..."                 │   │
│  │  Duration: 0:45                                         │   │
│  │                                                         │   │
│  │  Clip 2 • insight • Score: 0.89                         │   │
│  │  "What people don't realize about..."                   │   │
│  │  Duration: 1:12                                         │   │
│  │  ...                                                    │   │
│  │                                                         │   │
│  │  [📥 Download all clips] [📂 Open in Drive]             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  [🔄 Re-process Stream]                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Technical Stack

### 7.1 Frontend

| Component | Technology | Notes |
|-----------|------------|-------|
| Framework | Next.js 14+ | App Router, Server Components |
| Styling | Tailwind CSS | Utility-first CSS |
| UI Components | shadcn/ui | Accessible, customizable |
| State | React Query | Server state management |
| Auth | NextAuth.js | Google OAuth |

### 7.2 Backend

| Component | Technology | Notes |
|-----------|------------|-------|
| API Framework | FastAPI | Python, async support |
| Task Queue | Celery | Background job processing |
| Message Broker | Redis | For Celery + caching |
| Database | PostgreSQL | Job history, settings |
| File Storage | Google Drive API | Primary storage |
| Temp Storage | Cloud Storage (GCS) | Processing temp files |

### 7.3 External Services

| Service | Purpose | API |
|---------|---------|-----|
| Google Drive | File storage & sync | Drive API v3 |
| Return Zero | Korean/English transcription | RTZR STT API |
| Anthropic | Content analysis | Claude API |
| SendGrid/Resend | Email notifications | Email API |

### 7.4 Infrastructure

| Component | Service | Notes |
|-----------|---------|-------|
| Frontend Hosting | Vercel | Next.js optimized |
| Backend Hosting | Google Cloud Run | Serverless containers |
| Worker Hosting | Google Compute Engine | Long-running processes |
| Database | Cloud SQL (PostgreSQL) | Managed database |
| Redis | Cloud Memorystore | Managed Redis |

---

## 8. API Specification

### 8.1 Endpoints

#### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/auth/google` | Initiate Google OAuth |
| GET | `/api/auth/callback` | OAuth callback |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/me` | Get current user |

#### Jobs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/jobs` | List all jobs |
| GET | `/api/jobs/{id}` | Get job details |
| POST | `/api/jobs/{id}/reprocess` | Re-process a job |
| DELETE | `/api/jobs/{id}` | Delete job and outputs |

#### Settings

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/settings` | Get user settings |
| PUT | `/api/settings` | Update settings |
| POST | `/api/settings/test-drive` | Test Drive connection |

#### Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | Get current processing status |
| GET | `/api/status/stream` | SSE stream for real-time updates |

### 8.2 WebSocket/SSE Events

Real-time updates via Server-Sent Events:

```typescript
interface ProcessingEvent {
  type: 'job_started' | 'job_progress' | 'job_completed' | 'job_failed';
  jobId: string;
  data: {
    step?: string;       // Current step name
    progress?: number;   // 0-100
    message?: string;    // Status message
    error?: string;      // Error message if failed
  };
}
```

---

## 9. Background Worker Specification

### 9.1 File Watcher Task

Runs every 60 seconds:

```python
@celery.task
def watch_google_drive():
    """
    1. List folders in /StreamAutomation/Input
    2. For each folder:
       - Check if it has 3 required files
       - Check if files are fully uploaded (size stable)
       - Check if not already processed
    3. If ready, create job and enqueue processing task
    """
```

### 9.2 Processing Task

```python
@celery.task(bind=True, max_retries=3)
def process_stream(self, job_id: str):
    """
    1. Download files from Google Drive to temp storage
    2. Extract audio
    3. Detect silences
    4. Transcribe (Return Zero API)
    5. Analyze (Claude API)
    6. Generate Premiere XMLs
    7. Upload outputs to Google Drive
    8. Update job status
    9. Send notification
    10. Cleanup temp files
    """
```

### 9.3 Job States

```
PENDING → DOWNLOADING → PROCESSING → UPLOADING → COMPLETED
                ↓           ↓            ↓
              FAILED      FAILED       FAILED
```

---

## 10. Database Schema

### 10.1 Tables

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    google_id VARCHAR(255) UNIQUE NOT NULL,
    google_access_token TEXT,
    google_refresh_token TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User settings
CREATE TABLE settings (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    silence_threshold_db FLOAT DEFAULT -40,
    silence_min_duration FLOAT DEFAULT 0.5,
    silence_padding FLOAT DEFAULT 0.1,
    min_clips INTEGER DEFAULT 10,
    max_clip_duration INTEGER DEFAULT 180,
    viral_signals JSONB DEFAULT '[]',
    email_on_complete BOOLEAN DEFAULT true,
    input_folder_id VARCHAR(255),
    output_folder_id VARCHAR(255),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Processing jobs
CREATE TABLE jobs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    stream_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    current_step VARCHAR(100),
    progress INTEGER DEFAULT 0,
    error_message TEXT,

    -- Input files
    input_folder_id VARCHAR(255),
    full_stream_file_id VARCHAR(255),
    webcam_file_id VARCHAR(255),
    screen_file_id VARCHAR(255),

    -- Output info
    output_folder_id VARCHAR(255),
    chapters_count INTEGER,
    clips_count INTEGER,
    original_duration FLOAT,
    final_duration FLOAT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Processing history/logs
CREATE TABLE job_logs (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES jobs(id),
    level VARCHAR(20),  -- info, warning, error
    message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 11. Security Considerations

### 11.1 Authentication

- Google OAuth 2.0 for user authentication
- JWT tokens for API authentication
- Refresh token rotation

### 11.2 Authorization

- Users can only access their own jobs and settings
- Google Drive access scoped to specific folders
- API rate limiting per user

### 11.3 Data Privacy

- Video files processed in temp storage, deleted after completion
- Transcripts stored only in user's Google Drive
- No video content stored on service servers long-term

### 11.4 API Keys

- Return Zero and Anthropic API keys stored securely (env vars / secret manager)
- User's Google tokens encrypted at rest

---

## 12. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         VERCEL                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Next.js Frontend                       │    │
│  │              (Static + Server Components)                │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GOOGLE CLOUD                                  │
│                                                                  │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │   Cloud Run     │    │   Cloud Run     │                     │
│  │   (API)         │◄──►│   (Worker)      │                     │
│  └────────┬────────┘    └────────┬────────┘                     │
│           │                      │                               │
│           ▼                      ▼                               │
│  ┌─────────────────────────────────────────┐                    │
│  │           Cloud Memorystore              │                    │
│  │              (Redis)                     │                    │
│  └─────────────────────────────────────────┘                    │
│                      │                                           │
│                      ▼                                           │
│  ┌─────────────────────────────────────────┐                    │
│  │              Cloud SQL                   │                    │
│  │            (PostgreSQL)                  │                    │
│  └─────────────────────────────────────────┘                    │
│                                                                  │
│  ┌─────────────────────────────────────────┐                    │
│  │           Cloud Storage                  │                    │
│  │         (Temp file storage)              │                    │
│  └─────────────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 13. Workflow Example

### 13.1 End-to-End Flow

1. **User finishes streaming**
   - OBS saves 3 files to local folder
   - Google Drive desktop app syncs to cloud

2. **User organizes files**
   - Creates folder `2025-01-15_market_analysis` in `/StreamAutomation/Input`
   - Moves/copies the 3 video files into it

3. **Service detects new files** (within 60 seconds)
   - File watcher sees new folder with 3 videos
   - Validates files are fully uploaded
   - Creates job, sends to queue

4. **Processing begins**
   - Downloads files to temp storage
   - Web dashboard shows "Processing..."
   - Each step updates progress in real-time

5. **Processing completes** (10-30 minutes depending on length)
   - Outputs uploaded to `/StreamAutomation/Output/2025-01-15_market_analysis/`
   - Email notification sent
   - Dashboard shows completion with stats

6. **User imports to Premiere**
   - Downloads `timeline.xml` from Google Drive
   - File > Import in Premiere
   - Makes final adjustments and exports

---

## 14. Future Enhancements (v3.0+)

| Feature | Priority | Notes |
|---------|----------|-------|
| Dropbox/OneDrive support | Medium | Alternative cloud storage |
| Direct Premiere plugin | Medium | Skip XML import |
| Thumbnail generation | Medium | AI-generated thumbnails |
| Auto-upload to YouTube | Low | Draft upload for review |
| Team/multi-user support | Low | Collaboration features |
| Mobile app | Low | iOS/Android companion |
| Webhook integrations | Low | Zapier, IFTTT, etc. |

---

## 15. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Detection latency | < 2 minutes | Time from upload complete to job start |
| Processing time | < 15 min/hour of video | Total processing duration |
| Uptime | 99.9% | Service availability |
| Error rate | < 1% | Failed jobs / total jobs |
| User satisfaction | Zero manual intervention | Fully automated workflow |

---

## 16. Open Questions

1. **Hosting budget** - What's the acceptable monthly cost for cloud services?

2. **Notification preferences** - Email only, or also Discord/Slack/Telegram?

3. **Re-processing** - Should users be able to adjust settings and re-process? (Current answer: Yes)

4. **Storage retention** - How long to keep outputs in Google Drive? (User manages their own Drive)

5. **Multi-language expansion** - Any plans for languages beyond Korean/English?

---

## Appendix A: Google Drive API Scopes

Required OAuth scopes:
```
https://www.googleapis.com/auth/drive.file
https://www.googleapis.com/auth/drive.metadata.readonly
https://www.googleapis.com/auth/userinfo.email
https://www.googleapis.com/auth/userinfo.profile
```

---

## Appendix B: File Detection Algorithm

```python
def is_folder_ready_for_processing(folder) -> bool:
    """
    Check if a folder is ready for processing.
    """
    # 1. Check required files exist
    files = list_files_in_folder(folder.id)
    file_names = {f.name.lower() for f in files}

    required_patterns = ['full_stream', 'webcam', 'screen']
    video_extensions = ['.mp4', '.mov', '.mkv']

    found_files = {}
    for pattern in required_patterns:
        for f in files:
            name_lower = f.name.lower()
            if pattern in name_lower:
                if any(name_lower.endswith(ext) for ext in video_extensions):
                    found_files[pattern] = f
                    break

    if len(found_files) != 3:
        return False

    # 2. Check files are fully uploaded (size stable for 60s)
    for f in found_files.values():
        if not is_file_upload_complete(f):
            return False

    # 3. Check not already processed
    if is_folder_in_history(folder.id):
        return False

    return True
```
