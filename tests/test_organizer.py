import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import organizer
import organizer


# ============================================================
# Configuration
# ============================================================

VALID_CONFIG = {
    "categories": {
        "Images": [".jpg", ".png"],
        "Documents": [".pdf", ".txt"],
        "Videos": [".mp4"],
    },
    "settings": {
        "others_folder": "Others",
        "skip_hidden_files": True,
        "skip_system_files": True,
    },
}


# ============================================================
# Category Tests
# ============================================================

def test_get_category_image():
    category = organizer.get_category(".jpg", VALID_CONFIG)
    assert category == "Images"


def test_get_category_document():
    category = organizer.get_category(".pdf", VALID_CONFIG)
    assert category == "Documents"


def test_get_category_unknown_extension():
    category = organizer.get_category(".xyz", VALID_CONFIG)
    assert category == "Others"


def test_get_category_case_insensitive():
    category = organizer.get_category(".JPG", VALID_CONFIG)
    assert category == "Images"


# ============================================================
# Duplicate Filename Tests
# ============================================================

def test_get_unique_destination(tmp_path):
    destination = tmp_path / "Documents"
    destination.mkdir()

    original = tmp_path / "report.txt"
    original.write_text("original")

    existing = destination / "report.txt"
    existing.write_text("existing")

    result = organizer.get_unique_destination(destination, original)

    assert result.name == "report_1.txt"


def test_get_unique_destination_multiple_duplicates(tmp_path):
    destination = tmp_path / "Documents"
    destination.mkdir()

    original = tmp_path / "report.txt"
    original.write_text("original")

    (destination / "report.txt").write_text("existing")
    (destination / "report_1.txt").write_text("existing")
    (destination / "report_2.txt").write_text("existing")

    result = organizer.get_unique_destination(destination, original)

    assert result.name == "report_3.txt"


# ============================================================
# Ignored File Tests
# ============================================================

def test_hidden_file_is_ignored(tmp_path):
    hidden_file = tmp_path / ".hidden.txt"
    hidden_file.write_text("hidden")

    assert organizer.is_ignored(hidden_file, VALID_CONFIG) is True


def test_system_file_is_ignored(tmp_path):
    system_file = tmp_path / "thumbs.db"
    system_file.write_text("system")

    assert organizer.is_ignored(system_file, VALID_CONFIG) is True


def test_desktop_ini_is_ignored(tmp_path):
    system_file = tmp_path / "desktop.ini"
    system_file.write_text("system")

    assert organizer.is_ignored(system_file, VALID_CONFIG) is True


def test_normal_file_is_not_ignored(tmp_path):
    normal_file = tmp_path / "document.txt"
    normal_file.write_text("normal")

    assert organizer.is_ignored(normal_file, VALID_CONFIG) is False


# ============================================================
# Dry-Run Tests
# ============================================================

def test_dry_run_does_not_move_file(tmp_path):
    source = tmp_path / "document.txt"
    source.write_text("test document")

    organizer.organize_file(
        file=source,
        category="Documents",
        root_folder=tmp_path,
        dry_run=True,
    )

    assert source.exists()
    assert not (tmp_path / "Documents" / "document.txt").exists()


def test_dry_run_does_not_create_destination_folder(tmp_path):
    source = tmp_path / "document.txt"
    source.write_text("test document")

    destination = tmp_path / "Documents"

    assert not destination.exists()

    organizer.organize_file(
        file=source,
        category="Documents",
        root_folder=tmp_path,
        dry_run=True,
    )

    assert not destination.exists()


# ============================================================
# Actual File Move Test
# ============================================================

def test_organize_file_moves_file(tmp_path):
    source = tmp_path / "document.txt"
    source.write_text("test document")

    organizer.organize_file(
        file=source,
        category="Documents",
        root_folder=tmp_path,
        dry_run=False,
    )

    destination = tmp_path / "Documents" / "document.txt"

    assert not source.exists()
    assert destination.exists()
    assert destination.read_text() == "test document"


# ============================================================
# Recursive Scanning Tests
# ============================================================

def test_get_files_non_recursive(tmp_path):
    root_file = tmp_path / "root.txt"
    root_file.write_text("root")

    nested = tmp_path / "nested"
    nested.mkdir()

    nested_file = nested / "nested.txt"
    nested_file.write_text("nested")

    files = organizer.get_files(tmp_path, recursive=False)

    assert root_file in files
    assert nested_file not in files


def test_get_files_recursive(tmp_path):
    root_file = tmp_path / "root.txt"
    root_file.write_text("root")

    nested = tmp_path / "nested"
    nested.mkdir()

    nested_file = nested / "nested.txt"
    nested_file.write_text("nested")

    files = organizer.get_files(tmp_path, recursive=True)

    assert root_file in files
    assert nested_file in files


def test_recursive_scan_ignores_output_folders(tmp_path):
    root_file = tmp_path / "root.txt"
    root_file.write_text("root")

    documents = tmp_path / "Documents"
    documents.mkdir()

    organized_file = documents / "already_organized.txt"
    organized_file.write_text("organized")

    files = organizer.get_files(tmp_path, recursive=True)

    assert root_file in files
    assert organized_file not in files


# ============================================================
# Configuration Validation Tests
# ============================================================

def test_valid_config_is_accepted():
    result = organizer.validate_config(VALID_CONFIG)

    assert result == VALID_CONFIG


def test_invalid_config_type_is_rejected():
    with pytest.raises(ValueError):
        organizer.validate_config([])


def test_missing_categories_is_rejected():
    config = {
        "settings": VALID_CONFIG["settings"]
    }

    with pytest.raises(ValueError):
        organizer.validate_config(config)


def test_invalid_extension_is_rejected():
    config = {
        "categories": {
            "Images": ["jpg"]
        },
        "settings": VALID_CONFIG["settings"],
    }

    with pytest.raises(ValueError):
        organizer.validate_config(config)


def test_invalid_skip_hidden_files_setting_is_rejected():
    config = {
        "categories": VALID_CONFIG["categories"],
        "settings": {
            "others_folder": "Others",
            "skip_hidden_files": "yes",
            "skip_system_files": True,
        },
    }

    with pytest.raises(ValueError):
        organizer.validate_config(config)


def test_invalid_skip_system_files_setting_is_rejected():
    config = {
        "categories": VALID_CONFIG["categories"],
        "settings": {
            "others_folder": "Others",
            "skip_hidden_files": True,
            "skip_system_files": "yes",
        },
    }

    with pytest.raises(ValueError):
        organizer.validate_config(config)


def test_invalid_others_folder_is_rejected():
    config = {
        "categories": VALID_CONFIG["categories"],
        "settings": {
            "others_folder": "../Others",
            "skip_hidden_files": True,
            "skip_system_files": True,
        },
    }

    with pytest.raises(ValueError):
        organizer.validate_config(config)


# ============================================================
# Logging Test
# ============================================================

def test_setup_logging():
    organizer.setup_logging()

    assert organizer.LOG_DIR.exists()


# ============================================================
# Basic Integration Test
# ============================================================

def test_multiple_files_can_be_organized(tmp_path):
    image = tmp_path / "photo.jpg"
    document = tmp_path / "report.pdf"
    unknown = tmp_path / "data.xyz"

    image.write_text("image")
    document.write_text("document")
    unknown.write_text("unknown")

    files = organizer.get_files(tmp_path)

    stats = {}

    for file in files:
        category = organizer.get_category(file.suffix, VALID_CONFIG)

        success, _ = organizer.organize_file(
            file=file,
            category=category,
            root_folder=tmp_path,
            dry_run=False,
        )

        if success:
            stats[category] = stats.get(category, 0) + 1

    assert (tmp_path / "Images" / "photo.jpg").exists()
    assert (tmp_path / "Documents" / "report.pdf").exists()
    assert (tmp_path / "Others" / "data.xyz").exists()

    assert stats["Images"] == 1
    assert stats["Documents"] == 1
    assert stats["Others"] == 1