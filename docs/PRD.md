# Product Requirements Document (PRD)
# Livestream Content Automation System

**Version:** 1.0
**Author:** Juhyuk
**Last Updated:** 2025-01-21
**Status:** Draft

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

An automated pipeline that processes livestream recordings and generates:
- Ready-to-edit Adobe Premiere timelines (long-form and short-form)
- AI-identified viral moments and topic chapters
- Auto-generated captions in Korean and English
- Title and thumbnail suggestions

### 1.3 Target User

- **Primary:** Juhyuk (solo creator)
- **Content Type:** Market analysis, trading insights, financial commentary
- **Languages:** Korean and English (code-switching)
- **Platform:** macOS (Windows support planned for future)

---

## 2. Goals and Non-Goals

### 2.1 Goals

| ID | Goal | Success Metric |
|----|------|----------------|
| G1 | Reduce post-production time | < 30 minutes of manual editing after automation |
| G2 | Identify all clip-worthy moments | 90%+ of viral moments captured |
| G3 | Accurate Korean/English transcription | < 5% word error rate |
| G4 | Seamless Premiere integration | One-click import, no manual adjustments needed |
| G5 | Simple CLI interface | Single command to process a stream |

### 2.2 Non-Goals (v1.0)

| ID | Non-Goal | Reason |
|----|----------|--------|
| NG1 | Automatic upload to YouTube/TikTok | Keep human in the loop for quality control |
| NG2 | Real-time processing during stream | Focus on post-stream workflow first |
| NG3 | GUI application | CLI is sufficient for solo use |
| NG4 | Video rendering/export | Premiere handles final render |
| NG5 | Windows support | macOS first, Windows in v2.0 |
| NG6 | Automatic thumbnail generation | Provide concepts only, manual creation preferred |

---

## 3. User Stories

### 3.1 Primary Workflow

```
AS A content creator
I WANT TO run a single command after my livestream
SO THAT I get ready-to-edit Premiere timelines with all the tedious work done
```

### 3.2 Detailed User Stories

| ID | User Story | Priority |
|----|------------|----------|
| US1 | As a creator, I want silences automatically removed so I don't waste time scrubbing | P0 |
| US2 | As a creator, I want my 3 video sources synced in the timeline so I can switch between them | P0 |
| US3 | As a creator, I want chapters identified so viewers can navigate long videos | P0 |
| US4 | As a creator, I want viral moments identified so I can create short-form content | P0 |
| US5 | As a creator, I want captions generated so I don't have to transcribe manually | P0 |
| US6 | As a creator, I want title suggestions so I have starting points for optimization | P1 |
| US7 | As a creator, I want thumbnail concepts so I have creative direction | P2 |
| US8 | As a creator, I want to customize silence detection thresholds so I can tune for my content | P1 |
| US9 | As a creator, I want to review viral moments before export so I can approve/reject | P2 |

---

## 4. Input Specifications

### 4.1 Video Sources

| Source | Description | Format | Required |
|--------|-------------|--------|----------|
| `full_stream` | Complete stream output (webcam + screen + chat composited) | MP4, MOV | Yes |
| `webcam` | Isolated face camera recording | MP4, MOV | Yes |
| `screen` | Isolated computer screen recording | MP4, MOV | Yes |

### 4.2 Recording Requirements

- All 3 sources must be **frame-synchronized** (OBS Source Record plugin)
- Audio should be present in at least one source (typically `full_stream`)
- Recommended codecs: H.264, H.265, ProRes
- Recommended resolution: 1080p or higher
- Recommended framerate: 30fps or 60fps (consistent across sources)

### 4.3 File Naming Convention (Recommended)

```
{date}_{stream_title}/
├── full_stream.mp4
├── webcam.mp4
└── screen.mp4

Example:
2025-01-15_market_analysis/
├── full_stream.mp4
├── webcam.mp4
└── screen.mp4
```

---

## 5. Output Specifications

### 5.1 Directory Structure

```
output/{stream_name}/
├── longform/
│   ├── timeline.xml              # Premiere-compatible FCP7 XML
│   ├── captions.srt              # Full transcript with timestamps
│   ├── captions.vtt              # WebVTT format (YouTube compatible)
│   ├── chapters.txt              # YouTube chapter format
│   └── suggestions.md            # Title ideas, thumbnail concepts
│
├── shortform/
│   ├── timeline.xml              # All clips in sequence
│   ├── clips_metadata.json       # Detailed clip information
│   ├── captions/
│   │   ├── clip_001.srt
│   │   ├── clip_002.srt
│   │   └── ...
│   └── suggestions.md            # Title ideas per clip
│
└── transcript/
    ├── full_transcript.json      # Complete transcript with word-level timestamps
    ├── full_transcript.txt       # Plain text version
    └── segments.json             # Analyzed segments with metadata
```

### 5.2 Long-Form Output Details

#### 5.2.1 Timeline (timeline.xml)

| Track | Content | Notes |
|-------|---------|-------|
| V1 | `full_stream` video | Primary video, silences removed |
| A1 | `full_stream` audio | Synced with video cuts |
| Markers | Chapter markers | At each topic transition |

#### 5.2.2 Chapters (chapters.txt)

YouTube-compatible format:
```
00:00 Introduction
02:34 Market Overview
15:22 Bitcoin Analysis
32:10 Altcoin Picks
45:33 Q&A
```

#### 5.2.3 Suggestions (suggestions.md)

```markdown
# Long-Form Content Suggestions

## Title Ideas
1. "Why Bitcoin Will Hit $100K This Month (Here's The Data)"
2. "Market Analysis: The Bull Run Everyone's Missing"
3. ...

## Thumbnail Concepts
1. Split frame: Your surprised face + Bitcoin chart going up
2. Text overlay: "$100K" with arrow pointing up
3. ...

## Tags
bitcoin, crypto, market analysis, trading, ...
```

### 5.3 Short-Form Output Details

#### 5.3.1 Timeline (timeline.xml)

| Track | Content | Notes |
|-------|---------|-------|
| V1 | `webcam` video (top half) | Scaled to fit 9:16 top |
| V2 | `screen` video (bottom half) | Scaled to fit 9:16 bottom |
| A1 | Audio from `full_stream` | Synced with clips |
| Markers | Clip boundaries | Separating each viral moment |

#### 5.3.2 Clips Metadata (clips_metadata.json)

```json
{
  "clips": [
    {
      "id": "clip_001",
      "start_time": "00:15:32.500",
      "end_time": "00:16:15.200",
      "duration": 42.7,
      "transcript": "This is exactly why I said Bitcoin would...",
      "category": "bold_prediction",
      "viral_score": 0.92,
      "title_suggestions": [
        "I Called It - Bitcoin's Next Move",
        "Why Everyone Got This Wrong"
      ],
      "hook": "This is exactly why I said..."
    }
  ],
  "total_clips": 12,
  "total_duration": 487.3
}
```

#### 5.3.3 Clip Categories

| Category | Description | Detection Signals |
|----------|-------------|-------------------|
| `bold_prediction` | Strong market calls, price predictions | "I think...", "This will...", definitive language |
| `insight` | Unique analysis, contrarian takes | "What people don't realize...", "The key here is..." |
| `reaction` | Emotional responses to market moves | Exclamations, tone shifts, facial expressions (future) |
| `explanation` | Clear educational moments | "Let me explain...", "Here's how this works..." |
| `callout` | Addressing critics or validating past calls | "I told you...", "Remember when I said..." |

---

## 6. Technical Architecture

### 6.1 System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           CLI INTERFACE                             │
│                         (Python + Click)                            │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR                                 │
│                    (Pipeline Controller)                            │
└───────┬─────────────────┬─────────────────┬─────────────────┬───────┘
        │                 │                 │                 │
        ▼                 ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│    AUDIO      │ │ TRANSCRIPTION │ │   ANALYSIS    │ │   PREMIERE    │
│  PROCESSOR    │ │    CLIENT     │ │    ENGINE     │ │  EXPORTER     │
│               │ │               │ │               │ │               │
│ • Extract     │ │ • Return Zero │ │ • Claude API  │ │ • FCP7 XML    │
│ • Silence     │ │ • Korean/EN   │ │ • Topics      │ │ • Markers     │
│   detection   │ │ • Timestamps  │ │ • Viral clips │ │ • Captions    │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
        │                 │                 │                 │
        ▼                 ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FILE SYSTEM                                 │
│              (Input videos, Output XMLs, Captions)                  │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Module Breakdown

#### 6.2.1 Audio Processor (`src/audio/`)

| Component | Responsibility |
|-----------|----------------|
| `extractor.py` | Extract audio from video files (FFmpeg) |
| `silence.py` | Detect silence regions, generate cut list |
| `waveform.py` | Audio analysis utilities |

**Dependencies:** FFmpeg (via ffmpeg-python)

#### 6.2.2 Transcription Client (`src/transcription/`)

| Component | Responsibility |
|-----------|----------------|
| `rtzr_client.py` | Return Zero API integration |
| `transcript.py` | Transcript data models and utilities |
| `formatter.py` | Convert to SRT, VTT, plain text |

**Dependencies:** Return Zero API, httpx

#### 6.2.3 Analysis Engine (`src/analysis/`)

| Component | Responsibility |
|-----------|----------------|
| `claude_client.py` | Claude API integration |
| `longform.py` | Topic segmentation, chapter detection |
| `shortform.py` | Viral moment detection, clip extraction |
| `suggestions.py` | Title, thumbnail, tag generation |

**Dependencies:** Anthropic Python SDK

#### 6.2.4 Premiere Exporter (`src/premiere/`)

| Component | Responsibility |
|-----------|----------------|
| `xml_generator.py` | Generate FCP7 XML timelines |
| `timeline.py` | Timeline data models |
| `markers.py` | Chapter/clip marker generation |

**Dependencies:** None (pure Python XML generation)

#### 6.2.5 CLI Interface (`src/cli.py`)

| Command | Description |
|---------|-------------|
| `process` | Full pipeline: process a livestream |
| `transcribe` | Transcription only |
| `analyze` | Analysis only (requires transcript) |
| `export` | Premiere export only |
| `config` | View/edit configuration |

### 6.3 Technology Stack

| Component | Technology | Version | Notes |
|-----------|------------|---------|-------|
| Language | Python | 3.11+ | Type hints, async support |
| CLI Framework | Click | 8.x | Commands, options, help |
| HTTP Client | httpx | 0.27+ | Async API calls |
| Video Processing | FFmpeg | 6.x | Via ffmpeg-python wrapper |
| Transcription | Return Zero API | - | Korean-optimized ASR |
| AI Analysis | Claude API | claude-sonnet-4-20250514 | Via Anthropic SDK |
| Configuration | YAML | - | Via PyYAML |
| Data Validation | Pydantic | 2.x | Settings, data models |

### 6.4 Platform Requirements (macOS)

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| macOS | 12.0 (Monterey) | 14.0+ (Sonoma) |
| Python | 3.11 | 3.12 |
| FFmpeg | 6.0 | 6.1+ |
| RAM | 8 GB | 16 GB+ |
| Storage | 50 GB free | 100 GB+ free |
| GPU | Not required | Apple Silicon (faster FFmpeg) |

---

## 7. API Integrations

### 7.1 Return Zero API

**Purpose:** Korean/English transcription with word-level timestamps

**Endpoint:** `https://api.rtzr.ai/v1/transcribe` (to be confirmed)

**Authentication:** API Key (Bearer token)

**Request Flow:**
1. Upload audio file or provide URL
2. Poll for completion
3. Retrieve transcript with timestamps

**Rate Limits:** TBD (check documentation)

**Cost Estimate:** TBD (check pricing)

**Environment Variable:** `RTZR_API_KEY`

### 7.2 Claude API (Anthropic)

**Purpose:** Content analysis, viral moment detection, suggestions

**Model:** `claude-sonnet-4-20250514`

**Authentication:** API Key

**Usage:**
- Topic segmentation prompts
- Viral moment detection prompts
- Title/thumbnail generation prompts

**Rate Limits:** Tier-dependent

**Cost Estimate:** ~$0.003/1K input tokens, ~$0.015/1K output tokens

**Environment Variable:** `ANTHROPIC_API_KEY`

---

## 8. Configuration

### 8.1 Configuration File (`config/settings.yaml`)

```yaml
# Paths
paths:
  output_dir: "./output"
  temp_dir: "./temp"

# Silence Detection
silence:
  threshold_db: -40          # Silence threshold in dB
  min_duration: 0.5          # Minimum silence to cut (seconds)
  padding: 0.1               # Keep this much audio around speech

# Transcription
transcription:
  provider: "returnzero"     # returnzero | whisper (future)
  language_hints:            # Help with code-switching
    - "ko"
    - "en"

# Analysis
analysis:
  model: "claude-sonnet-4-20250514"

  longform:
    min_chapter_duration: 60  # Minimum chapter length (seconds)
    max_chapters: 20          # Maximum chapters to generate

  shortform:
    min_clip_duration: 15     # Minimum clip length (seconds)
    max_clip_duration: 60     # Maximum clip length (seconds)
    max_clips: 30             # Maximum clips to extract

    # Content signals for viral detection
    viral_signals:
      - "bold market predictions"
      - "contrarian takes"
      - "price calls"
      - "I told you so moments"
      - "surprising insights"
      - "emotional reactions"

# Video Settings
video:
  shortform:
    resolution: "1080x1920"   # 9:16 vertical
    webcam_position: "top"    # top | bottom
    webcam_height_ratio: 0.4  # 40% of frame for webcam

# Premiere Export
premiere:
  fps: 30
  sample_rate: 48000
  timecode_start: "00:00:00:00"

# Caption Style
captions:
  format:
    - "srt"
    - "vtt"
  style:
    font: "Arial Bold"
    size: 48
```

### 8.2 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `RTZR_API_KEY` | Yes | Return Zero API key |
| `ANTHROPIC_API_KEY` | Yes | Anthropic (Claude) API key |
| `STREAM_AUTOMATION_CONFIG` | No | Path to custom config file |

---

## 9. CLI Specification

### 9.1 Commands

#### `process` - Full Pipeline

```bash
stream-automation process \
  --full-stream ~/recordings/full_stream.mp4 \
  --webcam ~/recordings/webcam.mp4 \
  --screen ~/recordings/screen.mp4 \
  --name "January 15 Market Analysis" \
  --output ~/output/
```

**Options:**
| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--full-stream` | Yes | - | Path to full stream recording |
| `--webcam` | Yes | - | Path to webcam recording |
| `--screen` | Yes | - | Path to screen recording |
| `--name` | Yes | - | Stream name (used for output folder) |
| `--output` | No | `./output` | Output directory |
| `--skip-transcription` | No | False | Use existing transcript |
| `--skip-analysis` | No | False | Use existing analysis |
| `--config` | No | `./config/settings.yaml` | Config file path |

#### `transcribe` - Transcription Only

```bash
stream-automation transcribe \
  --input ~/recordings/full_stream.mp4 \
  --output ~/output/transcript.json
```

#### `analyze` - Analysis Only

```bash
stream-automation analyze \
  --transcript ~/output/transcript.json \
  --output ~/output/analysis/
```

#### `export` - Export Only

```bash
stream-automation export \
  --analysis ~/output/analysis/ \
  --full-stream ~/recordings/full_stream.mp4 \
  --webcam ~/recordings/webcam.mp4 \
  --screen ~/recordings/screen.mp4 \
  --output ~/output/premiere/
```

#### `config` - Configuration

```bash
# View current config
stream-automation config show

# Set a value
stream-automation config set silence.threshold_db -35

# Reset to defaults
stream-automation config reset
```

### 9.2 Output During Processing

```
$ stream-automation process --full-stream ... --webcam ... --screen ... --name "Market Analysis"

🎬 Livestream Automation v1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/5] Extracting audio...
      Duration: 1:32:45
      ✓ Audio extracted (2.3s)

[2/5] Detecting silences...
      Found: 234 silence regions
      Total silence: 12:34
      ✓ Silence map generated (5.1s)

[3/5] Transcribing (Return Zero)...
      Uploading audio... ✓
      Processing... ████████████████████ 100%
      ✓ Transcript received (45.2s)
      Words: 12,453
      Languages detected: Korean (72%), English (28%)

[4/5] Analyzing content (Claude)...
      ✓ Long-form analysis complete
        Chapters: 8
        Title ideas: 5
      ✓ Short-form analysis complete
        Viral clips: 14
        Total clip duration: 8:23

[5/5] Generating Premiere XMLs...
      ✓ Long-form timeline generated
      ✓ Short-form timeline generated
      ✓ Captions generated (SRT, VTT)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Complete! Output saved to: ./output/market-analysis/

Long-form:
  • Timeline: ./output/market-analysis/longform/timeline.xml
  • Chapters: 8 topics identified
  • Captions: SRT and VTT formats

Short-form:
  • Timeline: ./output/market-analysis/shortform/timeline.xml
  • Clips: 14 viral moments (8:23 total)
  • Captions: Per-clip SRT files

Next steps:
  1. Open Adobe Premiere Pro
  2. File > Import > ./output/market-analysis/longform/timeline.xml
  3. Review and make final adjustments
```

---

## 10. Error Handling

### 10.1 Error Categories

| Category | Examples | Handling |
|----------|----------|----------|
| Input Errors | Missing files, wrong format | Validate early, clear messages |
| API Errors | Rate limits, auth failures | Retry with backoff, cache results |
| Processing Errors | FFmpeg failures, memory issues | Log details, partial recovery |
| Output Errors | Disk full, permission denied | Check before processing |

### 10.2 Retry Strategy

| Service | Max Retries | Backoff | Notes |
|---------|-------------|---------|-------|
| Return Zero | 3 | Exponential (2s, 4s, 8s) | Cache successful transcripts |
| Claude API | 3 | Exponential (1s, 2s, 4s) | Cache successful analyses |
| FFmpeg | 1 | None | Fail fast, log error |

### 10.3 Recovery

- **Checkpoint system:** Save intermediate results after each stage
- **Resume capability:** `--resume` flag to continue from last checkpoint
- **Partial output:** Generate what's possible even if some stages fail

---

## 11. Testing Strategy

### 11.1 Test Categories

| Type | Coverage | Tools |
|------|----------|-------|
| Unit Tests | Core logic, utilities | pytest |
| Integration Tests | API clients, FFmpeg | pytest + mocks |
| End-to-End Tests | Full pipeline | Sample recordings |

### 11.2 Test Data

- Short sample recordings (1-2 minutes) for fast iteration
- Full-length test stream (30+ minutes) for realistic testing
- Edge cases: pure Korean, pure English, heavy code-switching

---

## 12. Future Enhancements (v2.0+)

| Feature | Priority | Notes |
|---------|----------|-------|
| Windows support | High | Planned for v2.0 |
| GUI application | Medium | Electron or native |
| Real-time processing | Medium | Process during stream |
| Auto-upload to platforms | Low | YouTube, TikTok, Instagram |
| Facial expression analysis | Low | Improve reaction detection |
| A/B title testing | Low | Track performance |
| Multi-language support | Low | Beyond Korean/English |

---

## 13. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Processing time | < 10 min for 1-hour stream | Time from start to output |
| Transcription accuracy | > 95% for Korean, > 98% for English | Manual review sampling |
| Viral clip recall | > 90% of "good" moments captured | Creator feedback |
| Premiere import success | 100% | No import errors |
| User satisfaction | Creator uses it for every stream | Adoption rate |

---

## 14. Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Return Zero API changes | High | Low | Abstract API client, easy to swap |
| Claude API cost overruns | Medium | Medium | Token budgets, caching, model fallback |
| FFmpeg compatibility issues | Medium | Low | Pin version, test on target OS |
| Poor viral detection | High | Medium | Iterate on prompts, user feedback loop |
| Long processing times | Medium | Medium | Async processing, progress indicators |

---

## 15. Timeline

This PRD intentionally does not include time estimates. Implementation will proceed in phases:

**Phase 1: Core Pipeline**
- Audio extraction and silence detection
- Return Zero transcription integration
- Basic Claude analysis
- FCP7 XML generation

**Phase 2: Polish**
- CLI refinement
- Error handling and recovery
- Configuration system
- Caption formatting

**Phase 3: Optimization**
- Prompt tuning for better viral detection
- Performance optimization
- Testing and documentation

---

## Appendix A: FCP7 XML Structure Reference

The Final Cut Pro 7 XML format is well-documented and imports cleanly into Adobe Premiere Pro.

Key elements:
- `<sequence>` - Timeline container
- `<video>` / `<audio>` - Track containers
- `<clipitem>` - Individual clips
- `<marker>` - Chapter/clip markers
- `<file>` - Media file references

Example structure available in `docs/examples/fcp7_xml_example.xml`

---

## Appendix B: Return Zero API Reference

Documentation: https://docs.rtzr.ai (to be confirmed)

Key endpoints:
- `POST /transcribe` - Submit audio for transcription
- `GET /transcribe/{id}` - Check status / retrieve result

Response format includes:
- Word-level timestamps
- Confidence scores
- Language detection per segment

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| FCP7 XML | Final Cut Pro 7 XML interchange format |
| Code-switching | Alternating between languages mid-speech |
| Viral moment | Content segment optimized for short-form engagement |
| Silence region | Audio below threshold for minimum duration |
| Chapter | Topic segment for long-form video navigation |
