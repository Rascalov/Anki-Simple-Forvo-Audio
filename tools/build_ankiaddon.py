#!/usr/bin/env python3
"""Build a .ankiaddon package.

An .ankiaddon is a plain zip with the add-on's files at the *root* — no
wrapping folder — plus a manifest.json naming the package. Anki refuses an
archive containing __pycache__, so nothing is copied blindly.

    python tools/build_ankiaddon.py --version 2.0.0

Writes dist/<package>-<version>.ankiaddon.
"""

import argparse
import json
import os
import pathlib
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

# The add-on is every Python module at the top level, plus its config and
# licence. Everything else in the repository — tests, this script, the README's
# screenshots, the .github folder — stays out of the package.
DATA_FILES = ("config.json", "config.md", "LICENSE")

PACKAGE = "560814150"  # the AnkiWeb id, so a manual install upgrades in place
NAME = "Anki Simple Forvo Audio"
HOMEPAGE = "https://github.com/Rascalov/Anki-Simple-Forvo-Audio"
# 2.1.50 is the first Anki built on Qt6, and the dialogs use Qt6 scoped enums.
MIN_POINT_VERSION = 50


def addon_files():
    """Every file that belongs in the package, as (source, name-in-zip)."""
    files = [(path, path.name) for path in sorted(ROOT.glob("*.py"))]
    for name in DATA_FILES:
        path = ROOT / name
        if path.is_file():
            files.append((path, name))
    return files


def source_date_epoch():
    """The commit time, so rebuilding the same commit gives the same zip."""
    override = os.environ.get("SOURCE_DATE_EPOCH")
    if override:
        return int(override)
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--pretty=%ct"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        return int(out.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return None


def build_manifest(version, mod):
    manifest = {
        "package": PACKAGE,
        "name": NAME,
        "human_version": version,
        "homepage": HOMEPAGE,
        "min_point_version": MIN_POINT_VERSION,
    }
    if mod is not None:
        manifest["mod"] = mod
    return json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"


def build(version, output=None):
    files = addon_files()
    if not any(name == "__init__.py" for _, name in files):
        sys.exit("error: no __init__.py at the repository root")

    mod = source_date_epoch()
    # Zip entries need a date; a fixed one keeps the build reproducible.
    timestamp = (1980, 1, 1, 0, 0, 0)

    DIST.mkdir(exist_ok=True)
    output = pathlib.Path(output) if output else DIST / f"{PACKAGE}-{version}.ankiaddon"

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for source, name in files:
            info = zipfile.ZipInfo(name, date_time=timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, source.read_bytes())
        info = zipfile.ZipInfo("manifest.json", date_time=timestamp)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        archive.writestr(info, build_manifest(version, mod))

    verify(output)
    print(f"built {output.relative_to(ROOT)} ({output.stat().st_size:,} bytes)")
    for name in sorted(zipfile.ZipFile(output).namelist()):
        print(f"  {name}")
    return output


def verify(path):
    """Refuse to ship something Anki will reject or silently mis-install."""
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        broken = archive.testzip()
        if broken:
            sys.exit(f"error: corrupt entry in archive: {broken}")
        for name in names:
            if "__pycache__" in name or name.endswith(".pyc"):
                sys.exit(f"error: {name} must not be in the package")
            if name.startswith("/") or ".." in pathlib.PurePosixPath(name).parts:
                sys.exit(f"error: unsafe path in archive: {name}")
        for required in ("__init__.py", "manifest.json"):
            if required not in names:
                sys.exit(f"error: {required} is missing from the archive root")
        manifest = json.loads(archive.read("manifest.json"))
        for key in ("package", "name"):
            if not manifest.get(key):
                sys.exit(f"error: manifest.json has no {key}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="human version, e.g. 2.0.0")
    parser.add_argument("--output", help="path to write instead of dist/")
    args = parser.parse_args()
    build(args.version.lstrip("v"), args.output)


if __name__ == "__main__":
    main()
