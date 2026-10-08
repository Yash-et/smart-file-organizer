from pathlib import Path
import argparse
import json
import logging
import shutil
import time

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

def validate_config(config):
    """Validate configuration structure and values."""

    if not isinstance(config, dict):
        raise ValueError("Config must be a JSON object.")

    categories = config.get("categories")
    settings = config.get("settings")

    if not isinstance(categories, dict) or not categories:
        raise ValueError("Categories must be a non-empty object.")

    if not isinstance(settings, dict):
        raise ValueError("Settings must be an object.")

    for category, extensions in categories.items():
        if not isinstance(category, str) or not category.strip():
            raise ValueError("Category names must be non-empty strings.")

        if category in {".", ".."} or "/" in category or "\\" in category:
            raise ValueError(f"Invalid category name: {category}")

        if not isinstance(extensions, list):
            raise ValueError(
                f"Extensions for {category} must be a list."
            )

        for ext in extensions:
            if (
                not isinstance(ext, str)
                or not ext.startswith(".")
                or len(ext) < 2
                or "/" in ext
                or "\\" in ext
            ):
                raise ValueError(
                    f"Invalid extension in {category}: {ext}"
                )

    others = settings.get("others_folder", "Others")

    if (
        not isinstance(others, str)
        or not others.strip()
        or others in {".", ".."}
        or "/" in others
        or "\\" in others
    ):
        raise ValueError("Invalid others_folder setting.")

    for key in ("skip_hidden_files", "skip_system_files"):
        if key in settings and not isinstance(settings[key], bool):
            raise ValueError(f"{key} must be true or false.")

    return config

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

        return validate_config(config)
    except (ValueError, TypeError) as error:
        print(Fore.RED + f"Invalid configuration: {error}")
        logging.error(f"Invalid configuration: {error}")
        print(Fore.YELLOW + "Using default configuration.")
        return DEFAULT_CONFIG
    
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

#OLD LOGIC FOR GETTING FILES (COMMENTED OUT)
# def get_files(folder, recursive=False):
#     """Return files to organize."""

#     if recursive:

#         return [
#             item
#             for item in folder.rglob("*")
#             if item.is_file()
#         ]

#     return [
#         item
#         for item in folder.iterdir()
#         if item.is_file()
#     ]

# NEW LOGIC FOR GETTING FILES
def get_files(folder, recursive=False):
    """Return files to organize without scanning output folders."""

    if not recursive:
        return [
            item for item in folder.iterdir()
            if item.is_file()
        ]

    excluded_dirs = {
        "Images",
        "Documents",
        "Videos",
        "Music",
        "Archives",
        "Programs",
        "Others",
        "logs",
        "reports",
    }

    files = []

    for item in folder.rglob("*"):
        if not item.is_file():
            continue

        relative_parts = item.relative_to(folder).parts

        # Skip files inside existing output/system folders.
        if any(part in excluded_dirs for part in relative_parts[:-1]):
            continue

        files.append(item)

    return files

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

# OLD LOGIC FOR ORGANIZING FILES (COMMENTED OUT)
# def organize_file(file, category, root_folder, dry_run=False):
#     """Move a file into its category."""

#     destination = root_folder / category

#     destination.mkdir(
#         exist_ok=True
#     )

#     target = get_unique_destination(
#         destination,
#         file
#     )

#     if dry_run:

#         print(
#             Fore.CYAN
#             + f"[DRY RUN] {file.name}"
#         )

#         print(
#             f"          → {category}"
#         )

#         return True, target

#     try:

#         shutil.move(
#             str(file),
#             str(target)
#         )

#         print(
#             Fore.GREEN
#             + f"✓ {file.name}"
#         )

#         print(
#             f"  → {category}"
#         )

#         logging.info(
#             f"Moved: {file} -> {target}"
#         )

#         return True, target

#     except Exception as error:

#         print(
#             Fore.RED
#             + f"✗ Failed: {file.name}"
#         )

#         print(
#             f"  Reason: {error}"
#         )

#         logging.error(
#             f"Failed to move {file}: {error}"
#         )

#         return False, target 

# NEW LOGIC FOR ORGANIZING FILES
def organize_file(file, category, root_folder, dry_run=False):
    """Move a file into its category, or preview the move."""

    destination = root_folder / category

    if dry_run:
        # Don't create directories or move files.
        target = get_unique_destination(destination, file)

        print(Fore.CYAN + f"[DRY RUN] {file.name}")
        print(f"          → {category}")

        return True, target

    try:
        destination.mkdir(exist_ok=True)

        target = get_unique_destination(destination, file)

        shutil.move(str(file), str(target))

        print(Fore.GREEN + f"✓ {file.name}")
        print(f"  → {category}")

        logging.info(f"Moved: {file} -> {target}")

        return True, target

    except Exception as error:
        print(Fore.RED + f"✗ Failed: {file.name}")
        print(f"  Reason: {error}")

        logging.error(f"Failed to move {file}: {error}")

        return False, target if "target" in locals() else None
    
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



def main():
    
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

    failed = 0

    stats = {}

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

if __name__ == "__main__":
    main()