from pathlib import Path
import shutil
import time

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


def main():

    folder = get_folder()

    start = time.time()

    total = 0

    skipped = 0

    failed = 0

    stats = {}

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


if __name__ == "__main__":
    main()