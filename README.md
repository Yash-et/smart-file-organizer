# 📂 Smart File Organizer

A lightweight and configurable Python command-line utility that automatically organizes files into category-based folders based on their extensions.

The project started as a simple file-sorting script and has evolved into a safer, configurable CLI utility with recursive scanning, dry-run support, duplicate-name handling, reporting, logging, configuration validation, and automated tests.

## ✨ Features

### Core Organization

* Automatically categorizes files based on their extensions
* Supports categories such as:

  * Images
  * Documents
  * Videos
  * Music
  * Archives
  * Programs
  * Others
* Preserves existing files by generating unique destination names when duplicates exist

### Safety Features

* Dry-run mode to preview changes without moving files
* Skips hidden files when configured
* Skips system files
* Prevents organizer output folders from being scanned recursively
* Handles file-operation errors without terminating the entire process
* Validates custom configuration before using it

### CLI Features

* Organize a specified folder
* Recursive directory scanning
* Dry-run preview
* Report generation
* Command-line help and usage information

### Logging & Reporting

* Operation logs are maintained separately
* Optional organization reports can be generated
* Reports contain information about processed files and organization results

### Testing

The project includes an automated pytest test suite covering:

* File categorization
* Duplicate destination handling
* Hidden/system file handling
* Dry-run behavior
* Actual file movement
* Recursive scanning
* Configuration validation
* Logging
* Integration behavior

**Current test status: 25 tests passed.**

---

## 🛠️ Tech Stack

* **Python 3**
* **pathlib** - filesystem handling
* **shutil** - file movement
* **argparse** - command-line interface
* **JSON** - configuration
* **logging** - operation logging
* **Colorama** - terminal output
* **pytest** - automated testing

---

## 📁 Project Structure

```text
smart-file-organizer/
│
├── organizer.py          # Main application
├── README.md             # Project documentation
├── requirements.txt      # Python dependencies
├── .gitignore
│
├── tests/
│   └── test_organizer.py # Automated test suite
│
├── logs/
│   └── .gitkeep
│
└── reports/
    └── .gitkeep
```
---

## 🚀 Installation

Clone the repository:

```bash
git clone <https://github.com/Yash-et/smart-file-organizer>
cd smart-file-organizer
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

---

## ▶️ Basic Usage

Run the organizer on a folder:

```bash
python organizer.py "path/to/folder"
```

For example:

```bash
python organizer.py "C:\Users\YourName\Downloads"
```

---

## 🔍 Dry Run

Preview what would happen without moving any files:

```bash
python organizer.py "path/to/folder" --dry-run
```

Dry-run mode does not create destination folders or move files.

This makes it useful for safely checking the organization plan before applying changes.

---

## 📂 Recursive Organization

To scan files inside subdirectories:

```bash
python organizer.py "path/to/folder" --recursive
```

The organizer automatically avoids scanning its own generated category folders during recursive processing.

---

## 📊 Generate a Report

A report can be generated while organizing:

```bash
python organizer.py "path/to/folder" --report
```

Generated reports are stored separately from the source files.

---

## ⚙️ Configuration

The organizer supports a JSON-based configuration system.

Configuration can control:

* File categories
* File extensions
* Hidden-file handling
* System-file handling
* The fallback `Others` directory

Invalid configuration values are detected and the application safely falls back to the default configuration.

This allows the organizer to be adapted to different workflows without changing the core Python code.

---

## 🧪 Running Tests

Install pytest if required:

```bash
pip install pytest
```

Run the complete test suite:

```bash
pytest -v
```

Current test coverage includes 25 automated tests for the organizer's core functionality and integration behavior.

---

## 🖥️ Example Workflow

Before:

```text
Downloads/
├── photo.jpg
├── report.pdf
├── song.mp3
├── archive.zip
└── presentation.pptx
```

After running the organizer:

```text
Downloads/
├── Images/
│   └── photo.jpg
│
├── Documents/
│   ├── report.pdf
│   └── presentation.pptx
│
├── Music/
│   └── song.mp3
│
└── Archives/
    └── archive.zip
```

---

## 🔐 Design Principles

The project is designed around a few practical principles:

**Safety first**

Files should not be moved unexpectedly. Dry-run mode and configuration validation provide an additional safety layer.

**Non-destructive organization**

Existing files are not overwritten. When a destination filename already exists, a unique filename is generated.

**Configurable behavior**

File categories and supported extensions can be customized without modifying the application's core logic.

**Testable functionality**

Important filesystem and organization behaviors are covered by automated tests.

**Simple CLI**

The project remains lightweight and usable directly from the terminal without requiring a graphical interface.

---

## 📈 Project Versions

### v1.0

Initial file organization utility.

### v1.1

Improved file categorization, duplicate handling, safety checks, and user-friendly output.

### v2.0

Introduced:

* Command-line arguments
* Dry-run mode
* Recursive scanning
* Logging
* Report generation
* Configurable categories
* Safer filesystem handling

### v2.1

Introduced:

* Configuration validation
* Improved dry-run protection
* Recursive output-folder protection
* Expanded automated testing
* 25 passing pytest tests
* Cleaned project configuration and Git ignore rules

---

## 🔮 Future Development

Potential future improvements include:

* Graphical user interface
* Custom category management through the UI
* Organization history
* Undo functionality
* File preview
* Scheduled organization
* More detailed statistics
* Cross-platform packaging

---

## 📄 License

This project is licensed under the MIT License.

See the `LICENSE` file for details.

---

## 👨‍💻 Author

**Yash**

Built as a practical Python project focused on filesystem automation, CLI development, configuration management, and software testing.
