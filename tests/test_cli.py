import pytest

from narrator.cli import build_parser


def test_defaults():
    args = build_parser().parse_args([])
    assert args.voice == "george"
    assert args.model == "eleven_v4"
    assert args.list_voices is None


def test_list_voices_without_search_term():
    assert build_parser().parse_args(["--list-voices"]).list_voices == ""


@pytest.mark.parametrize("flag", ["--stability", "--similarity", "--style"])
def test_unit_interval_settings_reject_out_of_range(flag, capsys):
    with pytest.raises(SystemExit):
        build_parser().parse_args([flag, "1.5"])
    assert "between 0 and 1" in capsys.readouterr().err
