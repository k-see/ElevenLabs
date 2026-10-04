# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

A Python command-line tool (`narrate`) that narrates text files with ElevenLabs text-to-speech, defaulting to the `eleven_v4` model. It uses the official `elevenlabs` SDK (2.x) and is managed with uv.

## Commands

```bash
uv sync                    # install, including dev dependencies
uv run narrate --help      # run the CLI
uv run pytest              # tests; never call the real API
uv run ruff check .        # lint
uv run ruff format .       # format
```

## Layout

- `src/narrator/cli.py`: argparse CLI, `.env` loading, turning API errors into readable messages. Keep printing and `sys.exit` here.
- `src/narrator/tts.py`: synthesis and streaming to disk. Raises `NarrationError`; it never prints or exits.
- `src/narrator/voices.py`: the `PREMADE_VOICES` catalog, `resolve_voice`, and `list_voices` with a fallback for keys missing `voices_read`.
- `stories/`: sample input text.
- `output/`: generated audio. Ignored by git.

## Conventions

- Library modules (`tts`, `voices`) take an `ElevenLabs` client as a parameter. Tests pass a `SimpleNamespace` fake, so the suite needs no key or network. Keep it that way; don't add tests that spend API credits.
- `client.text_to_speech.convert()` returns a lazy iterator, and the request is sent on first iteration. Don't wrap it in `list()` or `b"".join()` before writing; stream it.
- `MODEL_CHAR_LIMITS` in `tts.py` comes from https://elevenlabs.io/docs/models. Unknown models are passed through for the API to validate.
- Ruff config is in `pyproject.toml` (line length 120).

## Secrets

- The API key comes from `ELEVENLABS_API_KEY` in the environment or in `.env`. `.env` is ignored by git; `.env.example` is the template.
- Never print, log, commit or hard-code the key.
