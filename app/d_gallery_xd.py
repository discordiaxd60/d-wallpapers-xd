#!/usr/bin/env python3
"""Browse the D-LinesOS wallpaper collection."""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

from PIL import Image, ImageTk


APP_NAME = "D-Gallery-XD"
SYSTEM_WALLPAPERS = Path("/usr/share/wallpapers/dlinesos")


def wallpaper_directory():
    if SYSTEM_WALLPAPERS.is_dir():
        return SYSTEM_WALLPAPERS
    return Path(__file__).resolve().parents[1] / "src-wallpapers"


def creator_from_filename(filename):
    stem = Path(filename).stem
    match = re.search(r"(?:_By_|-by-)([^_]+)$", stem, re.IGNORECASE)
    return match.group(1).replace("-", " ") if match else ""


def title_from_filename(filename):
    stem = Path(filename).stem
    stem = re.sub(r"(?:_By_|-by-)[^_]+$", "", stem, flags=re.IGNORECASE)
    return stem.replace("_", " ").replace("-", " ")


def load_wallpapers():
    directory = wallpaper_directory()
    manifest = directory / "wallpapers.json"
    if not manifest.is_file():
        raise FileNotFoundError(f"Wallpaper metadata was not found: {manifest}")

    with manifest.open(encoding="utf-8") as source:
        entries = json.load(source)
    if not isinstance(entries, list):
        raise ValueError(f"Expected a list of wallpapers in {manifest}")

    wallpapers = []
    for entry in entries:
        filename = entry.get("file")
        if not isinstance(filename, str) or Path(filename).name != filename:
            raise ValueError(f"Invalid wallpaper filename in {manifest}: {filename!r}")
        path = directory / filename
        if not path.is_file():
            raise FileNotFoundError(f"Wallpaper image was not found: {path}")
        uploaded = entry.get("uploaded")
        if not isinstance(uploaded, str):
            raise ValueError(f"Missing upload date for {filename}")
        try:
            uploaded_date = datetime.fromisoformat(uploaded).date()
        except ValueError as error:
            raise ValueError(
                f"Invalid ISO 8601 upload date for {filename}: {uploaded}"
            ) from error
        wallpapers.append(
            {
                "file": filename,
                "path": path,
                "title": title_from_filename(filename),
                "creator": entry.get("creator") or creator_from_filename(filename),
                "description": entry.get("description", "").strip(),
                "uploaded": uploaded,
                "uploaded_date": uploaded_date,
            }
        )
    return sorted(
        wallpapers,
        key=lambda item: (item["uploaded_date"], item["title"].casefold()),
    )


def set_wallpaper(path):
    uri = path.resolve().as_uri()
    gsettings = shutil.which("gsettings")
    if gsettings:
        schemas = subprocess.run(
            [gsettings, "list-schemas"], check=True, capture_output=True, text=True
        ).stdout.splitlines()
        if "org.gnome.desktop.background" in schemas:
            keys = subprocess.run(
                [gsettings, "list-keys", "org.gnome.desktop.background"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.splitlines()
            subprocess.run(
                [
                    gsettings,
                    "set",
                    "org.gnome.desktop.background",
                    "picture-uri",
                    uri,
                ],
                check=True,
            )
            if "picture-uri-dark" in keys:
                subprocess.run(
                    [
                        gsettings,
                        "set",
                        "org.gnome.desktop.background",
                        "picture-uri-dark",
                        uri,
                    ],
                    check=True,
                )
            return

    for executable in ("qdbus6", "qdbus", "qdbus-qt5"):
        qdbus = shutil.which(executable)
        if qdbus:
            script = (
                "var allDesktops = desktops();"
                'for (var i = 0; i < allDesktops.length; i++) {'
                '  var d = allDesktops[i];'
                '  d.wallpaperPlugin = "org.kde.image";'
                '  d.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];'
                f'  d.writeConfig("Image", "{uri}");'
                "}"
            )
            subprocess.run(
                [
                    qdbus,
                    "org.kde.plasmashell",
                    "/PlasmaShell",
                    "org.kde.PlasmaShell.evaluateScript",
                    script,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            return

    raise RuntimeError(
        "Automatic wallpaper setting is supported on GNOME and KDE Plasma desktops."
    )


class Gallery(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1080x760")
        self.minsize(720, 540)
        self.configure(background="#101318")
        self.wallpapers = load_wallpapers()
        self.card_images = []
        self.selected_path = None
        self.search_visible = False

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Gallery.TButton",
            background="#303743",
            foreground="#ffffff",
            borderwidth=0,
            padding=(14, 9),
        )
        style.map("Gallery.TButton", background=[("active", "#485466")])
        style.configure(
            "Set.TButton",
            background="#7257e8",
            foreground="#ffffff",
            borderwidth=0,
            padding=(16, 10),
        )
        style.map("Set.TButton", background=[("active", "#8a74f2")])

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self.header = tk.Frame(self, bg="#171b22", padx=24, pady=14)
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.columnconfigure(3, weight=1)

        tk.Label(
            self.header,
            text=APP_NAME,
            bg="#171b22",
            fg="#f4f5f7",
            font=("TkDefaultFont", 17, "bold"),
        ).grid(row=0, column=0, padx=(0, 28))
        ttk.Button(
            self.header, text="Home", style="Gallery.TButton", command=self.show_home
        ).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(
            self.header, text="All", style="Gallery.TButton", command=self.show_all
        ).grid(row=0, column=2, padx=(0, 8))
        self.search_button = ttk.Button(
            self.header,
            text="🔍",
            width=3,
            style="Gallery.TButton",
            command=self.toggle_search,
        )
        self.search_button.grid(row=0, column=4, sticky="e")
        self.search_entry = ttk.Entry(self.header, width=28)
        self.search_entry.bind("<KeyRelease>", self.update_search_results)
        self.search_entry.bind("<Return>", self.open_first_search_result)

        self.results = tk.Listbox(
            self,
            height=5,
            bg="#242a33",
            fg="#f4f5f7",
            selectbackground="#7257e8",
            relief="flat",
            highlightthickness=0,
            activestyle="none",
            font=("TkDefaultFont", 11),
        )
        self.results.bind("<<ListboxSelect>>", self.open_search_result)

        self.content = tk.Frame(self, bg="#101318")
        self.content.grid(row=2, column=0, sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(self.content, bg="#101318", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(
            self.content, orient="vertical", command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.page = tk.Frame(self.canvas, bg="#101318", padx=28, pady=24)
        self.page_window = self.canvas.create_window(
            (0, 0), window=self.page, anchor="nw"
        )
        self.page.bind(
            "<Configure>",
            lambda _event: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            ),
        )
        self.canvas.bind(
            "<Configure>",
            lambda event: self.canvas.itemconfigure(
                self.page_window, width=event.width
            ),
        )
        self.show_home()

    def clear_page(self):
        self.card_images.clear()
        for child in self.page.winfo_children():
            child.destroy()

    def show_home(self, selected=None):
        self.clear_page()
        self.selected_path = selected
        for column in range(4):
            self.page.columnconfigure(column, weight=0)
        self.page.columnconfigure(0, weight=1)
        self.home_cards = {}
        for index, item in enumerate(self.wallpapers):
            card = tk.Frame(
                self.page,
                bg="#1b2029",
                padx=18,
                pady=18,
                highlightthickness=2 if item["path"] == selected else 0,
                highlightbackground="#7257e8",
            )
            card.grid(row=index, column=0, sticky="ew", pady=(0, 16))
            card.columnconfigure(1, weight=1)
            try:
                with Image.open(item["path"]) as image:
                    resampling = getattr(Image, "Resampling", Image)
                    image.thumbnail((310, 190), resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image.copy())
            except OSError as error:
                raise RuntimeError(f"Could not load {item['path']}: {error}") from error
            self.card_images.append(photo)
            tk.Label(card, image=photo, bg="#1b2029").grid(
                row=0, column=0, rowspan=4, padx=(0, 22), sticky="w"
            )
            tk.Label(
                card,
                text=item["title"],
                bg="#1b2029",
                fg="#ffffff",
                font=("TkDefaultFont", 24, "bold"),
                anchor="w",
                justify="left",
            ).grid(row=0, column=1, sticky="ew", pady=(0, 7))
            tk.Label(
                card,
                text=(
                    f"By {item['creator']}"
                    if item["creator"]
                    else "Creator not credited"
                ),
                bg="#1b2029",
                fg="#b9c0cc",
                font=("TkDefaultFont", 11),
                anchor="w",
            ).grid(row=1, column=1, sticky="ew")
            tk.Label(
                card,
                text=item["description"] or "No description provided yet.",
                bg="#1b2029",
                fg="#d4d8df",
                font=("TkDefaultFont", 11),
                anchor="w",
                justify="left",
                wraplength=600,
            ).grid(row=2, column=1, sticky="ew", pady=(6, 8))
            tk.Label(
                card,
                text=f"Added {item['uploaded'][:10]}",
                bg="#1b2029",
                fg="#9099a7",
                font=("TkDefaultFont", 9),
                anchor="w",
            ).grid(row=3, column=1, sticky="ew", pady=(0, 12))
            ttk.Button(
                card,
                text="Set Wallpaper",
                style="Set.TButton",
                command=lambda path=item["path"]: self.apply_wallpaper(path),
            ).grid(row=4, column=1, sticky="w")
            self.home_cards[item["path"]] = card

        self.canvas.yview_moveto(0)
        if selected in self.home_cards:
            self.after_idle(lambda: self.scroll_to(selected))

    def show_all(self):
        self.clear_page()
        columns = max(1, min(4, self.canvas.winfo_width() // 260))
        for column in range(columns):
            self.page.columnconfigure(column, weight=1)
        for index, item in enumerate(self.wallpapers):
            tile = tk.Frame(self.page, bg="#1b2029", padx=8, pady=8)
            tile.grid(
                row=index // columns,
                column=index % columns,
                sticky="nsew",
                padx=6,
                pady=6,
            )
            try:
                with Image.open(item["path"]) as image:
                    resampling = getattr(Image, "Resampling", Image)
                    image.thumbnail((230, 130), resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image.copy())
            except OSError as error:
                raise RuntimeError(f"Could not load {item['path']}: {error}") from error
            self.card_images.append(photo)
            preview = tk.Label(tile, image=photo, bg="#1b2029", cursor="hand2")
            preview.pack(fill="x")
            label = tk.Label(
                tile,
                text=item["title"],
                bg="#1b2029",
                fg="#f4f5f7",
                font=("TkDefaultFont", 10, "bold"),
                wraplength=210,
            )
            label.pack(fill="x", pady=(8, 0))
            for widget in (tile, preview, label):
                widget.bind(
                    "<Button-1>",
                    lambda _event, path=item["path"]: self.show_home(path),
                )
        self.canvas.yview_moveto(0)

    def scroll_to(self, path):
        self.update_idletasks()
        card = self.home_cards[path]
        card_top = card.winfo_rooty() - self.page.winfo_rooty()
        content_height = max(self.page.winfo_height(), 1)
        self.canvas.yview_moveto(max(card_top / content_height, 0))

    def toggle_search(self):
        self.search_visible = not self.search_visible
        if self.search_visible:
            self.search_entry.grid(row=0, column=3, sticky="e", padx=10)
            self.search_entry.focus_set()
        else:
            self.search_entry.grid_remove()
            self.results.grid_remove()
            self.search_entry.delete(0, tk.END)

    def update_search_results(self, _event=None):
        query = self.search_entry.get().strip().casefold()
        self.results.delete(0, tk.END)
        self.search_matches = []
        if not query:
            self.results.grid_remove()
            return
        self.search_matches = [
            item
            for item in self.wallpapers
            if query in item["title"].casefold()
            or query in item["creator"].casefold()
        ][:8]
        for item in self.search_matches:
            self.results.insert(tk.END, item["title"])
        if self.search_matches:
            self.results.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 8))
            self.results.lift()
        else:
            self.results.grid_remove()

    def open_search_result(self, _event=None):
        selection = self.results.curselection()
        if selection:
            self.select_wallpaper(self.search_matches[selection[0]])

    def open_first_search_result(self, _event=None):
        if self.search_matches:
            self.select_wallpaper(self.search_matches[0])

    def select_wallpaper(self, item):
        self.results.grid_remove()
        self.show_home(item["path"])

    def apply_wallpaper(self, path):
        try:
            set_wallpaper(path)
        except (OSError, subprocess.CalledProcessError, RuntimeError) as error:
            messagebox.showerror("Could not set wallpaper", str(error), parent=self)
            return
        messagebox.showinfo(
            "Wallpaper set", f"{path.name} is now your desktop wallpaper.", parent=self
        )


def main():
    if not sys.platform.startswith("linux"):
        raise SystemExit(f"{APP_NAME} is a Linux desktop application.")
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument("--smoke-test", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    try:
        app = Gallery()
    except (OSError, RuntimeError, ValueError, tk.TclError) as error:
        print(f"{APP_NAME}: {error}", file=sys.stderr)
        try:
            messagebox.showerror(APP_NAME, str(error))
        except tk.TclError:
            pass
        return 1

    if args.smoke_test:
        app.update_idletasks()
        app.destroy()
        return 0
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
