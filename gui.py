from pathlib import Path
from collections import Counter
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk
import organizer


# --------------------------------------------------
# APPLICATION CONFIGURATION
# --------------------------------------------------

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

APP_TITLE = "Smart File Organizer"
APP_VERSION = "3.1"
WINDOW_SIZE = "1100x720"


class SmartFileOrganizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_TITLE} v{APP_VERSION}")
        self.geometry(WINDOW_SIZE)
        self.minsize(900, 600)

        self.selected_folder = tk.StringVar()
        self.status_text = tk.StringVar(
            value="Select a folder to preview its organization."
        )

        # Each preview item stores: (source file, category, target path).
        self.preview_items = []
        self.preview_folder = None

        self._configure_layout()
        self._build_sidebar()
        self._build_main_panel()

    # --------------------------------------------------
    # LAYOUT
    # --------------------------------------------------

    def _configure_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self,
            width=210,
            corner_radius=0,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(
            self.sidebar,
            text="FILE ORGANIZER",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(padx=18, pady=(28, 6), anchor="w")

        ctk.CTkLabel(
            self.sidebar,
            text=f"Version {APP_VERSION} · GUI",
            text_color="gray",
        ).pack(padx=18, pady=(0, 28), anchor="w")

        for label in ("Dashboard", "Organize Files", "Settings"):
            ctk.CTkButton(
                self.sidebar,
                text=label,
                anchor="w",
                fg_color="transparent",
                hover_color=("#d9e7f5", "#26364a"),
                text_color=("gray10", "gray90"),
                command=lambda name=label: self._show_section(name),
            ).pack(fill="x", padx=12, pady=5)

        ctk.CTkLabel(
            self.sidebar,
            text="Preview before moving",
            text_color="#67d5a5",
        ).pack(side="bottom", padx=18, pady=24, anchor="w")

    def _build_main_panel(self):
        self.main = ctk.CTkFrame(self, corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew")

        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(
            self.main,
            text="Organize your files",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=28, pady=(26, 4))

        ctk.CTkLabel(
            self.main,
            text="Inspect destinations, then confirm before moving files.",
            text_color="gray",
        ).grid(row=1, column=0, sticky="w", padx=28, pady=(0, 18))

        folder_frame = ctk.CTkFrame(self.main)
        folder_frame.grid(
            row=2, column=0, sticky="ew", padx=28, pady=(0, 14)
        )
        folder_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            folder_frame,
            text="Source folder",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))

        self.folder_entry = ctk.CTkEntry(
            folder_frame,
            textvariable=self.selected_folder,
            placeholder_text="Choose a folder to scan...",
        )
        self.folder_entry.grid(
            row=1, column=0, sticky="ew", padx=14, pady=(0, 12)
        )

        ctk.CTkButton(
            folder_frame,
            text="Browse",
            width=100,
            command=self._browse_folder,
        ).grid(row=1, column=1, padx=(0, 14), pady=(0, 12))

        action_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        action_frame.grid(
            row=3, column=0, sticky="ew", padx=28, pady=(0, 12)
        )

        self.preview_button = ctk.CTkButton(
            action_frame,
            text="Preview Organization",
            command=self._preview_organization,
        )
        self.preview_button.pack(side="left")

        self.organize_button = ctk.CTkButton(
            action_frame,
            text="Organize Files",
            fg_color="#16845b",
            hover_color="#116b49",
            state="disabled",
            command=self._organize_files,
        )
        self.organize_button.pack(side="left", padx=(10, 0))

        self.clear_button = ctk.CTkButton(
            action_frame,
            text="Clear Preview",
            fg_color="transparent",
            border_width=1,
            command=self._clear_preview,
        )
        self.clear_button.pack(side="left", padx=(10, 0))

        self.summary_label = ctk.CTkLabel(
            self.main,
            text="No preview generated",
            anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.summary_label.grid(
            row=4, column=0, sticky="ew", padx=28, pady=(0, 8)
        )

        # Scrollable preview table.
        table_frame = ctk.CTkFrame(self.main)
        table_frame.grid(
            row=5, column=0, sticky="nsew", padx=28, pady=(0, 12)
        )
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Preview.Treeview",
            background="#20252e",
            foreground="#f1f5f9",
            fieldbackground="#20252e",
            rowheight=28,
            borderwidth=0,
        )
        style.configure(
            "Preview.Treeview.Heading",
            background="#303846",
            foreground="#ffffff",
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Preview.Treeview",
            background=[("selected", "#245b8f")],
        )

        columns = ("filename", "extension", "category", "destination")

        self.preview_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Preview.Treeview",
        )

        self.preview_table.heading("filename", text="File name")
        self.preview_table.heading("extension", text="Extension")
        self.preview_table.heading("category", text="Category")
        self.preview_table.heading(
            "destination", text="Proposed destination"
        )

        self.preview_table.column("filename", width=230, minwidth=120)
        self.preview_table.column("extension", width=90, minwidth=70)
        self.preview_table.column("category", width=130, minwidth=100)
        self.preview_table.column("destination", width=340, minwidth=180)

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.preview_table.yview,
        )
        self.preview_table.configure(yscrollcommand=scrollbar.set)

        self.preview_table.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        ctk.CTkLabel(
            self.main,
            textvariable=self.status_text,
            anchor="w",
            text_color="gray",
        ).grid(row=6, column=0, sticky="ew", padx=28, pady=(0, 18))

    # --------------------------------------------------
    # FOLDER AND CONFIGURATION
    # --------------------------------------------------

    def _browse_folder(self):
        folder = filedialog.askdirectory(
            title="Select a folder to organize"
        )

        if folder:
            self.selected_folder.set(folder)
            self._invalidate_preview()
            self.status_text.set(
                "Folder selected. Generate a new preview before organizing."
            )

    def _get_selected_folder(self):
        raw_folder = self.selected_folder.get().strip()

        if not raw_folder:
            messagebox.showwarning(
                "Folder required",
                "Please select a folder first.",
            )
            return None

        folder = Path(raw_folder).expanduser()

        if not folder.exists() or not folder.is_dir():
            messagebox.showerror(
                "Invalid folder",
                "The selected path does not exist or is not a directory.",
            )
            return None

        return folder.resolve()

    def _load_config_safely(self):
        # Do not call load_config() when the file is absent because the
        # CLI implementation may create config.json as a side effect.
        config_path = Path(organizer.CONFIG_FILE)

        if config_path.exists():
            return organizer.load_config()

        return organizer.DEFAULT_CONFIG

    def _collect_preview_items(self, folder, config):
        files = organizer.get_files(folder, recursive=False)
        files = [
            file for file in files
            if not organizer.is_ignored(file, config)
        ]

        items = []
        category_counts = Counter()
        planned_destinations = set()

        for file in sorted(files, key=lambda item: item.name.lower()):
            category = organizer.get_category(file.suffix, config)
            destination = folder / category
            target = destination / file.name

            # Avoid existing files and collisions with other preview items.
            counter = 1
            while (
                target.exists()
                or str(target).casefold() in planned_destinations
            ):
                target = destination / (
                    f"{file.stem}_{counter}{file.suffix}"
                )
                counter += 1

            planned_destinations.add(str(target).casefold())
            items.append((file, category, target))
            category_counts[category] += 1

        return items, category_counts

    # --------------------------------------------------
    # PREVIEW
    # --------------------------------------------------

    def _preview_organization(self):
        folder = self._get_selected_folder()

        if folder is None:
            return

        try:
            config = self._load_config_safely()
            items, category_counts = self._collect_preview_items(
                folder, config
            )

            self._clear_table_only()
            self.preview_items = items
            self.preview_folder = folder

            for file, category, target in items:
                self.preview_table.insert(
                    "",
                    "end",
                    values=(
                        file.name,
                        file.suffix.lower() or "(none)",
                        category,
                        str(target),
                    ),
                )

            if not items:
                self.summary_label.configure(
                    text="No eligible files found"
                )
                self.status_text.set(
                    "Scan complete. No eligible files were found."
                )
            else:
                summary = "  |  ".join(
                    f"{category}: {count}"
                    for category, count in sorted(
                        category_counts.items()
                    )
                )
                self.summary_label.configure(
                    text=f"{len(items)} file(s) found  |  {summary}"
                )
                self.status_text.set(
                    "Preview ready. No files have been moved."
                )

            self.organize_button.configure(
                state="normal" if items else "disabled"
            )

        except Exception as error:
            self._invalidate_preview()
            self.status_text.set("Preview failed.")
            messagebox.showerror(
                "Preview error",
                f"Could not generate the preview:\n{error}",
            )

    # --------------------------------------------------
    # ACTUAL ORGANIZATION
    # --------------------------------------------------

    def _organize_files(self):
        folder = self._get_selected_folder()

        if folder is None:
            return

        # Require a preview for the currently selected folder.
        if not self.preview_items or self.preview_folder != folder:
            messagebox.showwarning(
                "Preview required",
                "Generate a preview for this folder before organizing.",
            )
            return

        # Refresh the preview immediately before confirmation. This helps
        # account for files or destination conflicts changed since scanning.
        try:
            config = self._load_config_safely()
            items, _ = self._collect_preview_items(folder, config)

            self.preview_items = items
            self.preview_folder = folder
            self._refresh_preview_table(items)

        except Exception as error:
            messagebox.showerror(
                "Preparation failed",
                f"Could not refresh the preview:\n{error}",
            )
            return

        if not items:
            self.organize_button.configure(state="disabled")
            self.summary_label.configure(text="No eligible files found")
            self.status_text.set("Nothing to organize.")
            return

        confirmed = messagebox.askyesno(
            "Confirm file organization",
            f"Organize {len(items)} file(s) in this folder?\n\n"
            f"{folder}\n\n"
            "Files will be moved into category subfolders. "
            "Existing files will not be intentionally overwritten.\n\n"
            "This action moves files and is not automatically reversible.",
            icon="warning",
        )

        if not confirmed:
            self.status_text.set(
                "Organization cancelled. No files were moved."
            )
            return

        self.organize_button.configure(state="disabled")
        self.preview_button.configure(state="disabled")
        self.status_text.set("Organizing files...")

        moved = 0
        failed = 0
        failures = []

        try:
            for file, category, _planned_target in items:
                # The engine selects a unique destination again at move time.
                success, target = organizer.organize_file(
                    file,
                    category,
                    folder,
                    dry_run=False,
                )

                if success:
                    moved += 1
                else:
                    failed += 1
                    failures.append(file.name)

            # Rescan so the table reflects files remaining in the root.
            self._preview_organization()

            self.summary_label.configure(
                text=f"Organization complete  |  Moved: {moved}  |  Failed: {failed}"
            )

            if failed:
                self.status_text.set(
                    f"Finished with {failed} failure(s). "
                    "See the error summary for details."
                )
                messagebox.showwarning(
                    "Organization finished with errors",
                    f"Successfully moved: {moved}\n"
                    f"Failed: {failed}\n\n"
                    f"Files that failed:\n"
                    + "\n".join(failures[:15])
                    + (
                        "\n..." if len(failures) > 15 else ""
                    ),
                )
            else:
                self.status_text.set(
                    f"Organization complete. {moved} file(s) moved."
                )
                messagebox.showinfo(
                    "Organization complete",
                    f"Successfully organized {moved} file(s).\n\n"
                    f"Location:\n{folder}",
                )

        except Exception as error:
            messagebox.showerror(
                "Organization error",
                f"An unexpected error occurred:\n{error}\n\n"
                "Some files may already have been moved. "
                "Generate a new preview to inspect the folder.",
            )
            self.status_text.set(
                "Organization stopped unexpectedly. Please rescan."
            )

        finally:
            self.preview_button.configure(state="normal")

    def _refresh_preview_table(self, items):
        self._clear_table_only()

        for file, category, target in items:
            self.preview_table.insert(
                "",
                "end",
                values=(
                    file.name,
                    file.suffix.lower() or "(none)",
                    category,
                    str(target),
                ),
            )

        self.organize_button.configure(
            state="normal" if items else "disabled"
        )

    # --------------------------------------------------
    # CLEAR / NAVIGATION
    # --------------------------------------------------

    def _clear_table_only(self):
        for item in self.preview_table.get_children():
            self.preview_table.delete(item)

    def _invalidate_preview(self):
        self.preview_items = []
        self.preview_folder = None
        self.organize_button.configure(state="disabled")
        self._clear_table_only()
        self.summary_label.configure(text="No preview generated")

    def _clear_preview(self):
        self._invalidate_preview()
        self.status_text.set("Preview cleared. No files were changed.")

    def _show_section(self, section):
        if section == "Organize Files":
            self.status_text.set(
                "Select a folder, preview it, then confirm to organize."
            )
        elif section == "Dashboard":
            self.status_text.set(
                "Preview files safely before organizing."
            )
        elif section == "Settings":
            self.status_text.set(
                "Settings currently use the project's config.json defaults."
            )


if __name__ == "__main__":
    app = SmartFileOrganizerApp()
    app.mainloop()