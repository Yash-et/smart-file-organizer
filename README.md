# 📂 Smart File Organizer

A Python file-organization application with both a command-line interface (CLI) and a desktop GUI. It sorts files into category-based folders, lets you preview proposed moves, and records organization activity for later review.

## ✨ Features

### File organization
- Categorizes files by extension into categories such as Images, Documents, Videos, Music, Archives, Programs, and Others.
- Generates unique destination names to avoid intentionally overwriting existing files.
- Supports configurable categories and extension mappings.
- Supports recursive scanning through the CLI.

### Desktop GUI
- Browse for a folder and preview proposed destinations before organizing.
- Run organization in a background thread so the interface remains responsive.
- Display progress and request cancellation between file operations. Files already moved are not automatically restored.
- Review saved operation history in an in-app table.
- Search history and filter by `SUCCESS` or `FAILED`.
- Export records matching the active search and status filters to a separate CSV file.
- View a statistics dashboard with successful operations, failures, recorded operations, success rate, category counts, and recent activity.

### CLI and safety
- Dry-run mode for previewing CLI operations without moving files.
- Hidden-file and system-file handling.
- Protection against recursively scanning generated category folders.
- Configuration validation and file-operation error handling.

### History and reporting
- GUI operation history is stored in `logs/operation_history.csv`.
- CLI logging and optional report generation are provided by the command-line organizer.
- Dashboard statistics are calculated from recorded history; they cannot account for operations that were never recorded.

## 🛠️ Tech stack

- Python 3
- `pathlib`, `shutil`, and `argparse`
- JSON configuration and CSV history
- `customtkinter` and `tkinter` for the desktop GUI
- `pytest` for automated tests
- `colorama` for terminal output

## 📁 Project structure

```text
smart-file-organizer/
├── organizer.py             # Core organizer and CLI
├── gui.py                   # Desktop GUI
├── operation_history.py     # CSV operation-history utilities
├── requirements.txt         # Python dependencies
├── README.md
├── LICENSE
├── tests/                   # Automated tests
├── logs/                    # Runtime history/logs (generated)
└── reports/                 # Generated reports
```

Some files and folders are created at runtime and may not exist in a fresh clone.

## 🚀 Installation

Clone the repository:

```bash
git clone https://github.com/Yash-et/smart-file-organizer.git
cd smart-file-organizer
```

Create and activate a virtual environment (recommended):

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## 🖥️ Run the desktop application

Start the GUI:

```bash
python gui.py
```

Choose a source folder, select **Preview Organization**, review the proposed destinations, and then select **Organize Files** when ready. The application requires a preview for the selected folder before organizing.

Use **View History** to search and filter saved operations. **Export Filtered History** saves matching records to a separate CSV file and leaves the original history file unchanged. Select **Dashboard** to review summary statistics and recent activity.

## ▶️ Run the CLI

Organize a folder:

```bash
python organizer.py "path/to/folder"
```

Preview the operation without moving files:

```bash
python organizer.py "path/to/folder" --dry-run
```

Scan subdirectories recursively:

```bash
python organizer.py "path/to/folder" --recursive
```

Generate a report:

```bash
python organizer.py "path/to/folder" --report
```

See the available options for your checkout:

```bash
python organizer.py --help
```

## ⚙️ Configuration

The organizer supports JSON-based configuration for file categories, extensions, hidden-file handling, system-file handling, and fallback categorization. Check the project's configuration defaults and CLI help before changing settings.

## 🧪 Run tests

From the repository root:

```bash
python -m pytest -q
```

For verbose output:

```bash
python -m pytest -v
```

## 🛡️ Design principles

- **Safety first:** preview proposed moves and use CLI dry-run mode when appropriate.
- **Non-destructive naming:** avoid intentionally overwriting existing destination files.
- **Responsiveness:** GUI organization runs in a background worker and reports progress.
- **Traceability:** recorded operations can be reviewed, filtered, and exported.
- **Testability:** core behavior is covered by automated tests.

## 📸 Screenshots

### Organization interface
<!-- Add or update the latest GUI screenshot here. -->

### Operation history
<!-- Add or update the latest history-viewer screenshot here. -->

### Statistics dashboard
<!-- Add or update the latest v3.7 dashboard screenshot here. -->

## 📈 Version history

- **v1.x:** Initial file organization utility and early safety improvements.
- **v2.x:** CLI arguments, dry-run mode, recursive scanning, logging, report generation, configurable categories, configuration validation, and expanded tests.
- **v3.x:** Desktop GUI, preview-before-organizing workflow, progress reporting, background organization, cancellation, persistent operation history, searchable/filterable history viewer, and filtered CSV export.
- **v3.7:** Organization statistics dashboard with category counts, recent activity, and operation success-rate metrics based on saved history.

## 📄 License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE) for details.

## 👨‍💻 Author

**Yash**

Built as a practical project in filesystem automation, Python application development, GUI design, configuration management, logging, and software testing.
