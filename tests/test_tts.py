from types import SimpleNamespace

import pytest

from narrator.tts import NarrationError, check_length, narrate, output_path
from narrator.voices import Voice, resolve_voice


class FakeTTS:
    """Stands in for client.text_to_speech, recording the request it receives."""

    def __init__(self, chunks):
        self.chunks = chunks
        self.request = None

    def convert(self, **kwargs):
        self.request = kwargs
        yield from self.chunks


def fake_client(chunks):
    return SimpleNamespace(text_to_speech=FakeTTS(chunks))


@pytest.fixture
def story(tmp_path):
    path = tmp_path / "tiny_tale.txt"
    path.write_text("  Once upon a time.\n", encoding="utf-8")
    return path


def test_narrate_writes_streamed_audio(story, tmp_path):
    client = fake_client([b"ID3", b"abc", b"def"])
    result = narrate(client, story, resolve_voice("lily"), out_dir=tmp_path / "out")

    assert result.path.read_bytes() == b"ID3abcdef"
    assert result.characters == len("Once upon a time.")
    assert 0 <= result.first_byte_seconds <= result.total_seconds


def test_narrate_sends_stripped_text_and_options(story, tmp_path):
    client = fake_client([b"x"])
    narrate(client, story, resolve_voice("brian"), model="eleven_v3", seed=7, out_dir=tmp_path)

    request = client.text_to_speech.request
    assert request["text"] == "Once upon a time."
    assert request["voice_id"] == resolve_voice("brian").voice_id
    assert request["model_id"] == "eleven_v3"
    assert request["seed"] == 7


def test_narrate_empty_response_raises_and_cleans_up(story, tmp_path):
    out_dir = tmp_path / "out"
    with pytest.raises(NarrationError, match="no audio"):
        narrate(fake_client([]), story, resolve_voice("george"), out_dir=out_dir)
    assert list(out_dir.iterdir()) == []


def test_narrate_rejects_empty_story(tmp_path):
    empty = tmp_path / "empty.txt"
    empty.write_text("   \n", encoding="utf-8")
    with pytest.raises(NarrationError, match="empty"):
        narrate(fake_client([b"x"]), empty, resolve_voice("george"), out_dir=tmp_path)


def test_check_length_enforces_known_model_limits():
    check_length("a" * 10_000, "eleven_v4")
    with pytest.raises(NarrationError, match="at most 10,000"):
        check_length("a" * 10_001, "eleven_v4")
    with pytest.raises(NarrationError):
        check_length("a" * 5_001, "eleven_v3")


def test_check_length_ignores_unknown_models():
    check_length("a" * 100_000, "some_future_model")


def test_output_path_includes_story_model_voice_and_extension(tmp_path):
    path = output_path(tmp_path, tmp_path / "my_story.txt", "eleven_v4", Voice("id", "My Clone!"), "wav_44100")
    assert path.parent == tmp_path
    assert path.name.startswith("my_story_eleven_v4_my-clone_")
    assert path.suffix == ".wav"
