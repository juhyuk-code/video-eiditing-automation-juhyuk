# Product Requirements Document (PRD)
# Stream Automation - Web Service Edition

**Version:** 2.0
**Author:** Juhyuk
**Last Updated:** 2025-01-22
**Status:** Draft
**Monthly Budget:** $100 USD

---

## 1. Executive Summary

### 1.1 Problem Statement

Creating content from livestreams is a time-consuming manual process. After each stream, the creator must:
- Manually sync multiple video sources
- Scrub through hours of footage to find silence gaps
- Identify clip-worthy moments for short-form content
- Create separate timelines for long-form and short-form
- Write captions, titles, and chapter timestamps
- Design thumbnails

This process can take 3-5+ hours per livestream, limiting content output and creator productivity.

### 1.2 Solution

A **fully automated web service** that:
1. **Watches** a Google Drive folder for new OBS recordings
2. **Automatically processes** detected files:
   - Transcribes (Korean/English via Return Zero API)
   - Removes silences
   - Identifies chapters for long-form content
   - Detects viral moments for short-form clips
   - Generates Adobe Premiere timelines
   - Creates captions, titles, and thumbnail suggestions
3. **Uploads outputs** to organized Google Drive folders
4. **Notifies** via Telegram when processing is complete

### 1.3 Target User

- **Primary:** Juhyuk (solo creator)
- **Content Type:** Market analysis, trading insights, financial commentary
- **Languages:** Korean and English (code-switching)
- **Workflow:** Records with OBS → Files sync to Google Drive → Service handles everything automatically

---

## 2. Goals and Non-Goals

### 2.1 Goals

| ID | Goal | Success Metric |
|----|------|----------------|
| G1 | Zero-touch processing | No manual intervention after OBS recording stops |
| G2 | Cloud-based workflow | Process from any device, anywhere |
| G3 | Automatic file organization | Inputs/outputs organized in Google Drive |
| G4 | Real-time status updates | Telegram notifications + web dashboard |
| G5 | Minimum 10 viral clips | At least 10 short-form clips per stream |
| G6 | Accurate transcription | < 5% word error rate for Korean/English |
| G7 | Seamless Premiere integration | One-click XML import, no adjustments needed |

### 2.2 Non-Goals (v2.0)

| ID | Non-Goal | Reason |
|----|----------|--------|
| NG1 | Multi-user support | Single-user service for now |
| NG2 | Mobile app | Web app + Telegram is sufficient |
| NG3 | Direct YouTube/TikTok upload | Keep human in the loop for final review |
| NG4 | Real-time streaming processing | Focus on post-stream workflow |
| NG5 | Automatic thumbnail image generation | Provide concepts only |

---

## 3. Core Features (Complete List)

### 3.1 Input Processing

| Feature | Description |
|---------|-------------|
| **3 Video Sources** | full_stream (composited), webcam (face), screen (computer) |
| **Auto-sync** | All 3 sources synced via OBS Source Record plugin |
| **Format Support** | MP4, MOV, MKV (H.264, H.265, ProRes) |
| **Google Drive Watch** | Auto-detect new recordings in /Input folder |
| **Upload Validation** | Wait for files to finish uploading before processing |

### 3.2 Audio Processing

| Feature | Description |
|---------|-------------|
| **Audio Extraction** | Extract audio from full_stream via FFmpeg |
| **Silence Detection** | FFmpeg silencedetect filter |
| **Configurable Threshold** | Default: -40 dB |
| **Configurable Min Duration** | Default: 0.5 seconds |
| **Padding** | Keep 0.1s around speech to avoid harsh cuts |

### 3.3 Transcription (Return Zero API)

| Feature | Description |
|---------|-------------|
| **Korean Optimization** | Return Zero's "sommers" model for Korean |
| **English Support** | Handles Korean/English code-switching |
| **Word-level Timestamps** | Precise timing for each word |
| **Language Detection** | Auto-detect language per segment |
| **Output Formats** | JSON (full), TXT (plain), SRT, VTT |

### 3.4 Long-Form Analysis (Claude API)

| Feature | Description |
|---------|-------------|
| **Chapter Detection** | Identify topic changes for YouTube chapters |
| **Min Chapter Duration** | 60 seconds minimum |
| **Max Chapters** | Up to 20 chapters per stream |
| **Chapter Data** | title, start, end, summary, keywords |
| **Title Ideas** | 5 YouTube title suggestions (SEO-optimized) |
| **Thumbnail Concepts** | 3 visual concepts for thumbnails |
| **Tags** | 10-15 relevant YouTube tags |
| **Description Template** | Ready-to-use video description |
| **Stream Summary** | 2-3 sentence overview |

### 3.5 Short-Form Analysis (Claude API)

| Feature | Description |
|---------|-------------|
| **Viral Moment Detection** | AI identifies clip-worthy moments |
| **Minimum Clips** | At least 10 clips per stream |
| **Maximum Clips** | Up to 30 clips |
| **Clip Duration** | Up to 180 seconds (YouTube Shorts limit) |
| **Context-Driven Length** | No minimum - clip length based on content context |
| **No Overlap** | Clips do not overlap with each other |

#### 3.5.1 Viral Clip Categories

| Category | Description | Detection Signals |
|----------|-------------|-------------------|
| `bold_prediction` | Strong market calls, price predictions | "I think...", "This will...", definitive language |
| `insight` | Unique analysis, contrarian takes | "What people don't realize...", "The key here is..." |
| `reaction` | Emotional responses to market moves | Exclamations, tone shifts |
| `explanation` | Clear educational moments | "Let me explain...", "Here's how this works..." |
| `callout` | Validating past predictions | "I told you...", "Remember when I said..." |

#### 3.5.2 Viral Signals (Configurable)

Default signals for market/trading content:
- Bold market predictions
- Contrarian takes
- Price calls
- "I told you so" moments
- Surprising insights
- Emotional reactions

#### 3.5.3 Clip Metadata

Each clip includes:
```json
{
  "id": "clip_001",
  "start": 932.5,
  "end": 975.2,
  "duration": 42.7,
  "transcript": "This is exactly why I said Bitcoin would...",
  "category": "bold_prediction",
  "viral_score": 0.92,
  "title_suggestions": [
    "I Called It - Bitcoin's Next Move",
    "Why Everyone Got This Wrong"
  ],
  "hook": "This is exactly why I said...",
  "context": "Strong conviction call that proved correct"
}
```

### 3.6 Adobe Premiere Export (FCP7 XML)

#### 3.6.1 Long-Form Timeline (16:9)

| Track | Content |
|-------|---------|
| V1 | `full_stream` video with silences removed |
| A1 | `full_stream` audio synced with cuts |
| Markers | Chapter markers at topic transitions |

**Output:** `timeline.xml` - Import directly into Premiere

#### 3.6.2 Short-Form Timeline (9:16)

| Track | Content |
|-------|---------|
| V1 | `webcam` video (top 40% of frame) |
| V2 | `screen` video (bottom 60% of frame) |
| A1 | Audio from `full_stream` |
| Markers | Clip boundaries |

**Layout:**
```
┌─────────────┐
│   WEBCAM    │  ← 40% height (face, reactions)
│─────────────│
│             │
│   SCREEN    │  ← 60% height (charts, content)
│             │
└─────────────┘
    1080x1920 (9:16)
```

**Output:** `timeline.xml` - All clips in sequence with markers

### 3.7 Captions

| Output | Format | Description |
|--------|--------|-------------|
| Long-form | SRT | Full transcript with timestamps |
| Long-form | VTT | WebVTT for YouTube |
| Short-form | SRT per clip | Individual caption file for each clip |

### 3.8 Notifications (Telegram)

| Event | Notification |
|-------|--------------|
| New files detected | "📁 New stream detected: {name}. Processing will begin shortly." |
| Processing started | "🎬 Processing started: {name}" |
| Processing complete | "✅ Complete: {name}\n📺 {chapters} chapters\n📱 {clips} clips\n📂 View outputs: {link}" |
| Processing failed | "❌ Failed: {name}\n{error_message}" |

---

## 4. Output Specifications

### 4.1 Google Drive Output Structure

```
📁 StreamAutomation/
│
├── 📁 Input/                              ← User uploads here
│   └── 📁 2025-01-15_market_analysis/
│       ├── 📄 full_stream.mp4
│       ├── 📄 webcam.mp4
│       └── 📄 screen.mp4
│
└── 📁 Output/                             ← Service creates this
    └── 📁 2025-01-15_market_analysis/
        │
        ├── 📁 longform/
        │   ├── 📄 timeline.xml            ← Import to Premiere
        │   ├── 📄 captions.srt            ← Full subtitles
        │   ├── 📄 captions.vtt            ← YouTube format
        │   ├── 📄 chapters.txt            ← YouTube chapters
        │   └── 📄 suggestions.md          ← Titles, thumbnails, tags
        │
        ├── 📁 shortform/
        │   ├── 📄 timeline.xml            ← All clips in sequence
        │   ├── 📄 clips_metadata.json     ← Full clip data
        │   ├── 📁 captions/
        │   │   ├── 📄 clip_001.srt
        │   │   ├── 📄 clip_002.srt
        │   │   └── ... (one per clip)
        │   └── 📄 suggestions.md          ← Title per clip
        │
        └── 📁 transcript/
            ├── 📄 full_transcript.json    ← Word-level timestamps
            └── 📄 full_transcript.txt     ← Plain text
```

### 4.2 Long-Form suggestions.md Format

```markdown
# Long-Form Content Suggestions

## Title Ideas
1. "Why Bitcoin Will Hit $100K This Month (Here's The Data)"
2. "Market Analysis: The Bull Run Everyone's Missing"
3. "I Predicted This Crash - Here's What's Next"
4. "[날짜] 비트코인 시장 분석 - 지금 사야 하는 이유"
5. "This Chart Pattern Changes Everything"

## Thumbnail Concepts
1. Split frame: Surprised face + Bitcoin chart spiking up
2. Bold text "$100K" with upward arrow, your face pointing
3. Before/after chart comparison with shocked expression

## YouTube Chapters
00:00 Introduction
02:34 Market Overview
15:22 Bitcoin Analysis
32:10 Altcoin Picks
45:33 Q&A Session

## Tags
bitcoin, crypto, market analysis, trading, 비트코인, 암호화폐, cryptocurrency, BTC,
technical analysis, price prediction, bull run, crypto news

## Description Template
🔥 In today's stream, we cover...

📊 Chapters:
[chapters auto-inserted]

🔔 Subscribe for daily market analysis
💬 Join the community: [links]

#bitcoin #crypto #trading
```

### 4.3 Short-Form suggestions.md Format

```markdown
# Short-Form Clips

## CLIP_001
**Category:** bold_prediction
**Duration:** 0:45
**Viral Score:** 0.95

**Hook:** "This is exactly why I said..."

**Why it's clip-worthy:** Strong conviction call with supporting data

**Title Ideas:**
- "I Called It 📈"
- "Bitcoin's Next Move (I Predicted This)"
- "Nobody Believed Me..."

---

## CLIP_002
**Category:** insight
**Duration:** 1:12
**Viral Score:** 0.89

**Hook:** "What people don't realize about this chart..."

**Why it's clip-worthy:** Unique perspective that contradicts popular opinion

**Title Ideas:**
- "The Chart Everyone's Reading Wrong"
- "This Changes Everything"
- "Why I'm Buying When Everyone's Selling"

---
[continues for all clips]
```

---

## 5. System Architecture

### 5.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER'S ENVIRONMENT                              │
│                                                                              │
│  ┌─────────────┐         ┌─────────────────────────────────────────────┐    │
│  │  OBS Studio │ ──────► │              Google Drive                    │    │
│  │  (Records)  │  sync   │                                              │    │
│  └─────────────┘         │  📁 StreamAutomation/Input/                  │    │
│                          │    📁 2025-01-15_market_analysis/            │    │
│                          │      📄 full_stream.mp4                      │    │
│                          │      📄 webcam.mp4                           │    │
│                          │      📄 screen.mp4                           │    │
│                          └─────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────┐                                                            │
│  │  Telegram   │◄─────────── Notifications                                  │
│  │  App        │                                                            │
│  └─────────────┘                                                            │
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
│  │  • Dashboard     │    │  • Google OAuth  │    │                  │       │
│  │  • Job status    │    │  • Job queue     │    │  • File watcher  │       │
│  │  • Settings      │    │  • Telegram bot  │    │  • Audio extract │       │
│  │  • History       │    │  • Google Drive  │    │  • Silence detect│       │
│  │  • Clip preview  │    │  • WebSocket     │    │  • Transcription │       │
│  └──────────────────┘    └──────────────────┘    │  • Claude analysis│      │
│                                   │              │  • XML generation│       │
│                                   ▼              │  • Upload outputs│       │
│                          ┌──────────────────┐    │  • Send Telegram │       │
│                          │    Database      │    └──────────────────┘       │
│                          │   (PostgreSQL)   │              │                │
│                          │                  │◄─────────────┘                │
│                          │  • Jobs          │                               │
│                          │  • User settings │                               │
│                          │  • History       │                               │
│                          │  • Clip data     │                               │
│                          └──────────────────┘                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          │ External APIs
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL SERVICES                                  │
│                                                                              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐       │
│  │  Return Zero     │    │  Claude API      │    │  Telegram Bot    │       │
│  │  (Transcription) │    │  (Analysis)      │    │  API             │       │
│  │                  │    │                  │    │                  │       │
│  │  • Korean STT    │    │  • Chapters      │    │  • Notifications │       │
│  │  • English STT   │    │  • Viral clips   │    │  • Status updates│       │
│  │  • Timestamps    │    │  • Titles        │    │                  │       │
│  └──────────────────┘    │  • Thumbnails    │    └──────────────────┘       │
│                          └──────────────────┘                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Processing Pipeline (Detailed)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PROCESSING PIPELINE                                │
└─────────────────────────────────────────────────────────────────────────────┘

Step 1: DETECT (File Watcher - runs every 60 seconds)
┌─────────────────────────────────────────────────────────────────────────────┐
│  • List folders in Google Drive /StreamAutomation/Input                     │
│  • Check each folder for 3 required files (full_stream, webcam, screen)     │
│  • Validate files are fully uploaded (size stable for 60s)                  │
│  • Check folder not already processed                                        │
│  • If ready → Create job → Send to queue → Notify Telegram                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
Step 2: DOWNLOAD
┌─────────────────────────────────────────────────────────────────────────────┐
│  • Download all 3 video files from Google Drive                             │
│  • Store in temporary cloud storage (GCS)                                   │
│  • Validate file integrity                                                  │
│  • Update job status: "Downloading..." (10%)                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
Step 3: AUDIO PROCESSING
┌─────────────────────────────────────────────────────────────────────────────┐
│  • Extract audio from full_stream.mp4 using FFmpeg                          │
│  • Output: 16kHz mono WAV for transcription                                 │
│  • Detect silences using FFmpeg silencedetect                               │
│  • Generate edit regions (content to keep)                                  │
│  • Update job status: "Processing audio..." (20%)                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
Step 4: TRANSCRIPTION (Return Zero API)
┌─────────────────────────────────────────────────────────────────────────────┐
│  • Upload audio to Return Zero API                                          │
│  • Poll for completion                                                      │
│  • Receive transcript with word-level timestamps                            │
│  • Detect language breakdown (Korean %, English %)                          │
│  • Save: full_transcript.json, full_transcript.txt                          │
│  • Update job status: "Transcribing..." (40%)                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
Step 5: LONG-FORM ANALYSIS (Claude API)
┌─────────────────────────────────────────────────────────────────────────────┐
│  • Send transcript to Claude                                                │
│  • Prompt for chapter detection, title ideas, thumbnail concepts            │
│  • Receive: chapters[], title_ideas[], thumbnail_concepts[], tags[]         │
│  • Generate chapters.txt (YouTube format)                                   │
│  • Generate suggestions.md                                                  │
│  • Update job status: "Analyzing long-form..." (55%)                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
Step 6: SHORT-FORM ANALYSIS (Claude API)
┌─────────────────────────────────────────────────────────────────────────────┐
│  • Send transcript to Claude with viral signals config                      │
│  • Prompt for minimum 10 viral moments                                      │
│  • Receive: clips[] with id, start, end, category, score, titles, hook     │
│  • Sort by viral_score, ensure no overlaps                                  │
│  • Generate clips_metadata.json                                             │
│  • Generate suggestions.md (per clip)                                       │
│  • Update job status: "Analyzing short-form..." (70%)                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
Step 7: PREMIERE XML GENERATION
┌─────────────────────────────────────────────────────────────────────────────┐
│  • Generate long-form timeline.xml (FCP7 format)                            │
│    - full_stream on V1/A1 with silence cuts                                 │
│    - Chapter markers                                                         │
│  • Generate short-form timeline.xml (FCP7 format)                           │
│    - webcam on V1 (top 40%, scaled)                                         │
│    - screen on V2 (bottom 60%, scaled)                                      │
│    - Audio on A1                                                            │
│    - Clip boundary markers                                                   │
│  • Update job status: "Generating timelines..." (80%)                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
Step 8: CAPTION GENERATION
┌─────────────────────────────────────────────────────────────────────────────┐
│  • Generate long-form captions.srt and captions.vtt                         │
│  • Generate per-clip SRT files (clip_001.srt, clip_002.srt, ...)           │
│  • Update job status: "Generating captions..." (85%)                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
Step 9: UPLOAD TO GOOGLE DRIVE
┌─────────────────────────────────────────────────────────────────────────────┐
│  • Create output folder structure in /StreamAutomation/Output               │
│  • Upload all generated files                                               │
│  • Update job status: "Uploading..." (95%)                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
Step 10: COMPLETE & NOTIFY
┌─────────────────────────────────────────────────────────────────────────────┐
│  • Update job status: "Completed" (100%)                                    │
│  • Send Telegram notification with summary                                  │
│  • Clean up temporary files                                                 │
│  • Log processing metrics                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

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
│  │     Step 4/10: Transcribing... (40%)                    │   │
│  │     ████████████░░░░░░░░░░░░░░░░░░░░                    │   │
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
│  │  │    Duration: 1:32:45 → 1:18:22 (14m silences)   │   │   │
│  │  │    📺 8 chapters • 📱 12 clips                   │   │   │
│  │  │    [View Details] [Open in Drive] [Re-process]  │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │                                                         │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │ ✅ 2025-01-13 Bitcoin Analysis                  │   │   │
│  │  │    Duration: 2:05:12 → 1:48:33 (17m silences)   │   │   │
│  │  │    📺 10 chapters • 📱 15 clips                  │   │   │
│  │  │    [View Details] [Open in Drive] [Re-process]  │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │                                                         │   │
│  │  [View All History]                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 6.1.2 Job Detail Page

```
┌─────────────────────────────────────────────────────────────────┐
│  ← 2025-01-15 Market Analysis                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Status: ✅ Completed                                           │
│  Original: 1:32:45 → Final: 1:18:22 (14:23 silences removed)   │
│  Languages: Korean 72% • English 28%                           │
│  Processed: 2 hours ago                                         │
│                                                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 📺 LONG-FORM OUTPUT                         [Open in Drive] │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                         │   │
│  │  📄 Files:                                              │   │
│  │     • timeline.xml (Premiere import)                    │   │
│  │     • captions.srt / captions.vtt                       │   │
│  │     • chapters.txt                                      │   │
│  │     • suggestions.md                                    │   │
│  │                                                         │   │
│  │  📑 Chapters (8):                                       │   │
│  │     00:00 Introduction                                  │   │
│  │     02:34 Market Overview                               │   │
│  │     15:22 Bitcoin Analysis                              │   │
│  │     28:45 Ethereum Update                               │   │
│  │     42:10 Altcoin Picks                                 │   │
│  │     55:33 Risk Management                               │   │
│  │     1:08:20 Q&A Session                                 │   │
│  │     1:15:45 Closing Thoughts                            │   │
│  │                                                         │   │
│  │  💡 Title Ideas:                                        │   │
│  │     1. "Why Bitcoin Will Hit $100K This Month"          │   │
│  │     2. "The Bull Run Everyone's Missing"                │   │
│  │     3. "I Predicted This - Here's What's Next"          │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 📱 SHORT-FORM CLIPS (12)                    [Open in Drive] │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                         │   │
│  │  ┌───────────────────────────────────────────────────┐ │   │
│  │  │ CLIP_001 • bold_prediction • ⭐ 0.95              │ │   │
│  │  │ 0:45 duration • starts at 15:32                   │ │   │
│  │  │                                                   │ │   │
│  │  │ "This is exactly why I said Bitcoin would..."     │ │   │
│  │  │                                                   │ │   │
│  │  │ Titles: "I Called It 📈" / "Nobody Believed Me"   │ │   │
│  │  └───────────────────────────────────────────────────┘ │   │
│  │                                                         │   │
│  │  ┌───────────────────────────────────────────────────┐ │   │
│  │  │ CLIP_002 • insight • ⭐ 0.89                      │ │   │
│  │  │ 1:12 duration • starts at 28:15                   │ │   │
│  │  │                                                   │ │   │
│  │  │ "What people don't realize about this chart..."   │ │   │
│  │  │                                                   │ │   │
│  │  │ Titles: "The Chart Everyone's Missing" / "..."    │ │   │
│  │  └───────────────────────────────────────────────────┘ │   │
│  │                                                         │   │
│  │  [Show all 12 clips...]                                │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  [🔄 Re-process with different settings]                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 6.1.3 Settings Page

```
┌─────────────────────────────────────────────────────────────────┐
│  Settings                                            [← Back]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🔗 GOOGLE DRIVE                                          │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  Status: ✅ Connected as juhyuk@gmail.com               │   │
│  │  Input folder: /StreamAutomation/Input                  │   │
│  │  Output folder: /StreamAutomation/Output                │   │
│  │  [Reconnect] [Change Folders]                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 📱 TELEGRAM NOTIFICATIONS                                │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  Status: ✅ Connected                                   │   │
│  │  Chat ID: 123456789                                     │   │
│  │                                                         │   │
│  │  Notify on:                                             │   │
│  │  [x] New files detected                                 │   │
│  │  [x] Processing started                                 │   │
│  │  [x] Processing completed                               │   │
│  │  [x] Processing failed                                  │   │
│  │                                                         │   │
│  │  [Send Test Message] [Reconnect]                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🔊 SILENCE DETECTION                                     │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  Threshold: [-40] dB        (lower = more aggressive)   │   │
│  │  Min duration: [0.5] sec    (shorter silences kept)     │   │
│  │  Padding: [0.1] sec         (buffer around speech)      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🎬 SHORT-FORM CLIPS                                      │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  Minimum clips per stream: [10]                         │   │
│  │  Maximum clip duration: [180] seconds                   │   │
│  │                                                         │   │
│  │  Viral signals (what to look for):                      │   │
│  │  [x] Bold market predictions                            │   │
│  │  [x] Contrarian takes                                   │   │
│  │  [x] Price calls                                        │   │
│  │  [x] "I told you so" moments                            │   │
│  │  [x] Surprising insights                                │   │
│  │  [x] Emotional reactions                                │   │
│  │                                                         │   │
│  │  Custom signal: [________________] [+ Add]              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 📺 LONG-FORM SETTINGS                                    │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  Min chapter duration: [60] seconds                     │   │
│  │  Max chapters: [20]                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│                                          [Save Settings]        │
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
| Real-time | Server-Sent Events | Live progress updates |
| Auth | NextAuth.js | Google OAuth |

### 7.2 Backend

| Component | Technology | Notes |
|-----------|------------|-------|
| API Framework | FastAPI | Python, async support |
| Task Queue | Celery | Background job processing |
| Message Broker | Redis | For Celery + caching |
| Database | PostgreSQL | Job history, settings |
| File Storage | Google Drive API | Primary storage |
| Temp Storage | Google Cloud Storage | Processing temp files |
| Telegram | python-telegram-bot | Notifications |

### 7.3 Processing (same as CLI version)

| Component | Technology | Notes |
|-----------|------------|-------|
| Audio Extraction | FFmpeg | Via ffmpeg-python |
| Silence Detection | FFmpeg | silencedetect filter |
| Transcription | Return Zero API | Korean/English STT |
| Analysis | Claude API (Sonnet) | Chapter + viral detection |
| XML Generation | Python xml.etree | FCP7 format |

### 7.4 External Services

| Service | Purpose | Monthly Cost (Est.) |
|---------|---------|---------------------|
| Return Zero | Transcription | ~$20-30 |
| Anthropic Claude | Analysis | ~$10-20 |
| Telegram Bot | Notifications | Free |
| Google Drive | Storage | User's own quota |
| **Total API Costs** | | **~$30-50** |

### 7.5 Infrastructure

| Component | Service | Monthly Cost (Est.) |
|-----------|---------|---------------------|
| Frontend | Vercel (Hobby) | Free |
| Backend API | Google Cloud Run | ~$10-20 |
| Worker | Google Cloud Run | ~$10-20 |
| Database | Cloud SQL (Basic) | ~$10 |
| Redis | Cloud Memorystore (Basic) | ~$10 |
| Temp Storage | Cloud Storage | ~$5 |
| **Total Infrastructure** | | **~$45-65** |

### 7.6 Total Monthly Cost: **~$75-100**

---

## 8. Database Schema

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    google_id VARCHAR(255) UNIQUE NOT NULL,
    google_access_token TEXT,
    google_refresh_token TEXT,
    telegram_chat_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User settings
CREATE TABLE settings (
    user_id UUID PRIMARY KEY REFERENCES users(id),

    -- Google Drive
    input_folder_id VARCHAR(255),
    output_folder_id VARCHAR(255),

    -- Silence detection
    silence_threshold_db FLOAT DEFAULT -40,
    silence_min_duration FLOAT DEFAULT 0.5,
    silence_padding FLOAT DEFAULT 0.1,

    -- Short-form
    min_clips INTEGER DEFAULT 10,
    max_clip_duration INTEGER DEFAULT 180,
    viral_signals JSONB DEFAULT '["bold market predictions", "contrarian takes", "price calls", "I told you so moments", "surprising insights", "emotional reactions"]',

    -- Long-form
    min_chapter_duration INTEGER DEFAULT 60,
    max_chapters INTEGER DEFAULT 20,

    -- Notifications
    notify_on_detected BOOLEAN DEFAULT true,
    notify_on_started BOOLEAN DEFAULT true,
    notify_on_completed BOOLEAN DEFAULT true,
    notify_on_failed BOOLEAN DEFAULT true,

    updated_at TIMESTAMP DEFAULT NOW()
);

-- Processing jobs
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    stream_name VARCHAR(255) NOT NULL,

    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- pending, downloading, processing, transcribing, analyzing_longform,
    -- analyzing_shortform, generating, uploading, completed, failed
    current_step VARCHAR(100),
    progress INTEGER DEFAULT 0,
    error_message TEXT,

    -- Input files (Google Drive IDs)
    input_folder_id VARCHAR(255),
    full_stream_file_id VARCHAR(255),
    webcam_file_id VARCHAR(255),
    screen_file_id VARCHAR(255),

    -- Duration info
    original_duration FLOAT,
    final_duration FLOAT,
    silence_removed FLOAT,

    -- Output info
    output_folder_id VARCHAR(255),

    -- Long-form results
    chapters_count INTEGER,
    title_ideas JSONB,
    thumbnail_concepts JSONB,

    -- Short-form results
    clips_count INTEGER,
    clips_data JSONB,  -- Full clip metadata

    -- Transcript info
    word_count INTEGER,
    language_breakdown JSONB,  -- {"ko": 72.5, "en": 27.5}

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Job logs for debugging
CREATE TABLE job_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id),
    level VARCHAR(20),  -- info, warning, error
    step VARCHAR(100),
    message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 9. API Endpoints

### 9.1 Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/auth/google` | Initiate Google OAuth |
| GET | `/api/auth/google/callback` | OAuth callback |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/me` | Get current user |

### 9.2 Telegram

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/telegram/connect` | Get bot link for connection |
| POST | `/api/telegram/verify` | Verify connection with code |
| POST | `/api/telegram/test` | Send test notification |
| DELETE | `/api/telegram/disconnect` | Disconnect Telegram |

### 9.3 Jobs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/jobs` | List all jobs (paginated) |
| GET | `/api/jobs/current` | Get currently processing job |
| GET | `/api/jobs/{id}` | Get job details |
| POST | `/api/jobs/{id}/reprocess` | Re-process a job |
| DELETE | `/api/jobs/{id}` | Delete job and outputs |

### 9.4 Settings

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/settings` | Get user settings |
| PUT | `/api/settings` | Update settings |
| POST | `/api/settings/test-drive` | Test Drive connection |

### 9.5 Real-time Updates

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/events` | SSE stream for real-time updates |

```typescript
// Event types
interface JobEvent {
  type: 'job_detected' | 'job_started' | 'job_progress' | 'job_completed' | 'job_failed';
  jobId: string;
  data: {
    streamName?: string;
    step?: string;
    progress?: number;
    message?: string;
    error?: string;
    chaptersCount?: number;
    clipsCount?: number;
  };
}
```

---

## 10. Telegram Bot Setup

### 10.1 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Start bot, get connection code |
| `/status` | Get current processing status |
| `/history` | List recent processed streams |
| `/help` | Show available commands |

### 10.2 Notification Messages

**New files detected:**
```
📁 New stream detected!

Stream: 2025-01-15 Market Analysis
Files: 3 videos found
Status: Queued for processing

Processing will begin shortly.
```

**Processing started:**
```
🎬 Processing started

Stream: 2025-01-15 Market Analysis
Started: Just now

You'll be notified when complete.
```

**Processing complete:**
```
✅ Processing complete!

Stream: 2025-01-15 Market Analysis
Duration: 1:32:45 → 1:18:22
Silences removed: 14:23

📺 Long-form:
• 8 chapters detected
• 5 title ideas generated

📱 Short-form:
• 12 viral clips found
• Total clip duration: 8:45

📂 View outputs:
drive.google.com/...

🔗 Open dashboard:
streamauto.app/jobs/abc123
```

**Processing failed:**
```
❌ Processing failed

Stream: 2025-01-15 Market Analysis
Error: Transcription service timeout

Please try re-processing or contact support.

🔗 View details:
streamauto.app/jobs/abc123
```

---

## 11. Deployment

### 11.1 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         VERCEL                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Next.js Frontend                       │    │
│  │              streamauto.app                              │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTPS
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GOOGLE CLOUD PLATFORM                         │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Cloud Run                             │    │
│  │  ┌─────────────────┐    ┌─────────────────┐             │    │
│  │  │   API Service   │    │ Worker Service  │             │    │
│  │  │   (FastAPI)     │    │   (Celery)      │             │    │
│  │  │   api.streamauto│    │                 │             │    │
│  │  └────────┬────────┘    └────────┬────────┘             │    │
│  │           │                      │                       │    │
│  └───────────┼──────────────────────┼───────────────────────┘    │
│              │                      │                            │
│  ┌───────────▼──────────────────────▼───────────────────────┐    │
│  │                  Cloud Memorystore                        │    │
│  │                      (Redis)                              │    │
│  └───────────────────────────────────────────────────────────┘    │
│                              │                                    │
│  ┌───────────────────────────▼───────────────────────────────┐    │
│  │                      Cloud SQL                             │    │
│  │                   (PostgreSQL)                             │    │
│  └───────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐    │
│  │                   Cloud Storage                            │    │
│  │              (Temporary file storage)                      │    │
│  └───────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 12. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Detection latency | < 2 minutes | Time from upload to job start |
| Processing speed | < 15 min per hour of video | End-to-end processing time |
| Transcription accuracy | > 95% Korean, > 98% English | Manual sampling |
| Viral clip quality | > 90% relevant | User feedback |
| Clip count | ≥ 10 per stream | Automatic count |
| Uptime | 99.9% | Monitoring |
| User satisfaction | Zero manual intervention | Fully automated |

---

## 13. Open Questions Resolved

| Question | Answer |
|----------|--------|
| Budget | $100/month maximum |
| Notifications | Telegram only |
| Re-processing | Yes, with ability to change settings |
| Storage retention | User manages their own Google Drive |
| Languages | Korean and English only |

---

## Appendix A: Google Drive API Scopes

```
https://www.googleapis.com/auth/drive.file
https://www.googleapis.com/auth/drive.metadata.readonly
https://www.googleapis.com/auth/userinfo.email
https://www.googleapis.com/auth/userinfo.profile
```

---

## Appendix B: Environment Variables

```bash
# Google OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# Database
DATABASE_URL=postgresql://...

# Redis
REDIS_URL=redis://...

# External APIs
RTZR_CLIENT_ID=
RTZR_CLIENT_SECRET=
ANTHROPIC_API_KEY=

# Telegram
TELEGRAM_BOT_TOKEN=

# App
NEXT_PUBLIC_API_URL=https://api.streamauto.app
SECRET_KEY=
```
