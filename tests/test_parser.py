"""Tests for displayplacer `list` output parsing."""

from conftest import (
    DISPLAYPLACER_LIST_OUTPUT,
    MACBOOK_ID,
    EXTERNAL_27_ID,
    EXTERNAL_32_ID,
)
from core.advanced_display_manager import AdvancedDisplayManager


def make_manager(tmp_path):
    return AdvancedDisplayManager(layouts_file=str(tmp_path / "layouts.json"))


def parse(tmp_path, output=DISPLAYPLACER_LIST_OUTPUT):
    return make_manager(tmp_path)._parse_display_output(output)


class TestParsing:
    def test_display_count(self, tmp_path):
        displays = parse(tmp_path)
        assert len(displays) == 3

    def test_display_ids(self, tmp_path):
        displays = parse(tmp_path)
        assert set(displays.keys()) == {MACBOOK_ID, EXTERNAL_27_ID, EXTERNAL_32_ID}

    def test_display_names(self, tmp_path):
        displays = parse(tmp_path)
        assert displays[MACBOOK_ID].name == "MacBook Display"
        assert displays[EXTERNAL_27_ID].name == "External Display (27 inch)"
        assert displays[EXTERNAL_32_ID].name == "External Display (32 inch)"

    def test_display_types(self, tmp_path):
        displays = parse(tmp_path)
        assert displays[MACBOOK_ID].type == "macbook"
        assert displays[EXTERNAL_27_ID].type == "external"
        assert displays[EXTERNAL_32_ID].type == "external"

    def test_resolutions(self, tmp_path):
        displays = parse(tmp_path)
        assert displays[MACBOOK_ID].resolution == (1728, 1117)
        assert displays[EXTERNAL_27_ID].resolution == (1920, 1080)
        assert displays[EXTERNAL_32_ID].resolution == (1920, 1080)

    def test_positions_including_negative(self, tmp_path):
        displays = parse(tmp_path)
        assert displays[MACBOOK_ID].current_position == (0, 0)
        assert displays[EXTERNAL_27_ID].current_position == (1728, -996)
        # Display above/left of main has a negative CoreGraphics origin
        assert displays[EXTERNAL_32_ID].current_position == (-192, -1080)

    def test_hertz(self, tmp_path):
        displays = parse(tmp_path)
        assert displays[MACBOOK_ID].hz == 120
        assert displays[EXTERNAL_27_ID].hz == 60
        # "Hertz: N/A" falls back to the default of 60 rather than crashing
        assert displays[EXTERNAL_32_ID].hz == 60

    def test_scaling_flags(self, tmp_path):
        displays = parse(tmp_path)
        assert displays[MACBOOK_ID].scaling is True
        assert displays[EXTERNAL_27_ID].scaling is False
        assert displays[EXTERNAL_32_ID].scaling is True

    def test_exactly_one_main_display(self, tmp_path):
        displays = parse(tmp_path)
        mains = [d for d in displays.values() if d.is_main]
        assert len(mains) == 1
        assert mains[0].id == MACBOOK_ID

    def test_available_resolutions_deduped(self, tmp_path):
        displays = parse(tmp_path)
        macbook_res = displays[MACBOOK_ID].available_resolutions
        # Fixture lists each resolution at two refresh rates; dedup keeps one each
        assert macbook_res == [(960, 600), (1280, 800), (1728, 1117)]
        assert len(macbook_res) == len(set(macbook_res))

        ext32_res = displays[EXTERNAL_32_ID].available_resolutions
        assert ext32_res == [(1920, 1080), (3840, 2160)]

    def test_all_displays_enabled(self, tmp_path):
        displays = parse(tmp_path)
        assert all(d.enabled for d in displays.values())


class TestParsingRobustness:
    def test_malformed_section_is_skipped(self, tmp_path, capsys):
        malformed = (
            DISPLAYPLACER_LIST_OUTPUT
            + "Persistent screen id: DDDDDDDD-1111-2222-3333-444444444444\n"
            + "Type: 24 inch external screen\n"
            + "Resolution: garbagexnonsense\n"
            + "Origin: (not,numbers)\n"
        )
        displays = parse(tmp_path, malformed)
        # The three good displays survive; the malformed one is dropped
        assert len(displays) == 3
        assert "DDDDDDDD-1111-2222-3333-444444444444" not in displays
        captured = capsys.readouterr()
        assert "skipping" in captured.err.lower()

    def test_empty_output_returns_empty_dict(self, tmp_path):
        assert parse(tmp_path, "") == {}

    def test_whitespace_only_output_returns_empty_dict(self, tmp_path):
        assert parse(tmp_path, "\n\n   \n") == {}

    def test_format_drift_line_does_not_crash(self, tmp_path):
        # Lines without ": " separators should be ignored, not raise IndexError
        drifted = (
            "Persistent screen id: AAAAAAAA-1111-2222-3333-444444444444\n"
            "Type: MacBook built in screen\n"
            "Resolution:\n"
            "Hertz:\n"
            "Origin: (0,0) - main display\n"
            "Enabled: true\n"
        )
        displays = parse(tmp_path, drifted)
        assert len(displays) == 1
        display = displays[MACBOOK_ID]
        # Defaults hold when values are missing
        assert display.resolution == (1920, 1080)
        assert display.hz == 60
        assert display.is_main is True
