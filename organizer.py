from pathlib import Path
import shutil

# ==============================
# Smart File Organizer v1
# ==============================

DOWNLOADS = Path.home() / "Downloads"

FILE_TYPES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".ppt", ".pptx", ".xls", ".xlsx"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov"],
    "Music": [".mp3", ".wav", ".flac"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Programs": [".exe", ".msi"],
}

print("=" * 50)
print(" SMART FILE ORGANIZER v1 ")
print("=" * 50)

if not DOWNLOADS.exists():
    print("Downloads folder not found.")
    raise SystemExit

moved = 0

for item in DOWNLOADS.iterdir():

    if item.is_dir():
        continue

    extension = item.suffix.lower()

    destination = None

    for folder, extensions in FILE_TYPES.items():
        if extension in extensions:
            destination = DOWNLOADS / folder
            break

    if destination is None:
        destination = DOWNLOADS / "Others"

    destination.mkdir(exist_ok=True)

    shutil.move(str(item), str(destination / item.name))

    print(f"Moved: {item.name} -> {destination.name}")

    moved += 1

print("-" * 50)
print(f"Finished! {moved} file(s) organized.")