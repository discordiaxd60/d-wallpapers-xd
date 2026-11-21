#!/usr/bin/env python3
import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WALLPAPER_DIR = ROOT / "src-wallpapers"
CATALOG_PATH = WALLPAPER_DIR / "catalog.json"
DESKTOP_CATALOG_PATH = ROOT / "packaging" / "desktop-backgrounds" / "dlinesos-wallpapers.xml"
WALLPAPER_INSTALL_DIR = "/usr/share/wallpapers/dlinesos"
IMAGE_FORMATS = {
    ".heic": ("HEIC", "image/heic"),
    ".jpeg": ("JPEG", "image/jpeg"),
    ".jpg": ("JPEG", "image/jpeg"),
    ".png": ("PNG", "image/png"),
}
REQUIRED_FIELDS = {
    "filename",
    "title",
    "author",
    "description",
    "tags",
    "dimensions",
    "aspect_ratio",
    "orientation",
    "format",
    "mime_type",
    "license",
}


def fail(errors):
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)


def validate_desktop_catalog(entries, errors):
    expected = {
        entry["filename"]: entry["title"]
        for entry in entries
        if isinstance(entry, dict)
        and isinstance(entry.get("filename"), str)
        and isinstance(entry.get("title"), str)
    }

    try:
        root = ET.parse(DESKTOP_CATALOG_PATH).getroot()
    except (OSError, ET.ParseError) as error:
        errors.append(f"Cannot read desktop wallpaper catalog {DESKTOP_CATALOG_PATH}: {error}")
        return

    if root.tag != "wallpapers":
        errors.append("Desktop wallpaper catalog root must be <wallpapers>.")
        return

    actual = {}
    for index, wallpaper in enumerate(root.findall("wallpaper")):
        name = wallpaper.findtext("name")
        filename = wallpaper.findtext("filename")
        if not name or not filename:
            errors.append(f"Desktop wallpaper entry {index} must have a name and filename.")
            continue
        if not filename.startswith(WALLPAPER_INSTALL_DIR + "/"):
            errors.append(f"Desktop wallpaper entry {index} has an unexpected path: {filename}.")
            continue
        image_name = filename[len(WALLPAPER_INSTALL_DIR) + 1 :]
        if image_name in actual:
            errors.append(f"Desktop wallpaper catalog contains duplicate image: {image_name}.")
        actual[image_name] = name
        if wallpaper.findtext("options") != "zoom":
            errors.append(f"Desktop wallpaper entry {index} must use the zoom option.")

    if actual != expected:
        errors.append("Desktop wallpaper catalog must match the titles and files in catalog.json.")


def main():
    try:
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail([f"Cannot read {CATALOG_PATH}: {error}"])

    errors = []
    if not isinstance(catalog, dict) or catalog.get("schema_version") != 1:
        fail(["Catalog must be an object with schema_version 1."])

    entries = catalog.get("images")
    if not isinstance(entries, list):
        fail(["Catalog images must be a list."])

    actual_files = {
        path.name
        for path in WALLPAPER_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_FORMATS
    }
    catalog_files = []

    for index, entry in enumerate(entries):
        prefix = f"images[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object.")
            continue

        missing_fields = REQUIRED_FIELDS - entry.keys()
        if missing_fields:
            errors.append(f"{prefix} is missing fields: {', '.join(sorted(missing_fields))}.")

        filename = entry.get("filename")
        if not isinstance(filename, str) or Path(filename).name != filename:
            errors.append(f"{prefix}.filename must be a simple filename.")
            continue
        catalog_files.append(filename)

        if not isinstance(entry.get("title"), str) or not entry["title"].strip():
            errors.append(f"{prefix}.title must be a non-empty string.")
        author = entry.get("author")
        if author is not None and (not isinstance(author, str) or not author.strip()):
            errors.append(f"{prefix}.author must be a non-empty string or null.")
        if not isinstance(entry.get("description"), str) or not entry["description"].strip():
            errors.append(f"{prefix}.description must be a non-empty string.")
        tags = entry.get("tags")
        if not isinstance(tags, list) or not tags or any(
            not isinstance(tag, str) or not tag.strip() for tag in tags
        ):
            errors.append(f"{prefix}.tags must be a non-empty list of strings.")

        image_format = IMAGE_FORMATS.get(Path(filename).suffix.lower())
        if image_format is None:
            errors.append(f"{prefix}.filename has an unsupported image extension.")
            continue
        expected_format, expected_mime_type = image_format
        if entry.get("format") != expected_format:
            errors.append(f"{prefix}.format must be {expected_format}.")
        if entry.get("mime_type") != expected_mime_type:
            errors.append(f"{prefix}.mime_type must be {expected_mime_type}.")

        dimensions = entry.get("dimensions")
        if not isinstance(dimensions, dict):
            errors.append(f"{prefix}.dimensions must contain width and height.")
            continue
        width, height = dimensions.get("width"), dimensions.get("height")
        if (
            not isinstance(width, int)
            or isinstance(width, bool)
            or not isinstance(height, int)
            or isinstance(height, bool)
            or width <= 0
            or height <= 0
        ):
            errors.append(f"{prefix}.dimensions must use positive integer width and height.")
            continue

        expected_orientation = "landscape" if width > height else "portrait" if width < height else "square"
        if entry.get("orientation") != expected_orientation:
            errors.append(f"{prefix}.orientation must be {expected_orientation}.")
        ratio = entry.get("aspect_ratio")
        if (
            not isinstance(ratio, (int, float))
            or isinstance(ratio, bool)
            or not math.isfinite(ratio)
            or abs(ratio - width / height) > 0.001
        ):
            errors.append(f"{prefix}.aspect_ratio does not match its dimensions.")

        license_value = entry.get("license")
        if license_value is not None and not isinstance(license_value, str):
            errors.append(f"{prefix}.license must be a string or null.")

    if len(catalog_files) != len(set(catalog_files)):
        errors.append("Catalog contains duplicate filenames.")

    catalog_set = set(catalog_files)
    for filename in sorted(actual_files - catalog_set):
        errors.append(f"Image is missing from catalog: {filename}.")
    for filename in sorted(catalog_set - actual_files):
        errors.append(f"Catalog entry has no image file: {filename}.")

    validate_desktop_catalog(entries, errors)

    if errors:
        fail(errors)
    print(f"Validated metadata for {len(entries)} wallpapers.")


if __name__ == "__main__":
    main()
