"""CLI interface for stream automation."""

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from src.analysis import analyze_longform, analyze_shortform
from src.audio import detect_silences, extract_audio, generate_edit_regions, get_video_info
from src.models import Settings
from src.premiere import generate_longform_xml, generate_shortform_xml
from src.transcription import RTZRClient
from src.transcription.formatter import (
    extract_transcript_for_clip,
    format_transcript_to_srt,
    format_transcript_to_vtt,
)

console = Console()


def load_settings(config_path: Path | None = None) -> Settings:
    """Load settings from config file and environment."""
    if config_path and config_path.exists():
        return Settings.load_from_yaml(config_path)

    # Try default config location
    default_config = Path("config/settings.yaml")
    if default_config.exists():
        return Settings.load_from_yaml(default_config)

    return Settings()


@click.group()
@click.version_option(version="1.0.0")
def main():
    """Stream Automation - Automated livestream content processing."""
    pass


@main.command()
@click.option(
    "--full-stream",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to full stream recording (composited video)",
)
@click.option(
    "--webcam",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to webcam recording (face only)",
)
@click.option(
    "--screen",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to screen recording",
)
@click.option(
    "--name",
    required=True,
    help="Name for this stream (used for output folder)",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=Path("./output"),
    help="Output directory (default: ./output)",
)
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to config file",
)
@click.option(
    "--skip-transcription",
    is_flag=True,
    help="Skip transcription (use existing transcript)",
)
@click.option(
    "--skip-analysis",
    is_flag=True,
    help="Skip analysis (use existing analysis)",
)
def process(
    full_stream: Path,
    webcam: Path,
    screen: Path,
    name: str,
    output: Path,
    config: Path | None,
    skip_transcription: bool,
    skip_analysis: bool,
):
    """Process a livestream recording."""
    console.print(Panel.fit(
        "[bold blue]Stream Automation v1.0[/bold blue]\n"
        "Automated livestream content processing",
        border_style="blue",
    ))

    # Load settings
    settings = load_settings(config)

    # Create output directory
    slug = name.lower().replace(" ", "-")
    output_dir = output / slug
    output_dir.mkdir(parents=True, exist_ok=True)

    longform_dir = output_dir / "longform"
    shortform_dir = output_dir / "shortform"
    transcript_dir = output_dir / "transcript"

    longform_dir.mkdir(exist_ok=True)
    shortform_dir.mkdir(exist_ok=True)
    transcript_dir.mkdir(exist_ok=True)

    # Temp directory
    temp_dir = settings.paths.temp_dir
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Get video info
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Getting video info...", total=None)

            full_stream_info = get_video_info(full_stream)
            webcam_info = get_video_info(webcam)
            screen_info = get_video_info(screen)

            progress.update(task, completed=True)

        console.print(f"  Duration: [green]{_format_duration(full_stream_info.duration)}[/green]")
        console.print(f"  Resolution: [green]{full_stream_info.width}x{full_stream_info.height}[/green]")
        console.print()

        # Step 2: Extract audio
        console.print("[bold]Step 1/5:[/bold] Extracting audio...")
        audio_path = temp_dir / f"{slug}_audio.wav"

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Extracting audio...", total=None)
            extract_audio(full_stream, audio_path)
            progress.update(task, completed=True)

        console.print("  [green]Audio extracted[/green]")
        console.print()

        # Step 3: Detect silences
        console.print("[bold]Step 2/5:[/bold] Detecting silences...")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Analyzing audio...", total=None)

            silences = detect_silences(
                audio_path,
                threshold_db=settings.silence.threshold_db,
                min_duration=settings.silence.min_duration,
            )

            edit_regions = generate_edit_regions(
                silences,
                full_stream_info.duration,
                padding=settings.silence.padding,
            )

            progress.update(task, completed=True)

        total_silence = sum(s.duration for s in silences)
        console.print(f"  Found: [yellow]{len(silences)}[/yellow] silence regions")
        console.print(f"  Total silence: [yellow]{_format_duration(total_silence)}[/yellow]")
        console.print()

        # Step 4: Transcription
        transcript_path = transcript_dir / "full_transcript.json"

        if skip_transcription and transcript_path.exists():
            console.print("[bold]Step 3/5:[/bold] Loading existing transcript...")
            with open(transcript_path) as f:
                from src.models.transcript import Transcript
                transcript_data = json.load(f)
                transcript = Transcript(**transcript_data)
            console.print("  [green]Transcript loaded[/green]")
        else:
            console.print("[bold]Step 3/5:[/bold] Transcribing (Return Zero)...")

            def transcription_progress(msg):
                console.print(f"  [dim]{msg}[/dim]")

            try:
                client = RTZRClient()
                import asyncio
                transcript = asyncio.run(
                    client.transcribe(audio_path, progress_callback=transcription_progress)
                )

                # Save transcript
                with open(transcript_path, "w", encoding="utf-8") as f:
                    json.dump(transcript.model_dump(), f, ensure_ascii=False, indent=2)

                # Save plain text
                with open(transcript_dir / "full_transcript.txt", "w", encoding="utf-8") as f:
                    f.write(transcript.full_text)

                console.print(f"  Words: [green]{transcript.word_count}[/green]")
                if transcript.language_breakdown:
                    lang_str = ", ".join(
                        f"{lang}: {pct}%" for lang, pct in transcript.language_breakdown.items()
                    )
                    console.print(f"  Languages: [green]{lang_str}[/green]")
            except ValueError as e:
                console.print(f"  [red]Transcription skipped: {e}[/red]")
                console.print("  [yellow]Set RTZR_CLIENT_ID and RTZR_CLIENT_SECRET environment variables[/yellow]")
                # Create empty transcript for testing
                from src.models.transcript import Transcript
                transcript = Transcript(segments=[], duration=full_stream_info.duration)

        console.print()

        # Step 5: Analysis
        longform_analysis_path = longform_dir / "analysis.json"
        shortform_analysis_path = shortform_dir / "analysis.json"

        if skip_analysis and longform_analysis_path.exists() and shortform_analysis_path.exists():
            console.print("[bold]Step 4/5:[/bold] Loading existing analysis...")
            with open(longform_analysis_path) as f:
                from src.models.analysis import LongformAnalysis
                longform_analysis = LongformAnalysis(**json.load(f))
            with open(shortform_analysis_path) as f:
                from src.models.analysis import ShortformAnalysis
                shortform_analysis = ShortformAnalysis(**json.load(f))
            console.print("  [green]Analysis loaded[/green]")
        else:
            console.print("[bold]Step 4/5:[/bold] Analyzing content (Claude)...")

            try:
                def analysis_progress(msg):
                    console.print(f"  [dim]{msg}[/dim]")

                # Long-form analysis
                longform_analysis = analyze_longform(
                    transcript, settings, progress_callback=analysis_progress
                )

                # Save long-form analysis
                with open(longform_analysis_path, "w", encoding="utf-8") as f:
                    json.dump(longform_analysis.model_dump(), f, ensure_ascii=False, indent=2)

                console.print(f"  Long-form: [green]{len(longform_analysis.chapters)} chapters[/green]")

                # Short-form analysis
                shortform_analysis = analyze_shortform(
                    transcript, settings, progress_callback=analysis_progress
                )

                # Save short-form analysis
                with open(shortform_analysis_path, "w", encoding="utf-8") as f:
                    json.dump(shortform_analysis.model_dump(), f, ensure_ascii=False, indent=2)

                console.print(
                    f"  Short-form: [green]{shortform_analysis.total_clips} clips "
                    f"({_format_duration(shortform_analysis.total_duration)} total)[/green]"
                )
            except ValueError as e:
                console.print(f"  [red]Analysis skipped: {e}[/red]")
                console.print("  [yellow]Set ANTHROPIC_API_KEY environment variable[/yellow]")
                # Create empty analysis for testing
                from src.models.analysis import (
                    ContentSuggestions,
                    LongformAnalysis,
                    ShortformAnalysis,
                )
                longform_analysis = LongformAnalysis(chapters=[], suggestions=ContentSuggestions())
                shortform_analysis = ShortformAnalysis(clips=[], suggestions=ContentSuggestions())

        console.print()

        # Step 6: Generate outputs
        console.print("[bold]Step 5/5:[/bold] Generating outputs...")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Long-form timeline
            task = progress.add_task("[cyan]Generating long-form timeline...", total=None)

            generate_longform_xml(
                full_stream=full_stream_info,
                edit_regions=edit_regions,
                analysis=longform_analysis,
                settings=settings,
                output_path=longform_dir / "timeline.xml",
            )

            progress.update(task, completed=True)

            # Long-form captions
            task = progress.add_task("[cyan]Generating captions...", total=None)

            format_transcript_to_srt(transcript, longform_dir / "captions.srt")
            format_transcript_to_vtt(transcript, longform_dir / "captions.vtt")

            progress.update(task, completed=True)

            # Long-form chapters
            task = progress.add_task("[cyan]Generating chapters...", total=None)

            with open(longform_dir / "chapters.txt", "w", encoding="utf-8") as f:
                f.write(longform_analysis.to_chapters_txt())

            progress.update(task, completed=True)

            # Long-form suggestions
            task = progress.add_task("[cyan]Generating suggestions...", total=None)

            _write_suggestions(longform_dir / "suggestions.md", longform_analysis.suggestions, "Long-Form")

            progress.update(task, completed=True)

            # Short-form timeline
            task = progress.add_task("[cyan]Generating short-form timeline...", total=None)

            generate_shortform_xml(
                webcam=webcam_info,
                screen=screen_info,
                full_stream=full_stream_info,
                analysis=shortform_analysis,
                edit_regions=edit_regions,
                settings=settings,
                output_path=shortform_dir / "timeline.xml",
            )

            progress.update(task, completed=True)

            # Short-form clip captions
            task = progress.add_task("[cyan]Generating clip captions...", total=None)

            captions_dir = shortform_dir / "captions"
            captions_dir.mkdir(exist_ok=True)

            for clip in shortform_analysis.clips:
                clip_transcript = extract_transcript_for_clip(transcript, clip.start, clip.end)
                format_transcript_to_srt(
                    clip_transcript,
                    captions_dir / f"{clip.id}.srt",
                )

            progress.update(task, completed=True)

            # Short-form metadata
            task = progress.add_task("[cyan]Generating clip metadata...", total=None)

            clips_data = {
                "clips": [c.model_dump() for c in shortform_analysis.clips],
                "total_clips": shortform_analysis.total_clips,
                "total_duration": shortform_analysis.total_duration,
            }
            with open(shortform_dir / "clips_metadata.json", "w", encoding="utf-8") as f:
                json.dump(clips_data, f, ensure_ascii=False, indent=2)

            progress.update(task, completed=True)

            # Short-form suggestions
            task = progress.add_task("[cyan]Generating clip suggestions...", total=None)

            _write_clip_suggestions(shortform_dir / "suggestions.md", shortform_analysis)

            progress.update(task, completed=True)

        console.print()

        # Summary
        console.print(Panel.fit(
            f"[bold green]Complete![/bold green] Output saved to: [cyan]{output_dir}[/cyan]",
            border_style="green",
        ))

        # Output summary table
        table = Table(title="Output Summary")
        table.add_column("Type", style="cyan")
        table.add_column("Files", style="green")

        table.add_row(
            "Long-form",
            f"timeline.xml, captions.srt/.vtt, chapters.txt, suggestions.md"
        )
        table.add_row(
            "Short-form",
            f"timeline.xml, {shortform_analysis.total_clips} clip captions, clips_metadata.json"
        )

        console.print(table)

        # Next steps
        console.print()
        console.print("[bold]Next steps:[/bold]")
        console.print("  1. Open Adobe Premiere Pro")
        console.print(f"  2. File > Import > [cyan]{longform_dir / 'timeline.xml'}[/cyan]")
        console.print("  3. Review and make final adjustments")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@main.command()
@click.option(
    "--input",
    "input_path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to video file",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    required=True,
    help="Output path for transcript JSON",
)
def transcribe(input_path: Path, output: Path):
    """Transcribe a video file."""
    console.print("[bold]Transcribing...[/bold]")

    # Extract audio
    temp_audio = Path("/tmp/stream_automation_audio.wav")
    extract_audio(input_path, temp_audio)

    # Transcribe
    client = RTZRClient()
    import asyncio
    transcript = asyncio.run(client.transcribe(temp_audio))

    # Save
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(transcript.model_dump(), f, ensure_ascii=False, indent=2)

    console.print(f"[green]Transcript saved to {output}[/green]")


@main.command()
def config():
    """Show current configuration."""
    settings = load_settings()

    console.print("[bold]Current Configuration:[/bold]")
    console.print()

    table = Table()
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Output directory", str(settings.paths.output_dir))
    table.add_row("Silence threshold", f"{settings.silence.threshold_db} dB")
    table.add_row("Min silence duration", f"{settings.silence.min_duration}s")
    table.add_row("Transcription provider", settings.transcription.provider)
    table.add_row("Analysis model", settings.analysis.model)
    table.add_row("Min clips", str(settings.analysis.shortform.min_clips))
    table.add_row("Max clip duration", f"{settings.analysis.shortform.max_clip_duration}s")
    table.add_row("Short-form resolution", settings.video.shortform.resolution)
    table.add_row("FPS", str(settings.premiere.fps))

    console.print(table)


def _format_duration(seconds: float) -> str:
    """Format seconds as human-readable duration."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _write_suggestions(path: Path, suggestions, title: str) -> None:
    """Write suggestions to markdown file."""
    lines = [f"# {title} Content Suggestions", ""]

    if suggestions.title_ideas:
        lines.append("## Title Ideas")
        for i, title in enumerate(suggestions.title_ideas, 1):
            lines.append(f"{i}. {title}")
        lines.append("")

    if suggestions.thumbnail_concepts:
        lines.append("## Thumbnail Concepts")
        for i, concept in enumerate(suggestions.thumbnail_concepts, 1):
            lines.append(f"{i}. {concept}")
        lines.append("")

    if suggestions.tags:
        lines.append("## Tags")
        lines.append(", ".join(suggestions.tags))
        lines.append("")

    if suggestions.description_template:
        lines.append("## Description Template")
        lines.append(suggestions.description_template)
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _write_clip_suggestions(path: Path, analysis) -> None:
    """Write short-form clip suggestions to markdown file."""
    lines = ["# Short-Form Content Suggestions", ""]

    for clip in analysis.clips:
        lines.append(f"## {clip.id.upper()}")
        lines.append(f"**Category:** {clip.category}")
        lines.append(f"**Duration:** {_format_duration(clip.duration)}")
        lines.append(f"**Viral Score:** {clip.viral_score:.2f}")
        lines.append("")

        if clip.hook:
            lines.append(f"**Hook:** {clip.hook}")
            lines.append("")

        if clip.context:
            lines.append(f"**Why it's clip-worthy:** {clip.context}")
            lines.append("")

        if clip.title_suggestions:
            lines.append("**Title Ideas:**")
            for title in clip.title_suggestions:
                lines.append(f"- {title}")
            lines.append("")

        lines.append("---")
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
