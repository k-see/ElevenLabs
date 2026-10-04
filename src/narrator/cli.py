"""Command-line interface for the narrator."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from elevenlabs.core.api_error import ApiError

from narrator.tts import DEFAULT_FORMAT, DEFAULT_MODEL, NarrationError, narrate
from narrator.voices import list_voices, resolve_voice

DEFAULT_STORY = Path("stories/the_lighthouse_keeper.txt")


def unit_interval(value: str) -> float:
    """argparse type for settings that must fall in [0, 1]."""
    x = float(value)
    if not 0.0 <= x <= 1.0:
        raise argparse.ArgumentTypeError(f"must be between 0 and 1, got {x}")
    return x


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="narrate",
        description="Narrate a short story with ElevenLabs text-to-speech.",
    )
    p.add_argument("story", nargs="?", type=Path, default=DEFAULT_STORY, help="UTF-8 text file to narrate")
    p.add_argument("-v", "--voice", default="george", help="premade voice name (e.g. brian, lily) or voice ID")
    p.add_argument(
        "-m",
        "--model",
        default=DEFAULT_MODEL,
        help="e.g. eleven_v4, eleven_v4_turbo, eleven_v3, eleven_multilingual_v2",
    )
    p.add_argument("-f", "--format", default=DEFAULT_FORMAT, help="output format, e.g. mp3_44100_128, wav_44100")
    p.add_argument("-o", "--out-dir", type=Path, default=Path("output"), help="where audio files are written")

    tuning = p.add_argument_group("voice settings")
    tuning.add_argument("--stability", type=unit_interval, default=0.5, help="lower = more varied delivery")
    tuning.add_argument("--similarity", type=unit_interval, default=0.75, help="adherence to the original voice")
    tuning.add_argument("--style", type=unit_interval, default=0.3, help="style exaggeration")
    tuning.add_argument("--speed", type=float, default=1.0, help="speaking rate (about 0.7 to 1.2)")
    tuning.add_argument("--seed", type=int, help="seed for (mostly) reproducible output")

    p.add_argument(
        "--list-voices", nargs="?", const="", metavar="SEARCH", help="list voices (optionally filtered) and exit"
    )
    p.add_argument("--play", action="store_true", help="open the result in the default audio player")
    return p


def open_file(path: Path) -> None:
    if sys.platform == "win32":
        os.startfile(path)  # type: ignore[attr-defined]
    else:
        subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", str(path)], check=False)


def make_client() -> ElevenLabs:
    load_dotenv()
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("ELEVENLABS_API_KEY is not set. Add it to your environment or a .env file (see .env.example).")
    return ElevenLabs(api_key=api_key)


def cmd_list_voices(client: ElevenLabs, search: str) -> None:
    voices, from_account = list_voices(client, search or None)
    if not from_account:
        print("API key can't read account voices (needs voices_read); showing premade voices.\n")
    for v in voices:
        print(f"{v.voice_id}  {v.name:<24} {v.description}")


def cmd_narrate(client: ElevenLabs, args: argparse.Namespace) -> None:
    voice = resolve_voice(args.voice)
    settings = VoiceSettings(
        stability=args.stability,
        similarity_boost=args.similarity,
        style=args.style,
        use_speaker_boost=True,
        speed=args.speed,
    )
    print(f"Narrating {args.story} with model={args.model} voice={voice.name} ({voice.voice_id}) ...")
    result = narrate(
        client,
        args.story,
        voice,
        model=args.model,
        output_format=args.format,
        settings=settings,
        seed=args.seed,
        out_dir=args.out_dir,
    )
    print(f"  {result.characters:,} characters")
    print(f"  first audio byte after {result.first_byte_seconds:.2f}s, finished in {result.total_seconds:.2f}s")
    print(f"  saved {result.path} ({result.size_bytes / 1024:.0f} KB)")
    if args.play:
        open_file(result.path)


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    client = make_client()
    try:
        if args.list_voices is not None:
            cmd_list_voices(client, args.list_voices)
        else:
            cmd_narrate(client, args)
    except (NarrationError, FileNotFoundError) as e:
        sys.exit(f"error: {e}")
    except ApiError as e:
        detail = e.body.get("detail", e.body) if isinstance(e.body, dict) else e.body
        message = detail.get("message", detail) if isinstance(detail, dict) else detail
        sys.exit(f"ElevenLabs API error ({e.status_code}): {message}")


if __name__ == "__main__":
    main()
