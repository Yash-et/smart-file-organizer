from email import message
import os
import csv
import subprocess
import sys
import operation_history
from pathlib import Path
from collections import Counter
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk
import organizer

'''APPLICATION CONFIGURATION'''
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

APP_TITLE = "Smart File Organizer"
APP_VERSION = "3.7"
WINDOW_SIZE = "1100x720"

def calculate_dashboard_statistics(records):
    """Calculate dashboard values from operation-history records.

    Success rate uses only records marked SUCCESS or FAILED. An empty history
    returns None for the rate rather than misleadingly reporting 100 percent.
    Category totals include successful file operations only.
    """
    records = list(records)
    normalized = [
        (record, str(record.get("status", "")).strip().upper())
        for record in records
    ]
    successful = [record for record, status in normalized if status == "SUCCESS"]
    failed = [record for record, status in normalized if status == "FAILED"]
    attempts = len(successful) + len(failed)
    category_counts = Counter(
        str(record.get("category") or "Uncategorized").strip() or "Uncategorized"
        for record in successful
    )
    return {
        "recorded_operations": len(records),
        "successful_files": len(successful),
        "failed_operations": len(failed),
        "success_rate": (len(successful) / attempts * 100) if attempts else None,
        "category_counts": category_counts,
        "recent_records": records[:8],
    }

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

        '''Each preview item stores: (source file, category, target path).'''
        self.preview_items = []
        self.preview_folder = None

        '''Background organization state. Only the GUI thread may update widgets.'''
        self.is_organizing = False
        self.cancel_requested = threading.Event()
        self.worker_queue = queue.Queue()

        # Dashboard window and widget references are created on demand.
        self.dashboard_window = None
        self.dashboard_stat_labels = {}
        self.dashboard_category_frame = None
        self.dashboard_activity_tree = None
        self.dashboard_empty_label = None

        self._configure_layout()
        self._build_sidebar()
        self._build_main_panel()

        '''Poll worker messages from the GUI thread.'''
        self.after(100, self._process_worker_events)

    '''LAYOUT'''

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
        self.main.grid_rowconfigure(6, weight=1)

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

        self.browse_button = ctk.CTkButton(
            folder_frame,
            text="Browse",
            width=100,
            command=self._browse_folder,
        )
        self.browse_button.grid(
            row=1, column=1, padx=(0, 14), pady=(0, 12)
        )

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

        self.cancel_button = ctk.CTkButton(
            action_frame,
            text="Cancel",
            width=90,
            fg_color="#9b2c2c",
            hover_color="#7f1d1d",
            state="disabled",
            command=self._cancel_organization,
        )
        self.cancel_button.pack(side="left", padx=(10, 0))
        
        self.history_button = ctk.CTkButton(
            action_frame,
            text="Open History",
            width=110,
            command=self._open_history_file,
        )
        self.history_button.pack(side="left", padx=(10, 0))

        self.view_history_button = ctk.CTkButton(
            action_frame,
            text="View History",
            width=110,
            command=self._view_history,
        )
        self.view_history_button.pack(side="left", padx=(10, 0))
        
        progress_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        progress_frame.grid(
            row=4, column=0, sticky="ew", padx=28, pady=(0, 10)
        )
        progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="Ready",
            anchor="w",
            text_color="gray",
        )
        self.progress_label.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.grid(row=1, column=0, sticky="ew")
        self.progress_bar.set(0)

        self.summary_label = ctk.CTkLabel(
            self.main,
            text="No preview generated",
            anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.summary_label.grid(
            row=5, column=0, sticky="ew", padx=28, pady=(0, 8)
        )

        '''Scrollable preview table.'''
        table_frame = ctk.CTkFrame(self.main)
        table_frame.grid(
            row=6, column=0, sticky="nsew", padx=28, pady=(0, 12)
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
        ).grid(row=7, column=0, sticky="ew", padx=28, pady=(0, 18))
    
    def _open_history_file(self):
        """Open the saved operation history using the default application."""
        try:
            history_path = operation_history.ensure_history_file()

            if os.name == "nt":
                os.startfile(str(history_path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(history_path)])
            else:
                subprocess.Popen(["xdg-open", str(history_path)])

        except Exception as error:
            messagebox.showerror(
                "Could not open history",
                f"Unable to open the operation history:\n{error}",
            )
    def _view_history(self):
        """Open an in-app viewer for saved file operations."""
        window = ctk.CTkToplevel(self)
        window.title("Operation History")
        window.geometry("1050x560")
        window.minsize(780, 420)
        window.transient(self)

        window.grid_columnconfigure(0, weight=1)
        window.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            window,
            text="Operation History",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 10))

        filter_frame = ctk.CTkFrame(window, fg_color="transparent")
        filter_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        filter_frame.grid_columnconfigure(0, weight=1)

        search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            filter_frame,
            textvariable=search_var,
            placeholder_text="Search filename, folder, destination, or category...",
        )
        search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        status_var = tk.StringVar(value="All")
        status_filter = ctk.CTkOptionMenu(
            filter_frame,
            variable=status_var,
            values=["All", "SUCCESS", "FAILED"],
            width=130,
        )
        status_filter.grid(row=0, column=1, padx=(0, 10))

        refresh_button = ctk.CTkButton(
            filter_frame,
            text="Refresh",
            width=90,
            command=lambda: self._refresh_history_table(
                tree, count_label, search_var.get(), status_var.get()
            ),
        )
        refresh_button.grid(row=0, column=2, padx=(0, 10))

        open_csv_button = ctk.CTkButton(
            filter_frame,
            text="Open CSV",
            width=90,
            command=self._open_history_file,
        )
        open_csv_button.grid(row=0, column=3)

        table_frame = ctk.CTkFrame(window)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 10))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = ("timestamp", "filename", "category", "status", "destination", "error")
        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Preview.Treeview",
        )
        headings = {
            "timestamp": ("Timestamp", 155),
            "filename": ("File name", 160),
            "category": ("Category", 100),
            "status": ("Status", 85),
            "destination": ("Destination", 250),
            "error": ("Error", 180),
        }
        for column, (heading, width) in headings.items():
            tree.heading(column, text=heading)
            tree.column(column, width=width, minwidth=70, anchor="w")

        scrollbar_y = ttk.Scrollbar(
            table_frame, orient="vertical", command=tree.yview
        )
        scrollbar_x = ttk.Scrollbar(
            table_frame, orient="horizontal", command=tree.xview
        )
        tree.configure(
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
        )
        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        count_label = ctk.CTkLabel(window, text="Loading history...", anchor="w")
        count_label.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 14))

        search_var.trace_add(
            "write",
            lambda *_: self._refresh_history_table(
                tree, count_label, search_var.get(), status_var.get()
            ),
        )
        status_var.trace_add(
            "write",
            lambda *_: self._refresh_history_table(
                tree, count_label, search_var.get(), status_var.get()
            ),
        )

        self._refresh_history_table(tree, count_label, "", "All")
        search_entry.focus_set()
        export_button = ctk.CTkButton(
                    filter_frame,
                    text="Export Filtered History",
                    width=170,
                    command=lambda: self._export_filtered_history(
                        search_var.get(),
                        status_var.get(),
                    ),
                )
        export_button.grid(row=0, column=4, padx=(10, 0))

    def _refresh_history_table(self, tree, count_label, search_text="", status="All"):
        """Reload and filter operation history in the viewer."""
        try:
            records = operation_history.read_operations()
        except Exception as error:
            messagebox.showerror(
                "History could not be loaded",
                f"Unable to read operation history:\n{error}",
            )
            return

        query = search_text.strip().casefold()
        for item in tree.get_children():
            tree.delete(item)

        shown = 0
        for record in records:
            record_status = record.get("status", "").upper()
            if status != "All" and record_status != status:
                continue

            searchable_text = " ".join(
                str(record.get(field, ""))
                for field in (
                    "timestamp",
                    "source_folder",
                    "source_file",
                    "destination",
                    "category",
                    "status",
                    "error",
                )
            ).casefold()
            if query and query not in searchable_text:
                continue

            tree.insert(
                "",
                "end",
                values=(
                    record.get("timestamp", ""),
                    Path(record.get("source_file", "")).name,
                    record.get("category", ""),
                    record.get("status", ""),
                    record.get("destination", ""),
                    record.get("error", ""),
                ),
            )
            shown += 1

        count_label.configure(
            text=f"Showing {shown} of {len(records)} operation record(s)."
        )

    '''EXPORT FILTERED HISTORY'''
    
    def _export_filtered_history(self, search_text="", status="All"):
        """Export only the records matching the active history filters."""
        try:
            records = operation_history.read_operations()
        except Exception as error:
            messagebox.showerror(
                "History could not be loaded",
                f"Unable to read operation history:\n{error}",
                parent=self,
            )
            return

        query = search_text.strip().casefold()
        filtered_records = []

        searchable_fields = (
            "timestamp",
            "source_folder",
            "source_file",
            "destination",
            "category",
            "status",
            "error",
        )

        for record in records:
            record_status = record.get("status", "").upper()

            if status != "All" and record_status != status:
                continue

            searchable_text = " ".join(
                str(record.get(field, ""))
                for field in searchable_fields
            ).casefold()

            if query and query not in searchable_text:
                continue

            filtered_records.append(record)

        if not filtered_records:
            messagebox.showinfo(
                "Nothing to export",
                "No history records match the current search and status filters.",
                parent=self,
            )
            return

        output_path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Filtered History",
            defaultextension=".csv",
            initialfile="filtered_operation_history.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )

        if not output_path:
            return

        try:
            fieldnames = operation_history.FIELDNAMES

            with open(
                output_path,
                "w",
                newline="",
                encoding="utf-8-sig",
            ) as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=fieldnames,
                    extrasaction="ignore",
                )
                writer.writeheader()
                writer.writerows(filtered_records)

        except (OSError, csv.Error) as error:
            messagebox.showerror(
                "Export failed",
                f"Could not export the filtered history:\n{error}",
                parent=self,
            )
            return

        messagebox.showinfo(
            "Export successful",
            f"Exported {len(filtered_records)} record(s) to:\n{output_path}",
            parent=self,
        )

    '''FOLDER AND CONFIGURATION'''

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
        '''Do not call load_config() when the file is absent because the
        CLI implementation may create config.json as a side effect.'''
        
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

            '''Avoid existing files and collisions with other preview items.'''
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

    '''PREVIEW'''

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

    '''ACTUAL ORGANIZATION'''

    def _organize_files(self):
        if self.is_organizing:
            return

        folder = self._get_selected_folder()
        if folder is None:
            return

        '''Require a preview for the currently selected folder.'''
        if not self.preview_items or self.preview_folder != folder:
            messagebox.showwarning(
                "Preview required",
                "Generate a preview for this folder before organizing.",
            )
            return

        '''Refresh the preview immediately before confirmation.'''
        try:
            config = self._load_config_safely()
            items, _ = self._collect_preview_items(folder, config)
            self.preview_items = items
            self.preview_folder = folder
            self._refresh_preview_table(items)
        except Exception as error:
            messagebox.showerror(
                "Preparation failed",
                f"Could not refresh the preview:\\n{error}",
            )
            return

        if not items:
            self.organize_button.configure(state="disabled")
            self.summary_label.configure(text="No eligible files found")
            self.status_text.set("Nothing to organize.")
            self.progress_label.configure(text="No eligible files found.")
            self.progress_bar.set(0)
            return

        confirmed = messagebox.askyesno(
            "Confirm file organization",
            f"Organize {len(items)} file(s) in this folder?\\n\\n"
            f"{folder}\\n\\n"
            "Files will be moved into category subfolders. "
            "Existing files will not be intentionally overwritten.\\n\\n"
            "Cancellation takes effect between file operations. "
            "Files already moved will not be automatically restored.",
            icon="warning",
        )

        if not confirmed:
            self.status_text.set(
                "Organization cancelled. No files were moved."
            )
            return

        self.is_organizing = True
        self.cancel_requested.clear()
        self.progress_bar.set(0)
        self.progress_label.configure(
            text=f"Preparing to organize {len(items)} file(s)..."
        )
        self.status_text.set("Organization in progress...")

        '''Disable controls that could invalidate the current operation.'''
        self.organize_button.configure(state="disabled")
        self.preview_button.configure(state="disabled")
        self.clear_button.configure(state="disabled")
        self.browse_button.configure(state="disabled")
        self.folder_entry.configure(state="disabled")
        self.cancel_button.configure(state="normal")

        worker = threading.Thread(
            target=self._organization_worker,
            args=(items, folder),
            daemon=True,
        )
        worker.start()
    
    def _organization_worker(self, items, folder):
        """Move files and record each attempted operation."""
        total = len(items)
        moved = 0
        failed = 0
        processed = 0
        failures = []
        history_errors = []

        for index, (file, category, planned_target) in enumerate(
            items, start=1
        ):
            if self.cancel_requested.is_set():
                break

            self.worker_queue.put(
                ("current", index, total, file.name)
            )

            # Start with the preview destination as a fallback.
            target = planned_target
            status = "FAILED"
            error_message = ""

            try:
                success, target = organizer.organize_file(
                    file,
                    category,
                    folder,
                    dry_run=False,
                )

                if success:
                    moved += 1
                    status = "SUCCESS"
                else:
                    failed += 1
                    error_message = "Organizer reported failure"
                    failures.append(
                        (file.name, error_message)
                    )

            except Exception as error:
                failed += 1
                error_message = str(error)
                failures.append((file.name, error_message))

            # History failures must not change the move result.
            try:
                operation_history.record_operation(
                    source_folder=folder,
                    source_file=file,
                    destination=target,
                    category=category,
                    status=status,
                    error=error_message,
                )
            except Exception as history_error:
                message = (
                    f"{file.name}: "
                    f"{type(history_error).__name__}: {history_error}"
                )
                history_errors.append(message)
                print(f"[HISTORY LOG ERROR] {message}")

            processed += 1

            self.worker_queue.put(
                ("progress", processed, total, file.name)
            )

        result = {
            "moved": moved,
            "failed": failed,
            "failures": failures,
            "processed": processed,
            "total": total,
            "cancelled": (
                self.cancel_requested.is_set()
                and processed < total
            ),
            "history_errors": history_errors,
        }

        self.worker_queue.put(("finished", result))

    def _cancel_organization(self):
        if not self.is_organizing:
            return

        self.cancel_requested.set()
        self.cancel_button.configure(state="disabled")
        self.status_text.set(
            "Cancellation requested. Finishing the current file operation..."
        )
        self.progress_label.configure(text="Cancellation requested...")

    def _process_worker_events(self):
        """Handle worker messages on the GUI's main thread."""
        try:
            while True:
                event = self.worker_queue.get_nowait()
                event_type = event[0]

                if event_type == "current":
                    _, index, total, filename = event
                    self.progress_label.configure(
                        text=f"Processing {index} of {total}: {filename}"
                    )

                elif event_type == "progress":
                    _, processed, total, filename = event
                    self.progress_bar.set(
                        processed / total if total else 0
                    )
                    self.progress_label.configure(
                        text=(
                            f"{processed} of {total} processed — "
                            f"{filename}"
                        )
                    )

                elif event_type == "finished":
                    self._finish_organization(event[1])

        except queue.Empty:
            pass
        except tk.TclError:
            return

        try:
            self.after(100, self._process_worker_events)
        except tk.TclError:
            pass

    def _finish_organization(self, result):
        """Restore the interface and summarize the completed operation."""
        self.is_organizing = False

        moved = result["moved"]
        failed = result["failed"]
        failures = result["failures"]
        processed = result["processed"]
        history_errors = result.get("history_errors", [])
        total = result["total"]
        remaining = total - processed
        cancelled = result["cancelled"]

        self.preview_button.configure(state="normal")
        self.clear_button.configure(state="normal")
        self.browse_button.configure(state="normal")
        self.folder_entry.configure(state="normal")
        self.cancel_button.configure(state="disabled")

        '''Rescan the source folder so the preview shows what remains.'''
        self._preview_organization()

        if total:
            self.progress_bar.set(processed / total)

        if cancelled:
            self.progress_label.configure(
                text=f"Cancelled after processing {processed} of {total} files."
            )
            self.status_text.set(
                "Operation cancelled. Files already moved remain in their destinations."
            )
        elif failed:
            self.progress_label.configure(
                text=f"Finished with {failed} failure(s)."
            )
            self.status_text.set(
                "Organization finished with errors. Review the summary."
            )
        else:
            self.progress_label.configure(
                text=f"Completed: {processed} of {total} files processed."
            )
            self.status_text.set("Organization complete.")

        summary = (
            f"Moved: {moved}  |  Failed: {failed}  |  "
            f"Not processed: {remaining}"
        )
        if cancelled:
            summary = "Cancelled  |  " + summary
        self.summary_label.configure(text=summary)

        if failures:
            details = "\\n".join(
                f"• {name}: {reason}" for name, reason in failures[:10]
            )
            if len(failures) > 10:
                details += f"\\n...and {len(failures) - 10} more failure(s)."
            if history_errors:
                details += (
                    "\n\nHistory logging warnings: "
                    f"{len(history_errors)} record(s) could not be saved."
                )
            messagebox.showwarning(
                "Organization finished with errors",
                f"Moved: {moved}\\n"
                f"Failed: {failed}\\n"
                f"Not processed: {remaining}\\n\\n"
                f"{details}",
            )
        elif cancelled:
            history_notice = ""
            if history_errors:
                history_notice = (
                    "\n\nHistory logging warning: "
                    f"{len(history_errors)} record(s) could not be saved."
                )
            messagebox.showinfo(
                "Organization cancelled",
                f"Moved: {moved}\\n"
                f"Failed: {failed}\\n"
                f"Not processed: {remaining}\\n\\n"
                "Files already moved were not automatically restored.",
            )
        else:
            history_notice = ""
            if history_errors:
                history_notice = (
                    "\n\nHistory logging warning: "
                    f"{len(history_errors)} record(s) could not be saved."
                )

            messagebox.showinfo(
                "Organization complete",
                f"Successfully organized {moved} file(s).\n\n"
                f"Location:\n{self.preview_folder}"
                f"{history_notice}",
            )

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

    '''CLEAR / NAVIGATION'''

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


    # DASHBOARD

    def _open_dashboard(self):
        """Open the organization statistics dashboard, reusing it if open."""
        if self.dashboard_window is not None:
            try:
                if self.dashboard_window.winfo_exists():
                    self.dashboard_window.lift()
                    self._refresh_dashboard()
                    return
            except tk.TclError:
                self.dashboard_window = None

        window = ctk.CTkToplevel(self)
        self.dashboard_window = window
        window.title(f"{APP_TITLE} — Statistics Dashboard")
        window.geometry("1000x720")
        window.minsize(820, 580)
        window.transient(self)
        window.protocol("WM_DELETE_WINDOW", self._close_dashboard)
        window.grid_columnconfigure(0, weight=1)
        window.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(window, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=22, pady=(20, 12))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Organization Dashboard",
            font=ctk.CTkFont(size=25, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text="Statistics are calculated from your saved operation history.",
            text_color="gray",
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))
        ctk.CTkButton(
            header,
            text="Refresh",
            width=100,
            command=self._refresh_dashboard,
        ).grid(row=0, column=1, rowspan=2, padx=(12, 0))

        stats_frame = ctk.CTkFrame(window, fg_color="transparent")
        stats_frame.grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 14))
        for column in range(4):
            stats_frame.grid_columnconfigure(column, weight=1, uniform="stat")

        stat_definitions = [
            ("successful", "Files Organized"),
            ("failed", "Failed Operations"),
            ("operations", "Recorded Operations"),
            ("rate", "Success Rate"),
        ]
        self.dashboard_stat_labels = {}
        for column, (key, title) in enumerate(stat_definitions):
            card = ctk.CTkFrame(stats_frame, corner_radius=12)
            card.grid(row=0, column=column, sticky="ew", padx=5, pady=2)
            ctk.CTkLabel(
                card,
                text=title,
                text_color="gray",
                font=ctk.CTkFont(size=12),
            ).pack(anchor="w", padx=14, pady=(13, 4))
            value_label = ctk.CTkLabel(
                card,
                text="—",
                font=ctk.CTkFont(size=25, weight="bold"),
            )
            value_label.pack(anchor="w", padx=14, pady=(0, 13))
            self.dashboard_stat_labels[key] = value_label

        content = ctk.CTkFrame(window, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew", padx=22, pady=(0, 12))
        content.grid_columnconfigure(0, weight=1, uniform="content")
        content.grid_columnconfigure(1, weight=2, uniform="content")
        content.grid_rowconfigure(0, weight=1)

        category_panel = ctk.CTkFrame(content)
        category_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        category_panel.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            category_panel,
            text="Files by Category",
            font=ctk.CTkFont(size=17, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(14, 8))
        self.dashboard_category_frame = ctk.CTkScrollableFrame(
            category_panel,
            height=300,
            fg_color="transparent",
        )
        self.dashboard_category_frame.grid(
            row=1, column=0, sticky="nsew", padx=8, pady=(0, 10)
        )
        category_panel.grid_rowconfigure(1, weight=1)

        activity_panel = ctk.CTkFrame(content)
        activity_panel.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        activity_panel.grid_columnconfigure(0, weight=1)
        activity_panel.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(
            activity_panel,
            text="Recent Activity",
            font=ctk.CTkFont(size=17, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(14, 8))

        tree_frame = ctk.CTkFrame(activity_panel, fg_color="transparent")
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)
        columns = ("timestamp", "filename", "category", "status")
        self.dashboard_activity_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            style="Preview.Treeview",
            height=10,
        )
        for column, heading, width in (
            ("timestamp", "Timestamp", 145),
            ("filename", "File", 170),
            ("category", "Category", 100),
            ("status", "Status", 80),
        ):
            self.dashboard_activity_tree.heading(column, text=heading)
            self.dashboard_activity_tree.column(column, width=width, minwidth=65, anchor="w")
        activity_scrollbar = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self.dashboard_activity_tree.yview,
        )
        self.dashboard_activity_tree.configure(yscrollcommand=activity_scrollbar.set)
        self.dashboard_activity_tree.grid(row=0, column=0, sticky="nsew")
        activity_scrollbar.grid(row=0, column=1, sticky="ns")

        self.dashboard_empty_label = ctk.CTkLabel(
            window,
            text="",
            text_color="gray",
            anchor="w",
        )
        self.dashboard_empty_label.grid(
            row=3, column=0, sticky="ew", padx=24, pady=(0, 14)
        )
        self._refresh_dashboard()

    def _close_dashboard(self):
        """Close the dashboard and clear its widget references."""
        if self.dashboard_window is not None:
            try:
                self.dashboard_window.destroy()
            except tk.TclError:
                pass
        self.dashboard_window = None
        self.dashboard_stat_labels = {}
        self.dashboard_category_frame = None
        self.dashboard_activity_tree = None
        self.dashboard_empty_label = None

    def _refresh_dashboard(self):
        """Refresh dashboard metrics from the persistent CSV history."""
        if self.dashboard_window is None:
            return
        try:
            if not self.dashboard_window.winfo_exists():
                return
            records = operation_history.read_operations()
        except (OSError, csv.Error, tk.TclError) as error:
            messagebox.showerror(
                "Dashboard could not be refreshed",
                f"Unable to read operation history:\n{error}",
                parent=self.dashboard_window,
            )
            return
        except Exception as error:
            messagebox.showerror(
                "Dashboard could not be refreshed",
                f"Unable to load dashboard statistics:\n{error}",
                parent=self.dashboard_window,
            )
            return

        stats = calculate_dashboard_statistics(records)
        self.dashboard_stat_labels["successful"].configure(
            text=str(stats["successful_files"])
        )
        self.dashboard_stat_labels["failed"].configure(
            text=str(stats["failed_operations"])
        )
        self.dashboard_stat_labels["operations"].configure(
            text=str(stats["recorded_operations"])
        )
        rate = stats["success_rate"]
        self.dashboard_stat_labels["rate"].configure(
            text=f"{rate:.1f}%" if rate is not None else "N/A"
        )

        for child in self.dashboard_category_frame.winfo_children():
            child.destroy()
        category_counts = stats["category_counts"]
        if category_counts:
            max_count = max(category_counts.values())
            for row, (category, count) in enumerate(
                sorted(category_counts.items(), key=lambda item: (-item[1], item[0].casefold()))
            ):
                item_frame = ctk.CTkFrame(
                    self.dashboard_category_frame,
                    fg_color="transparent",
                )
                item_frame.grid(row=row, column=0, sticky="ew", padx=4, pady=5)
                item_frame.grid_columnconfigure(0, weight=1)
                ctk.CTkLabel(
                    item_frame,
                    text=category,
                    anchor="w",
                ).grid(row=0, column=0, sticky="ew")
                ctk.CTkLabel(
                    item_frame,
                    text=str(count),
                    font=ctk.CTkFont(weight="bold"),
                ).grid(row=0, column=1, sticky="e", padx=(8, 0))
                bar = ctk.CTkProgressBar(item_frame, height=8)
                bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))
                bar.set(count / max_count if max_count else 0)
        else:
            ctk.CTkLabel(
                self.dashboard_category_frame,
                text="No successful file operations yet.",
                text_color="gray",
                wraplength=230,
            ).grid(row=0, column=0, sticky="w", padx=5, pady=8)

        tree = self.dashboard_activity_tree
        for item in tree.get_children():
            tree.delete(item)
        for record in stats["recent_records"]:
            timestamp = str(record.get("timestamp", "")).replace("T", " ")[:19]
            tree.insert(
                "",
                "end",
                values=(
                    timestamp,
                    Path(record.get("source_file", "")).name,
                    record.get("category", ""),
                    str(record.get("status", "")).upper(),
                ),
            )

        if stats["recorded_operations"] == 0:
            self.dashboard_empty_label.configure(
                text="No operation history has been recorded yet. Success rate is N/A until an operation is recorded."
            )
        else:
            self.dashboard_empty_label.configure(
                text=(
                    f"Showing {len(stats['recent_records'])} recent record(s). "
                    "Category counts include successful operations only."
                )
            )

    def _show_section(self, section):
        if section == "Organize Files":
            self.status_text.set(
                "Select a folder, preview it, then confirm to organize."
            )
        elif section == "Dashboard":
            self._open_dashboard()
        elif section == "Settings":
            self.status_text.set(
                "Settings currently use the project's config.json defaults."
            )

if __name__ == "__main__":
    app = SmartFileOrganizerApp()
    app.mainloop()
