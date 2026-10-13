
import csv
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
HISTORY_FILE = LOG_DIR / "operation_history.csv"

FIELDNAMES = [
    "timestamp",
    "source_folder",
    "source_file",
    "destination",
    "category",
    "status",
    "error",
]


def ensure_history_file():
    """Create the history CSV and its header if needed."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    if not HISTORY_FILE.exists() or HISTORY_FILE.stat().st_size == 0:
        with HISTORY_FILE.open(
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writeheader()

    return HISTORY_FILE


def record_operation(
    source_folder,
    source_file,
    destination,
    category,
    status,
    error="",
):
    """Append one attempted file operation to the CSV history."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    file_exists = (
        HISTORY_FILE.exists() and HISTORY_FILE.stat().st_size > 0
    )

    record = {
        "timestamp": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "source_folder": str(source_folder),
        "source_file": str(source_file),
        "destination": str(destination),
        "category": category,
        "status": status,
        "error": error or "",
    }

    with HISTORY_FILE.open(
        "a",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)

        if not file_exists:
            writer.writeheader()

        writer.writerow(record)
