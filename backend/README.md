# Stream Automation Backend

Automated processing service for livestream content.

## Features

- Google Drive integration for file watching
- Audio processing with FFmpeg (silence detection)
- Transcription via Return Zero API (Korean/English)
- Content analysis via Claude API (chapters, titles, thumbnails)
- FCP7 XML timeline generation for Adobe Premiere
- Telegram notifications
- Background processing with Celery

## Quick Start

### Prerequisites

- Docker and Docker Compose
- API keys (see `.env.example`)

### Setup

1. Copy environment file:
```bash
cp .env.example .env
```

2. Fill in your API keys in `.env`

3. Start services:
```bash
docker-compose up -d
```

4. Access the API at http://localhost:8000

### Development

For local development without Docker:

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Install FFmpeg:
```bash
# macOS
brew install ffmpeg

# Ubuntu
sudo apt-get install ffmpeg
```

3. Start PostgreSQL and Redis (via Docker):
```bash
docker-compose up -d db redis
```

4. Run the API:
```bash
uvicorn app.main:app --reload
```

5. Run Celery worker:
```bash
celery -A app.workers.celery_app worker --loglevel=info
```

## API Endpoints

### Authentication
- `GET /api/auth/google` - Start Google OAuth
- `GET /api/auth/google/callback` - OAuth callback
- `GET /api/auth/me` - Get current user

### Jobs
- `GET /api/jobs` - List all jobs
- `GET /api/jobs/current` - Get current processing job
- `GET /api/jobs/{id}` - Get job details
- `POST /api/jobs/{id}/reprocess` - Re-process a job
- `DELETE /api/jobs/{id}` - Delete a job

### Settings
- `GET /api/settings` - Get user settings
- `PUT /api/settings` - Update settings
- `POST /api/settings/telegram/connect` - Connect Telegram
- `POST /api/settings/telegram/test` - Test Telegram

## Architecture

```
backend/
├── app/
│   ├── api/           # FastAPI routes
│   ├── db/            # Database models
│   ├── models/        # Pydantic models
│   ├── services/      # Business logic
│   │   ├── google_drive.py
│   │   ├── audio.py
│   │   ├── transcription.py
│   │   ├── analysis.py
│   │   ├── xml_generator.py
│   │   └── telegram.py
│   ├── workers/       # Celery tasks
│   │   ├── processor.py
│   │   └── watcher.py
│   ├── config.py
│   └── main.py
├── Dockerfile
└── requirements.txt
```

## Processing Pipeline

1. **DETECT** - Watch Google Drive for new YYYYMMDD folders
2. **DOWNLOAD** - Download stream file to temp storage
3. **AUDIO** - Extract audio, detect silences
4. **TRANSCRIBE** - Send to Return Zero API
5. **ANALYZE** - Send to Claude for chapters/titles
6. **GENERATE** - Create timeline.xml, captions, chapters
7. **UPLOAD** - Upload outputs to Google Drive
8. **NOTIFY** - Send Telegram notification
