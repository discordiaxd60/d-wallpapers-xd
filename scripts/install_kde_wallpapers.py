#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import unicodedata
from pathlib import Path


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def package_id(filename):
    stem = Path(filename).stem
    slug = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-") or "wallpaper"
    suffix = hashlib.sha256(filename.encode("utf-8")).hexdigest()[:8]
    return f"dlinesos-{slug}-{suffix}"


def metadata_for(entry, identifier):
    plugin = {
        "Id": identifier,
        "Name": entry["title"],
        "Description": entry["description"],
        "Authors": [{"Name": entry["author"]}] if entry["author"] else [],
    }
    return {"KPackageStructure": "Wallpaper/Images", "KPlugin": plugin}


def desktop_metadata_for(entry, identifier):
    lines = [
        "[Desktop Entry]",
        f"Name={entry['title']}",
        f"X-KDE-PluginInfo-Name={identifier}",
    ]
    if entry["author"]:
        lines.append(f"X-KDE-PluginInfo-Author={entry['author']}")
    return "\n".join(lines) + "\n"


def validate_package(wallpaper_dir, package_root, entry, identifier):
    package_dir = package_root / identifier
    image_path = wallpaper_dir / entry["filename"]
    link_path = package_dir / "contents" / "images" / entry["filename"]
    metadata_path = package_dir / "metadata.json"
    desktop_metadata_path = package_dir / "metadata.desktop"

    try:
        image_exists = image_path.is_file()
        package_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        desktop_metadata = desktop_metadata_path.read_text(encoding="utf-8")
        link_valid = link_path.is_symlink() and link_path.resolve(strict=True) == image_path.resolve(strict=True)
    except (OSError, json.JSONDecodeError) as error:
        fail(f"KDE wallpaper package for {entry['filename']} is incomplete: {error}")

    if not image_exists:
        fail(f"Wallpaper image is missing: {image_path}")
    if package_metadata != metadata_for(entry, identifier):
        fail(f"KDE metadata does not match the catalog for {entry['filename']}.")
    if desktop_metadata != desktop_metadata_for(entry, identifier):
        fail(f"KDE desktop metadata does not match the catalog for {entry['filename']}.")
    if not link_valid:
        fail(f"KDE image link is missing or points to the wrong file: {link_path}")


def install_package(wallpaper_dir, package_root, entry, identifier):
    image_path = wallpaper_dir / entry["filename"]
    if not image_path.is_file():
        fail(f"Wallpaper image is missing: {image_path}")

    package_dir = package_root / identifier
    image_dir = package_dir / "contents" / "images"
    image_dir.mkdir(parents=True, exist_ok=True)

    link_path = image_dir / entry["filename"]
    relative_image_path = os.path.relpath(image_path, image_dir)
    if link_path.is_symlink():
        if link_path.resolve() != image_path.resolve():
            link_path.unlink()
            link_path.symlink_to(relative_image_path)
    elif link_path.exists():
        fail(f"Refusing to replace an existing KDE package image: {link_path}")
    else:
        link_path.symlink_to(relative_image_path)

    metadata = metadata_for(entry, identifier)
    (package_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (package_dir / "metadata.desktop").write_text(
        desktop_metadata_for(entry, identifier),
        encoding="utf-8",
    )


def remove_legacy_packages(wallpaper_dir, identifiers):
    legacy_root = wallpaper_dir.parent / f"{wallpaper_dir.name}-kde"
    if not legacy_root.is_dir() or legacy_root.is_symlink():
        return

    for identifier in identifiers:
        package_dir = legacy_root / identifier
        if not package_dir.is_dir() or package_dir.is_symlink():
            continue

        try:
            metadata = json.loads((package_dir / "metadata.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        if (
            isinstance(metadata, dict)
            and metadata.get("KPackageStructure") == "Wallpaper/Images"
        ):
            plugin = metadata.get("KPlugin")
        else:
            continue

        if (
            isinstance(plugin, dict) and plugin.get("Id") == identifier
        ):
            shutil.rmtree(package_dir)

    if not any(legacy_root.iterdir()):
        legacy_root.rmdir()


def main():
    parser = argparse.ArgumentParser(
        description="Create per-wallpaper KPackage metadata for Plasma's wallpaper picker."
    )
    parser.add_argument("--wallpaper-dir", required=True, type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify generated KPackage metadata and image links without changing files.",
    )
    args = parser.parse_args()

    wallpaper_dir = Path(os.path.abspath(args.wallpaper_dir))
    if (wallpaper_dir / "metadata.desktop").exists():
        fail(
            "The collection directory must not have a root metadata.desktop; "
            "Plasma only recognizes per-wallpaper packages below it."
        )

    catalog_path = wallpaper_dir / "catalog.json"
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"Cannot read wallpaper catalog {catalog_path}: {error}")

    entries = catalog.get("images") if isinstance(catalog, dict) else None
    if not isinstance(entries, list):
        fail(f"Wallpaper catalog has no images list: {catalog_path}")

    package_root = wallpaper_dir.parent
    if not args.check:
        package_root.mkdir(parents=True, exist_ok=True)

    identifiers = set()
    for entry in entries:
        if not isinstance(entry, dict):
            fail("Wallpaper catalog entries must be objects.")
        filename = entry.get("filename")
        title = entry.get("title")
        description = entry.get("description")
        author = entry.get("author")
        if (
            not isinstance(filename, str)
            or Path(filename).name != filename
            or not isinstance(title, str)
            or not title.strip()
            or not isinstance(description, str)
            or not description.strip()
            or "author" not in entry
            or (author is not None and (not isinstance(author, str) or not author.strip()))
        ):
            fail(f"Invalid KDE wallpaper metadata entry: {entry!r}")

        identifier = package_id(filename)
        if identifier in identifiers:
            fail(f"Duplicate KDE wallpaper package ID: {identifier}")
        identifiers.add(identifier)

        if args.check:
            validate_package(wallpaper_dir, package_root, entry, identifier)
        else:
            install_package(wallpaper_dir, package_root, entry, identifier)

    if not args.check:
        remove_legacy_packages(wallpaper_dir, identifiers)

    print(f"{'Validated' if args.check else 'Created'} {len(entries)} KDE wallpaper packages.")


if __name__ == "__main__":
    main()
