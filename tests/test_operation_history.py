import csv
import operation_history

def test_history_records_success_and_failure(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    history_file = log_dir / "operation_history.csv"

    monkeypatch.setattr(operation_history, "LOG_DIR", log_dir)
    monkeypatch.setattr(
        operation_history, "HISTORY_FILE", history_file
    )

    operation_history.record_operation(
        source_folder=tmp_path,
        source_file=tmp_path / "photo.jpg",
        destination=tmp_path / "Images" / "photo.jpg",
        category="Images",
        status="SUCCESS",
    )

    operation_history.record_operation(
        source_folder=tmp_path,
        source_file=tmp_path / "broken.pdf",
        destination=tmp_path / "Documents" / "broken.pdf",
        category="Documents",
        status="FAILED",
        error="Permission denied",
    )

    with history_file.open(
        "r", newline="", encoding="utf-8-sig"
    ) as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 2
    assert rows[0]["status"] == "SUCCESS"
    assert rows[0]["category"] == "Images"
    assert rows[1]["status"] == "FAILED"
    assert rows[1]["error"] == "Permission denied"
    assert rows[0]["timestamp"]
