# ElevenLabs Narrator

A small command-line tool for testing how well **ElevenLabs Eleven v4** text-to-speech narrates a short story. You give it a text file and a voice, and it saves an MP3 (or WAV) and reports how long the API took to respond.

```text
$ uv run narrate --voice charlie
Narrating stories/the_lighthouse_keeper.txt with model=eleven_v4 voice=charlie (IKne3meq5aSn9XLyUdCD) ...
  1,941 characters
  first audio byte after 23.51s, finished in 23.74s
  saved output/the_lighthouse_keeper_eleven_v4_charlie_20261004-114906.mp3 (1934 KB)
```

## Features

- **Eleven v4 by default.** Any other ElevenLabs model can be chosen with `--model`, so you can compare them on the same text.
- **Voices by name or ID.** `--voice brian` works for the 20 premade voices; custom and cloned voices work by ID.
- **Works with restricted API keys.** If the key isn't allowed to read voices, `--list-voices` falls back to a built-in catalog of premade voices.
- **Streaming writes.** Audio goes to disk chunk by chunk as it arrives instead of being held in memory first.
- **Timing.** Each run reports time to first byte and total time.
- **Voice controls.** Stability, similarity, style, speed and seed can all be set from the command line, and values outside the allowed range are rejected before anything is sent to the API.
- **Checks before calling the API.** Empty stories and stories over the model's character limit are rejected without using any credits.
- **Tested without the API.** The test suite uses a fake client, so it needs no API key, no network and no credits.

## Quick start

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone <this-repo>
cd ElevenLabs
uv sync
cp .env.example .env        # then paste your ElevenLabs API key into .env
uv run narrate --play
```

Get an API key from your [ElevenLabs API key settings](https://elevenlabs.io/app/settings/api-keys). The key needs the **Text to Speech** permission. **Voices: Read** is optional; with it, `--list-voices` shows your own and cloned voices as well as the premade ones.

## Usage

```bash
uv run narrate                                   # sample story, George voice, eleven_v4
uv run narrate path/to/story.txt --voice lily    # your own story, a different voice
uv run narrate --model eleven_multilingual_v2    # compare against an older model
uv run narrate --style 0.6 --stability 0.3       # a more expressive, varied delivery
uv run narrate --format wav_44100 --play         # lossless output, then play it
uv run narrate --list-voices british             # find voices
```

| Option | Default | Description |
| --- | --- | --- |
| `story` | `stories/the_lighthouse_keeper.txt` | UTF-8 text file to narrate |
| `-v, --voice` | `george` | Premade voice name or any voice ID |
| `-m, --model` | `eleven_v4` | ElevenLabs model ID |
| `-f, --format` | `mp3_44100_128` | Output format (`mp3_*`, `wav_*`, `opus_*`, `pcm_*`) |
| `-o, --out-dir` | `output/` | Where audio files are written |
| `--stability` | `0.5` | 0–1; lower gives a more varied, emotional delivery |
| `--similarity` | `0.75` | 0–1; how closely the output sticks to the original voice |
| `--style` | `0.3` | 0–1; how strongly the voice's style is exaggerated |
| `--speed` | `1.0` | Speaking rate |
| `--seed` | none | Makes output (mostly) repeatable between runs |
| `--list-voices [SEARCH]` | | List voices and exit |
| `--play` | | Open the result in the default audio player |

Output files are named `<story>_<model>_<voice>_<timestamp>.<ext>`, so takes made with different models or voices can sit next to each other for comparison.

## How it works

```
src/narrator/
├── cli.py      argument parsing, API key loading, user-facing output and errors
├── tts.py      character-limit check, the API request, streaming to disk, timing
└── voices.py   premade voice catalog, name/ID lookup, account voice listing
```

`tts.narrate()` reads the story, checks it against the model's per-request character limit, and calls `client.text_to_speech.convert()`. The SDK returns a lazy iterator of audio bytes: the HTTP request is only sent when the first chunk is requested. That's why timing starts right before the call and "first byte" covers the full synthesis wait.

## Findings so far

Measured on the sample story (1,941 characters, about 2 minutes of audio) with `eleven_v4`:

| Voice | Time to first byte | Total | Output |
| --- | --- | --- | --- |
| George | 24.5s | 24.8s | 2.0 MB |
| Charlie | 23.5s | 23.7s | 1.9 MB |

Almost all of the time is spent before the first byte arrives. Through this endpoint, v4 generates the whole clip on the server and then sends it all at once, which suits pre-rendered narration. For playback that starts while audio is still being generated, look at `eleven_v4_turbo` or the streaming/WebSocket endpoints.

## Development

```bash
uv run pytest          # tests (no API key needed)
uv run ruff check .    # lint
uv run ruff format .   # format
```

Continuous integration runs lint, format checks and tests on every push (see [.github/workflows/ci.yml](.github/workflows/ci.yml)).

## License

[MIT](LICENSE)
