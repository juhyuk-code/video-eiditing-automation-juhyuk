# Stream Automation

Automated livestream content processing for long-form and short-form video creation.

## Overview

Stream Automation processes OBS recordings and generates:

- **Long-form content** (16:9): Silences removed, chapter markers, captions
- **Short-form clips** (9:16): Viral moments identified, webcam+screen layout

## Features

- **Silence Detection**: Automatically removes silent portions using FFmpeg
- **Korean/English Transcription**: Return Zero API for accurate Korean STT
- **AI Content Analysis**: Claude identifies chapters and viral-worthy moments
- **Adobe Premiere Export**: FCP7 XML format imports directly into Premiere

## Prerequisites

- **Python 3.11+**
- **FFmpeg 6.0+** (install via `brew install ffmpeg` on macOS)
- **Return Zero API account** ([rtzr.ai](https://rtzr.ai))
- **Anthropic API key** ([console.anthropic.com](https://console.anthropic.com))

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/stream-automation.git
cd stream-automation

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Configuration

### Environment Variables

Set your API keys:

```bash
export RTZR_CLIENT_ID="your_client_id"
export RTZR_CLIENT_SECRET="your_client_secret"
export ANTHROPIC_API_KEY="your_anthropic_api_key"
```

### Config File (Optional)

Create `config/settings.yaml` to customize settings:

```yaml
silence:
  threshold_db: -40
  min_duration: 0.5
  padding: 0.1

analysis:
  shortform:
    min_clips: 10
    max_clip_duration: 180
```

## Usage

### Full Pipeline

Process a livestream with all 3 source recordings:

```bash
stream-automation process \
  --full-stream ~/recordings/full_stream.mp4 \
  --webcam ~/recordings/webcam.mp4 \
  --screen ~/recordings/screen.mp4 \
  --name "January 15 Market Analysis"
```

### Output Structure

```
output/january-15-market-analysis/
├── longform/
│   ├── timeline.xml      # Import into Premiere
│   ├── captions.srt      # Subtitles
│   ├── captions.vtt      # WebVTT format
│   ├── chapters.txt      # YouTube chapters
│   └── suggestions.md    # Title/thumbnail ideas
├── shortform/
│   ├── timeline.xml      # All clips in sequence
│   ├── captions/         # Per-clip SRT files
│   ├── clips_metadata.json
│   └── suggestions.md    # Title ideas per clip
└── transcript/
    ├── full_transcript.json
    └── full_transcript.txt
```

### Other Commands

```bash
# View current configuration
stream-automation config

# Transcribe only
stream-automation transcribe --input video.mp4 --output transcript.json
```

## Importing into Premiere

1. Open Adobe Premiere Pro
2. **File > Import**
3. Select `timeline.xml` from the output folder
4. Review the imported sequence with silences already removed
5. Make final adjustments and export

## OBS Setup

For optimal results, configure OBS with the **Source Record** plugin:

1. **Full Stream**: Main output with all overlays
2. **Webcam**: Isolated face camera recording
3. **Screen**: Isolated screen capture

All 3 recordings must start simultaneously (Source Record handles this).

## Supported Formats

- **Input**: MP4, MOV (H.264, H.265, ProRes)
- **Output**: FCP7 XML, SRT, VTT, JSON, Markdown

## API References

- [Return Zero API Docs](https://developers.rtzr.ai/docs/en/)
- [Anthropic Claude API](https://docs.anthropic.com)

## License

MIT
