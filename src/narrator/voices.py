"""Voice lookup: premade voice names, IDs, and account voice listing."""

from dataclasses import dataclass

from elevenlabs.client import ElevenLabs
from elevenlabs.core.api_error import ApiError

# ElevenLabs premade voices, available on every account. Lets --voice take a
# friendly name and lets voice listing work even when the API key lacks the
# voices_read permission.
PREMADE_VOICES: dict[str, tuple[str, str]] = {
    "george": ("JBFqnCBsd6RMkjVDRZzb", "male, British, warm storyteller"),
    "brian": ("nPczCjzI2devNBz1zQrb", "male, American, deep narrator"),
    "daniel": ("onwK4e9ZLuTAKqWW03F9", "male, British, authoritative"),
    "bill": ("pqHfZKP75CvOlQylNhV4", "male, American, older, trustworthy"),
    "callum": ("N2lVS1w4EtoT3dr4eOWO", "male, gravelly, intense"),
    "charlie": ("IKne3meq5aSn9XLyUdCD", "male, Australian, casual"),
    "chris": ("iP95p4xoKVk53GoZ742B", "male, American, casual"),
    "eric": ("cjVigY5qzO86Huf0OWal", "male, American, smooth"),
    "liam": ("TX3LPaxmHKxFdv7VOQHJ", "male, American, young"),
    "will": ("bIHbv24MWmeRgasZH58o", "male, American, friendly"),
    "river": ("SAz9YHcvj6GT2YYXdXww", "neutral, American, calm"),
    "rachel": ("21m00Tcm4TlvDq8ikWAM", "female, American, calm"),
    "alice": ("Xb7hH8MSUJpSbSDYk0k2", "female, British, confident"),
    "aria": ("9BWtsMINqrJLrRacOk9x", "female, American, expressive"),
    "charlotte": ("XB0fDUnXU5powFXDhCwa", "female, Swedish, seductive"),
    "jessica": ("cgSgspJ2msm6clMCkdW9", "female, American, expressive"),
    "laura": ("FGY2WhTYpPnrIDTdsKH5", "female, American, upbeat"),
    "lily": ("pFZP5JQG7iQjIQuC4Bku", "female, British, warm"),
    "matilda": ("XrExE9yKIg1WjnnlVkGX", "female, American, friendly"),
    "sarah": ("EXAVITQu4vr4xnSDxMaL", "female, American, soft"),
}

_NAME_BY_ID = {voice_id: name for name, (voice_id, _) in PREMADE_VOICES.items()}


@dataclass(frozen=True)
class Voice:
    voice_id: str
    name: str
    description: str = ""


def resolve_voice(voice: str) -> Voice:
    """Turn a premade voice name (case-insensitive) or a raw voice ID into a Voice."""
    key = voice.strip().lower()
    if key in PREMADE_VOICES:
        voice_id, desc = PREMADE_VOICES[key]
        return Voice(voice_id, key, desc)
    if voice in _NAME_BY_ID:
        name = _NAME_BY_ID[voice]
        return Voice(voice, name, PREMADE_VOICES[name][1])
    return Voice(voice, voice)


def premade_voices(search: str | None = None) -> list[Voice]:
    """Premade voices, optionally filtered by a case-insensitive search term."""
    term = (search or "").lower()
    return [
        Voice(voice_id, name, desc)
        for name, (voice_id, desc) in PREMADE_VOICES.items()
        if term in f"{name} {desc}".lower()
    ]


def list_voices(client: ElevenLabs, search: str | None = None) -> tuple[list[Voice], bool]:
    """List voices on the account, falling back to premade voices.

    Returns (voices, from_account). from_account is False when the API key
    is not permitted to read voices and the built-in premade list was used.
    """
    try:
        resp = client.voices.search(search=search, page_size=100)
    except ApiError as e:
        if e.status_code not in (401, 403):
            raise
        return premade_voices(search), False

    voices = [
        Voice(v.voice_id, v.name or "", ", ".join(f"{val}" for val in (v.labels or {}).values())) for v in resp.voices
    ]
    return voices, True
