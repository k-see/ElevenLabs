"""Text-to-speech synthesis: send a story to ElevenLabs and stream audio to disk."""

import re
import time
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

from narrator.voices import Voice

DEFAULT_MODEL = "eleven_v4"
DEFAULT_FORMAT = "mp3_44100_128"

# Per-request character limits from https://elevenlabs.io/docs/models.
# Models not listed here are passed through and left to the API to validate.
MODEL_CHAR_LIMITS: dict[str, int] = {
    "eleven_v4": 10_000,
    "eleven_v3": 5_000,
    "eleven_multilingual_v2": 10_000,
    "eleven_flash_v2_5": 40_000,
    "eleven_flash_v2": 30_000,
}


class NarrationError(Exception):
    """Raised when a story can't be narrated."""


@dataclass(frozen=True)
class NarrationResult:
    path: Path
    characters: int
    first_byte_seconds: float
    total_seconds: float

    @property
    def size_bytes(self) -> int:
        return self.path.stat().st_size


def check_length(text: str, model: str) -> None:
    """Raise NarrationError if text exceeds the model's per-request limit."""
    limit = MODEL_CHAR_LIMITS.get(model)
    if limit is not None and len(text) > limit:
        raise NarrationError(f"Story is {len(text):,} characters; {model} accepts at most {limit:,} per request.")


def output_path(out_dir: Path, story: Path, model: str, voice: Voice, output_format: str) -> Path:
    """Build a unique, descriptive filename like story_eleven_v4_george_20261004-114906.mp3."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    ext = output_format.split("_")[0]
    voice_slug = re.sub(r"[^a-z0-9]+", "-", voice.name.lower()).strip("-") or "voice"
    return out_dir / f"{story.stem}_{model}_{voice_slug}_{stamp}.{ext}"


def write_stream(chunks: Iterator[bytes], path: Path, start: float) -> tuple[float, float]:
    """Write streamed audio chunks to path.

    Returns (seconds to first chunk, total seconds), both measured from start.
    The ElevenLabs SDK sends the HTTP request lazily on first iteration, so the
    first-chunk time includes the full server-side synthesis latency.
    """
    first_chunk_at: float | None = None
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        for chunk in chunks:
            if first_chunk_at is None:
                first_chunk_at = time.perf_counter() - start
            f.write(chunk)
    if first_chunk_at is None:
        path.unlink(missing_ok=True)
        raise NarrationError("The API returned no audio.")
    return first_chunk_at, time.perf_counter() - start


def narrate(
    client: ElevenLabs,
    story: Path,
    voice: Voice,
    *,
    model: str = DEFAULT_MODEL,
    output_format: str = DEFAULT_FORMAT,
    settings: VoiceSettings | None = None,
    seed: int | None = None,
    out_dir: Path = Path("output"),
) -> NarrationResult:
    """Narrate the story file and save the audio under out_dir."""
    text = story.read_text(encoding="utf-8").strip()
    if not text:
        raise NarrationError(f"{story} is empty.")
    check_length(text, model)

    start = time.perf_counter()
    audio = client.text_to_speech.convert(
        voice_id=voice.voice_id,
        text=text,
        model_id=model,
        output_format=output_format,
        voice_settings=settings,
        seed=seed,
    )
    path = output_path(out_dir, story, model, voice, output_format)
    first_byte, total = write_stream(audio, path, start)
    return NarrationResult(path, len(text), first_byte, total)
