"""Tests for layout persistence and displayplacer command generation."""

import json
from dataclasses import asdict
from datetime import datetime

from conftest import (
    DISPLAYPLACER_LIST_OUTPUT,
    MACBOOK_ID,
    EXTERNAL_27_ID,
    EXTERNAL_32_ID,
)
from core.advanced_display_manager import AdvancedDisplayManager, LayoutProfile


def make_manager(tmp_path, filename="layouts.json"):
    return AdvancedDisplayManager(layouts_file=str(tmp_path / filename))


def sample_config():
    """A three-display layout config as the GUI would provide it."""
    return {
        MACBOOK_ID: {
            "resolution": [1728, 1117],
            "position": [0, 0],
            "hz": 120,
            "scaling": True,
            "is_main": True,
            "rotation": 0,
            "color_depth": 8,
        },
        EXTERNAL_27_ID: {
            "resolution": [1920, 1080],
            "position": [1728, -996],
            "hz": 60,
            "scaling": False,
            "is_main": False,
            "rotation": 0,
            "color_depth": 8,
        },
        EXTERNAL_32_ID: {
            "resolution": [1920, 1080],
            "position": [-192, -1080],
            "hz": 100,
            "scaling": True,
            "is_main": False,
            "rotation": 0,
            "color_depth": 8,
        },
    }


def seed_displays(manager):
    """Seed manager.displays from the parser fixture (no live detection)."""
    manager.displays = manager._parse_display_output(DISPLAYPLACER_LIST_OUTPUT)


def capture_commands(manager, result=True):
    """Monkeypatch command execution, capturing the generated commands."""
    captured = []

    def fake_execute(commands):
        captured.extend(commands)
        return result

    manager._execute_displayplacer_commands = fake_execute
    return captured


def parts_for(commands, display_id):
    """Return the command string for a given display id."""
    for cmd in commands:
        if cmd.startswith(f"id:{display_id}"):
            return cmd
    raise AssertionError(f"No command generated for {display_id}")


def origin_of(cmd):
    """Extract the (x, y) origin tuple from a displayplacer command string."""
    for part in cmd.split():
        if part.startswith("origin:"):
            x, y = part[len("origin:("):-1].split(",")
            return int(x), int(y)
    raise AssertionError(f"No origin in command: {cmd}")


class TestLayoutPersistence:
    def test_save_layout_from_config_round_trip(self, tmp_path):
        manager = make_manager(tmp_path)
        assert manager.save_layout_from_config("Desk", "Home office", sample_config())

        layout = manager.get_layout("Desk")
        assert layout is not None
        assert layout.name == "Desk"
        assert layout.description == "Home office"
        assert layout.displays == sample_config()
        assert layout.created_at  # stamped
        assert layout.last_used == ""

        # Persisted: a fresh manager on the same file sees the layout
        manager2 = make_manager(tmp_path)
        layout2 = manager2.get_layout("Desk")
        assert layout2 is not None
        assert layout2.displays == sample_config()

    def test_save_layout_from_config_empty_rejected(self, tmp_path):
        manager = make_manager(tmp_path)
        assert manager.save_layout_from_config("Empty", "", {}) is False
        assert manager.get_layout("Empty") is None

    def test_delete_layout(self, tmp_path):
        manager = make_manager(tmp_path)
        manager.save_layout_from_config("Doomed", "", sample_config())
        assert "Doomed" in manager.get_layout_names()

        assert manager.delete_layout("Doomed") is True
        assert manager.get_layout_names() == []
        assert manager.delete_layout("Doomed") is False

        # Deletion persisted
        manager2 = make_manager(tmp_path)
        assert manager2.get_layout_names() == []

    def test_export_import_round_trip(self, tmp_path):
        manager = make_manager(tmp_path, "source.json")
        manager.save_layout_from_config("Desk", "Home office", sample_config())

        # Export (same shape the CLI export command writes)
        export_file = tmp_path / "export.json"
        export_data = {
            name: asdict(manager.get_layout(name))
            for name in manager.get_layout_names()
        }
        export_file.write_text(json.dumps(export_data, indent=2))

        # Import into a separate manager (same shape the CLI import uses)
        manager2 = make_manager(tmp_path, "target.json")
        imported = json.loads(export_file.read_text())
        for name, layout_data in imported.items():
            manager2.layouts[name] = LayoutProfile(**layout_data)
        manager2.save_layouts()

        # Round-trip preserved everything
        manager3 = make_manager(tmp_path, "target.json")
        layout = manager3.get_layout("Desk")
        assert layout is not None
        assert layout.description == "Home office"
        assert layout.displays == sample_config()


class TestApplyLayout:
    def test_command_parts_formatted_correctly(self, tmp_path):
        manager = make_manager(tmp_path)
        seed_displays(manager)
        commands = capture_commands(manager)
        manager.save_layout_from_config("Desk", "", sample_config())

        assert manager.apply_layout("Desk") is True
        assert len(commands) == 3

        macbook_cmd = parts_for(commands, MACBOOK_ID)
        assert f"id:{MACBOOK_ID}" in macbook_cmd
        assert "res:1728x1117" in macbook_cmd
        assert "hz:120" in macbook_cmd
        assert "scaling:on" in macbook_cmd
        assert "origin:(0,0)" in macbook_cmd
        assert "degree:0" in macbook_cmd
        assert "color_depth:8" in macbook_cmd

        ext27_cmd = parts_for(commands, EXTERNAL_27_ID)
        assert "res:1920x1080" in ext27_cmd
        assert "hz:60" in ext27_cmd
        assert "scaling:off" in ext27_cmd
        assert "origin:(1728,-996)" in ext27_cmd

        ext32_cmd = parts_for(commands, EXTERNAL_32_ID)
        assert "hz:100" in ext32_cmd
        assert "scaling:on" in ext32_cmd
        assert "origin:(-192,-1080)" in ext32_cmd

    def test_new_main_display_renormalizes_origins(self, tmp_path):
        manager = make_manager(tmp_path)
        seed_displays(manager)
        commands = capture_commands(manager)

        # Same physical arrangement, but the 27-inch external is now main
        config = sample_config()
        config[MACBOOK_ID]["is_main"] = False
        config[EXTERNAL_27_ID]["is_main"] = True
        manager.save_layout_from_config("ExtMain", "", config)

        assert manager.apply_layout("ExtMain") is True

        origins = {
            MACBOOK_ID: origin_of(parts_for(commands, MACBOOK_ID)),
            EXTERNAL_27_ID: origin_of(parts_for(commands, EXTERNAL_27_ID)),
            EXTERNAL_32_ID: origin_of(parts_for(commands, EXTERNAL_32_ID)),
        }

        # The new main display must sit at CoreGraphics origin (0,0)
        assert origins[EXTERNAL_27_ID] == (0, 0)
        # All origins shifted by the same delta (-1728, +996)
        assert origins[MACBOOK_ID] == (-1728, 996)
        assert origins[EXTERNAL_32_ID] == (-1920, -84)

        # Relative offsets between displays are preserved exactly
        old = {k: tuple(v["position"]) for k, v in config.items()}
        for a in origins:
            for b in origins:
                assert (
                    origins[a][0] - origins[b][0],
                    origins[a][1] - origins[b][1],
                ) == (old[a][0] - old[b][0], old[a][1] - old[b][1])

    def test_no_main_display_keeps_origins_as_is(self, tmp_path):
        manager = make_manager(tmp_path)
        seed_displays(manager)
        commands = capture_commands(manager)

        config = sample_config()
        for cfg in config.values():
            cfg["is_main"] = False
        manager.save_layout_from_config("NoMain", "", config)

        assert manager.apply_layout("NoMain") is True
        assert origin_of(parts_for(commands, MACBOOK_ID)) == (0, 0)
        assert origin_of(parts_for(commands, EXTERNAL_27_ID)) == (1728, -996)
        assert origin_of(parts_for(commands, EXTERNAL_32_ID)) == (-192, -1080)

    def test_last_used_stamped_on_success(self, tmp_path):
        manager = make_manager(tmp_path)
        seed_displays(manager)
        capture_commands(manager, result=True)
        manager.save_layout_from_config("Desk", "", sample_config())

        before = datetime.now()
        assert manager.apply_layout("Desk") is True

        layout = manager.get_layout("Desk")
        assert layout.last_used != ""
        stamped = datetime.fromisoformat(layout.last_used)
        assert stamped >= before.replace(microsecond=0)

        # Stamp is persisted to disk
        manager2 = make_manager(tmp_path)
        assert manager2.get_layout("Desk").last_used == layout.last_used

    def test_last_used_not_stamped_on_failure(self, tmp_path):
        manager = make_manager(tmp_path)
        seed_displays(manager)
        capture_commands(manager, result=False)
        manager.save_layout_from_config("Desk", "", sample_config())

        assert manager.apply_layout("Desk") is False
        assert manager.get_layout("Desk").last_used == ""

    def test_apply_unknown_layout_fails(self, tmp_path):
        manager = make_manager(tmp_path)
        seed_displays(manager)
        capture_commands(manager)
        assert manager.apply_layout("Nope") is False


class TestApplyDisplayConfig:
    """apply_display_config: the GUI's one-shot apply path (no layouts touched)."""

    def test_never_persists_anything(self, tmp_path):
        """Regression: GUI Apply used to leak temp '_apply_*' layouts to disk."""
        layouts_file = tmp_path / "layouts.json"
        manager = AdvancedDisplayManager(layouts_file=str(layouts_file))
        seed_displays(manager)
        manager.save_layout_from_config("Real", "", sample_config())

        commands = capture_commands(manager)
        assert manager.apply_display_config(sample_config()) is True
        assert len(commands) == 3

        # In memory and on disk: only the real layout, nothing transient
        assert manager.get_layout_names() == ["Real"]
        on_disk = json.loads(layouts_file.read_text())
        assert list(on_disk.keys()) == ["Real"]
        assert not any(k.startswith("_apply_") for k in on_disk)

    def test_no_connected_displays_fails(self, tmp_path):
        manager = make_manager(tmp_path)
        manager.displays = {}          # nothing detected
        commands = capture_commands(manager)
        assert manager.apply_display_config(sample_config()) is False
        assert commands == []

    def test_layout_with_no_connected_displays_fails_without_stamp(self, tmp_path):
        manager = make_manager(tmp_path)
        manager.displays = {}
        capture_commands(manager)
        manager.save_layout_from_config("Ghost", "", sample_config())

        assert manager.apply_layout("Ghost") is False
        assert manager.get_layout("Ghost").last_used == ""

    def test_disconnected_main_falls_back_to_connected_anchor(self, tmp_path):
        """A layout whose marked main is unplugged must still put a
        connected display at CoreGraphics origin (0,0)."""
        manager = make_manager(tmp_path)
        seed_displays(manager)
        del manager.displays[MACBOOK_ID]   # the marked main is not connected
        commands = capture_commands(manager)

        assert manager.apply_display_config(sample_config()) is True
        assert len(commands) == 2

        origins = {
            EXTERNAL_27_ID: origin_of(parts_for(commands, EXTERNAL_27_ID)),
            EXTERNAL_32_ID: origin_of(parts_for(commands, EXTERNAL_32_ID)),
        }
        # One of the connected displays is anchored at (0,0)…
        assert (0, 0) in origins.values()
        # …and the relative offset between the two is preserved
        assert (
            origins[EXTERNAL_27_ID][0] - origins[EXTERNAL_32_ID][0],
            origins[EXTERNAL_27_ID][1] - origins[EXTERNAL_32_ID][1],
        ) == (1728 - (-192), -996 - (-1080))
