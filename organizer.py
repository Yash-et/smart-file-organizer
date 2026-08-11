from pathlib import Path
import argparse
import json
import logging
import shutil
import time

<<<<<<< HEAD
# ==========================================
# Smart File Organizer v1.1
# ==========================================

FILE_TYPES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".ppt", ".pptx", ".xls", ".xlsx", ".csv"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov", ".wmv"],
    "Music": [".mp3", ".wav", ".aac", ".flac"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Programs": [".exe", ".msi"],
}

IGNORED_FILES = {
    "thumbs.db",
    "desktop.ini"
}


def get_folder():
    folder = input(
        "Enter folder path (Press Enter for Downloads): "
    ).strip()

    if folder:
        path = Path(folder)

    else:
        path = Path.home() / "Downloads"

    if not path.exists():
        print("\nFolder does not exist.")
        raise SystemExit

    return path


def get_destination(extension):

    for folder, extensions in FILE_TYPES.items():

        if extension in extensions:
            return folder

    return "Others"


def unique_name(destination, file):

    new_path = destination / file.name

    counter = 1

    while new_path.exists():

        new_path = destination / f"{file.stem}_{counter}{file.suffix}"

        counter += 1

    return new_path
=======
from colorama import Fore, Style, init


# ==========================================
# Smart File Organizer v2.0
# ==========================================

init(autoreset=True)

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"
LOG_DIR = BASE_DIR / "logs"
REPORT_DIR = BASE_DIR / "reports"

LOG_FILE = LOG_DIR / "organizer.log"


DEFAULT_CONFIG = {
    "categories": {
        "Images": [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".webp",
            ".svg"
        ],
        "Documents": [
            ".pdf",
            ".doc",
            ".docx",
            ".txt",
            ".ppt",
            ".pptx",
            ".xls",
            ".xlsx",
            ".csv"
        ],
        "Videos": [
            ".mp4",
            ".mkv",
            ".avi",
            ".mov",
            ".wmv"
        ],
        "Music": [
            ".mp3",
            ".wav",
            ".aac",
            ".flac"
        ],
        "Archives": [
            ".zip",
            ".rar",
            ".7z",
            ".tar",
            ".gz"
        ],
        "Programs": [
            ".exe",
            ".msi"
        ]
    },
    "settings": {
        "others_folder": "Others",
        "skip_hidden_files": True,
        "skip_system_files": True
    }
}


SYSTEM_FILES = {
    "thumbs.db",
    "desktop.ini",
    ".ds_store"
}


def setup_logging():
    """Configure application logging."""

    LOG_DIR.mkdir(exist_ok=True)

    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )


def load_config():
    """Load configuration from config.json."""

    if not CONFIG_FILE.exists():

        with open(CONFIG_FILE, "w", encoding="utf-8") as file:
            json.dump(
                DEFAULT_CONFIG,
                file,
                indent=4
            )

        print(
            Fore.YELLOW
            + "config.json was missing. A default configuration was created."
        )

        return DEFAULT_CONFIG

    try:

        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            config = json.load(file)

        return config

    except json.JSONDecodeError:

        print(
            Fore.RED
            + "Invalid config.json. Using default configuration."
        )

        logging.error(
            "Invalid config.json. Default configuration used."
        )

        return DEFAULT_CONFIG


def parse_arguments():
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Smart File Organizer - organize files automatically."
    )

    parser.add_argument(
        "folder",
        nargs="?",
        help="Folder to organize. Defaults to Downloads."
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without moving files."
    )

    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Scan subdirectories recursively."
    )

    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate a detailed report."
    )

    return parser.parse_args()


def get_target_folder(folder_argument):
    """Resolve the target folder."""

    if folder_argument:

        folder = Path(folder_argument).expanduser()

    else:

        folder = Path.home() / "Downloads"

    if not folder.exists():

        print(
            Fore.RED
            + f"Folder does not exist: {folder}"
        )

        raise SystemExit(1)

    if not folder.is_dir():

        print(
            Fore.RED
            + f"Path is not a directory: {folder}"
        )

        raise SystemExit(1)

    return folder


def get_files(folder, recursive=False):
    """Return files to organize."""

    if recursive:

        return [
            item
            for item in folder.rglob("*")
            if item.is_file()
        ]

    return [
        item
        for item in folder.iterdir()
        if item.is_file()
    ]


def is_ignored(file, config):
    """Determine whether a file should be ignored."""

    settings = config.get("settings", {})

    if settings.get("skip_hidden_files", True):

        if file.name.startswith("."):
            return True

    if settings.get("skip_system_files", True):

        if file.name.lower() in SYSTEM_FILES:
            return True

    return False


def get_category(extension, config):
    """Find category for a file extension."""

    categories = config.get("categories", {})

    extension = extension.lower()

    for category, extensions in categories.items():

        normalized_extensions = [
            ext.lower()
            for ext in extensions
        ]

        if extension in normalized_extensions:
            return category

    return config.get(
        "settings",
        {}
    ).get(
        "others_folder",
        "Others"
    )


def get_unique_destination(destination, file):
    """Prevent filename conflicts."""

    target = destination / file.name

    counter = 1

    while target.exists():

        target = (
            destination
            / f"{file.stem}_{counter}{file.suffix}"
        )

        counter += 1

    return target


def organize_file(file, category, root_folder, dry_run=False):
    """Move a file into its category."""

    destination = root_folder / category

    destination.mkdir(
        exist_ok=True
    )

    target = get_unique_destination(
        destination,
        file
    )

    if dry_run:

        print(
            Fore.CYAN
            + f"[DRY RUN] {file.name}"
        )

        print(
            f"          → {category}"
        )

        return True, target

    try:

        shutil.move(
            str(file),
            str(target)
        )

        print(
            Fore.GREEN
            + f"✓ {file.name}"
        )

        print(
            f"  → {category}"
        )

        logging.info(
            f"Moved: {file} -> {target}"
        )

        return True, target

    except Exception as error:

        print(
            Fore.RED
            + f"✗ Failed: {file.name}"
        )

        print(
            f"  Reason: {error}"
        )

        logging.error(
            f"Failed to move {file}: {error}"
        )

        return False, target


def generate_report(
    root_folder,
    stats,
    total,
    skipped,
    failed,
    dry_run,
    elapsed
):
    """Generate a text report."""

    REPORT_DIR.mkdir(
        exist_ok=True
    )

    timestamp = time.strftime(
        "%Y%m%d_%H%M%S"
    )

    report_file = (
        REPORT_DIR
        / f"report_{timestamp}.txt"
    )

    with open(
        report_file,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "SMART FILE ORGANIZER REPORT\n"
        )

        file.write(
            "=" * 50 + "\n\n"
        )

        file.write(
            f"Folder: {root_folder}\n"
        )

        file.write(
            f"Dry Run: {dry_run}\n\n"
        )

        file.write(
            "CATEGORY STATISTICS\n"
        )

        file.write(
            "-" * 50 + "\n"
        )

        for category in sorted(stats):

            file.write(
                f"{category}: {stats[category]}\n"
            )

        file.write(
            "\n"
        )

        file.write(
            f"Moved/Planned : {total}\n"
        )

        file.write(
            f"Skipped       : {skipped}\n"
        )

        file.write(
            f"Failed        : {failed}\n"
        )

        file.write(
            f"Time Taken    : {elapsed:.2f} seconds\n"
        )

    return report_file
>>>>>>> d6961ad (Release Smart File Organizer v2.0)


def main():

<<<<<<< HEAD
    folder = get_folder()

    start = time.time()

    total = 0

    skipped = 0

=======
    setup_logging()

    args = parse_arguments()

    config = load_config()

    folder = get_target_folder(
        args.folder
    )

    print()
    print(
        Fore.MAGENTA
        + "=" * 60
    )

    print(
        Fore.MAGENTA
        + " SMART FILE ORGANIZER v2.0"
    )

    print(
        Fore.MAGENTA
        + "=" * 60
    )

    print(
        f"Folder    : {folder}"
    )

    print(
        f"Recursive : {args.recursive}"
    )

    print(
        f"Dry Run   : {args.dry_run}"
    )

    print(
        Fore.MAGENTA
        + "=" * 60
    )

    start = time.time()

    files = get_files(
        folder,
        recursive=args.recursive
    )

    total = 0
    skipped = 0
>>>>>>> d6961ad (Release Smart File Organizer v2.0)
    failed = 0

    stats = {}

<<<<<<< HEAD
    print("\n" + "=" * 60)
    print(" SMART FILE ORGANIZER v1.1 ")
    print("=" * 60)

    for item in folder.iterdir():

        if item.is_dir():
            continue

        if item.name.startswith("."):
            skipped += 1
            continue

        if item.name.lower() in IGNORED_FILES:
            skipped += 1
            continue

        category = get_destination(item.suffix.lower())

        destination = folder / category

        destination.mkdir(exist_ok=True)

        destination_file = unique_name(destination, item)

        try:

            shutil.move(str(item), str(destination_file))

            total += 1

            stats[category] = stats.get(category, 0) + 1

            print(f"✓ {item.name}")
            print(f"  → {category}")

        except Exception as e:

            failed += 1

            print(f"✗ Could not move {item.name}")
            print(f"  Reason: {e}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for category in sorted(stats):

        print(f"{category:<15}: {stats[category]}")

    print("-" * 60)

    print(f"Moved Files     : {total}")
    print(f"Skipped Files   : {skipped}")
    print(f"Failed Files    : {failed}")

    print(f"Time Taken      : {time.time()-start:.2f} seconds")

    print("=" * 60)
=======
    for file in files:

        if is_ignored(
            file,
            config
        ):

            skipped += 1

            logging.info(
                f"Skipped: {file}"
            )

            continue

        category = get_category(
            file.suffix,
            config
        )

        success, _ = organize_file(
            file=file,
            category=category,
            root_folder=folder,
            dry_run=args.dry_run
        )

        if success:

            total += 1

            stats[category] = (
                stats.get(category, 0)
                + 1
            )

        else:

            failed += 1

    elapsed = time.time() - start

    print()
    print(
        Fore.MAGENTA
        + "=" * 60
    )

    print(
        Fore.MAGENTA
        + " SUMMARY"
    )

    print(
        Fore.MAGENTA
        + "=" * 60
    )

    if stats:

        for category in sorted(stats):

            print(
                f"{category:<15}: {stats[category]}"
            )

    else:

        print("No files processed.")

    print("-" * 60)

    print(
        f"Processed       : {total}"
    )

    print(
        f"Skipped         : {skipped}"
    )

    print(
        f"Failed          : {failed}"
    )

    print(
        f"Time Taken      : {elapsed:.2f} seconds"
    )

    if args.report:

        report = generate_report(
            root_folder=folder,
            stats=stats,
            total=total,
            skipped=skipped,
            failed=failed,
            dry_run=args.dry_run,
            elapsed=elapsed
        )

        print()
        print(
            Fore.GREEN
            + f"Report created: {report}"
        )

    print(
        Fore.MAGENTA
        + "=" * 60
    )
>>>>>>> d6961ad (Release Smart File Organizer v2.0)


if __name__ == "__main__":
    main()