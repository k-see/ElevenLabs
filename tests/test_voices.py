from types import SimpleNamespace

import pytest
from elevenlabs.core.api_error import ApiError

from narrator.voices import PREMADE_VOICES, list_voices, premade_voices, resolve_voice


@pytest.mark.parametrize("name", ["george", "George", " GEORGE "])
def test_resolve_voice_by_name_is_case_insensitive(name):
    voice = resolve_voice(name)
    assert voice.voice_id == PREMADE_VOICES["george"][0]
    assert voice.name == "george"


def test_resolve_voice_by_premade_id_recovers_name():
    voice = resolve_voice("IKne3meq5aSn9XLyUdCD")
    assert voice.name == "charlie"


def test_resolve_unknown_id_passes_through():
    voice = resolve_voice("customVoiceId123")
    assert voice.voice_id == "customVoiceId123"
    assert voice.name == "customVoiceId123"


def test_premade_voices_search_matches_description():
    names = {v.name for v in premade_voices("british")}
    assert names == {"george", "daniel", "alice", "lily"}


def test_premade_voice_ids_are_unique():
    ids = [voice_id for voice_id, _ in PREMADE_VOICES.values()]
    assert len(ids) == len(set(ids))


def _client_raising(status_code):
    def search(**_):
        raise ApiError(status_code=status_code, body={"detail": "nope"})

    return SimpleNamespace(voices=SimpleNamespace(search=search))


@pytest.mark.parametrize("status_code", [401, 403])
def test_list_voices_falls_back_when_not_permitted(status_code):
    voices, from_account = list_voices(_client_raising(status_code), "lily")
    assert not from_account
    assert [v.name for v in voices] == ["lily"]


def test_list_voices_reraises_other_errors():
    with pytest.raises(ApiError):
        list_voices(_client_raising(500))


def test_list_voices_from_account():
    account_voice = SimpleNamespace(voice_id="abc", name="My Clone", labels={"accent": "Irish"})
    client = SimpleNamespace(voices=SimpleNamespace(search=lambda **_: SimpleNamespace(voices=[account_voice])))
    voices, from_account = list_voices(client)
    assert from_account
    assert voices[0].name == "My Clone"
    assert voices[0].description == "Irish"
