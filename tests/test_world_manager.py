import json
from pathlib import Path

import pytest

import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

import world_duplicator
from world_duplicator import WorldManager


@pytest.fixture
def sample_save_dir(tmp_path: Path) -> Path:
    """Create a fake save directory with two worlds and metadata."""
    metadata = {
        "worlds": [
            {
                "id": "world1",
                "name": "World One",
                "createdAt": 0,
                "lastPlayed": 0,
            },
            {
                "id": "world2",
                "name": "World Two",
                "createdAt": 0,
                "lastPlayed": 0,
            },
        ]
    }
    (tmp_path / "enshrouded_user.json").write_text(json.dumps(metadata))

    # World 1 files
    (tmp_path / "world1-index").write_text(
        json.dumps({"id": "world1", "time": 0, "deleted": False, "latest": 1})
    )
    (tmp_path / "world1-data").write_text("source")

    # World 2 files
    (tmp_path / "world2-index").write_text(
        json.dumps({"id": "world2", "time": 0, "deleted": False, "latest": 2})
    )
    (tmp_path / "world2-data").write_text("target")

    return tmp_path


def test_set_save_directory(sample_save_dir: Path) -> None:
    wm = WorldManager()
    wm.set_save_directory(sample_save_dir)

    assert wm.save_dir == sample_save_dir
    assert "world1" in wm.worlds and "world2" in wm.worlds


def test_scan_worlds(sample_save_dir: Path) -> None:
    wm = WorldManager()
    wm.set_save_directory(sample_save_dir)
    world_list = wm.scan_worlds()

    ids = {world_id for _, world_id in world_list}
    assert ids == {"world1", "world2"}


def test_duplicate_world(sample_save_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    wm = WorldManager()
    wm.set_save_directory(sample_save_dir)

    # Freeze time for predictable results
    monkeypatch.setattr(world_duplicator.time, "time", lambda: 1234567890)
    monkeypatch.setattr(
        world_duplicator.time, "strftime", lambda fmt: "20200101000000"
    )

    backup_dir = wm.duplicate_world("world1", "world2")
    assert backup_dir is not None
    assert backup_dir.is_dir()

    # Original target files should be in the backup directory
    assert (backup_dir / "world2-data").read_text() == "target"
    assert (backup_dir / "world2-index").exists()

    # Target files should now match source contents
    assert (sample_save_dir / "world2-data").read_text() == "source"

    index_data = json.loads((sample_save_dir / "world2-index").read_text())
    assert index_data["time"] == 1234567890
    assert index_data["deleted"] is False
    assert index_data["latest"] == 1

    metadata = json.loads((sample_save_dir / "enshrouded_user.json").read_text())
    world2_meta = next(w for w in metadata["worlds"] if w["id"] == "world2")
    assert world2_meta["name"] == "Copy of World One"
    assert world2_meta["lastPlayed"] == 1234567890


def test_duplicate_world_rollback(sample_save_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure target files are restored if duplication fails."""
    wm = WorldManager()
    wm.set_save_directory(sample_save_dir)

    # Force shutil.copy2 to fail after first call
    original_copy = world_duplicator.shutil.copy2

    def failing_copy(src, dst, *args, **kwargs):
        if failing_copy.called:
            raise RuntimeError("copy failed")
        failing_copy.called = True
        return original_copy(src, dst, *args, **kwargs)

    failing_copy.called = False
    monkeypatch.setattr(world_duplicator.shutil, "copy2", failing_copy)

    result = wm.duplicate_world("world1", "world2")
    assert result is None

    # Target files should be restored to their original state
    assert (sample_save_dir / "world2-data").read_text() == "target"
    assert (sample_save_dir / "world2-index").exists()

    # No backup directories should remain
    assert not any(sample_save_dir.glob("world2_backup_*"))
