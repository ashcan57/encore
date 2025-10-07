#!/usr/bin/env python3
"""
Robust Kodi repo builder:
 - finds addon folders (contains addon.xml)
 - zips each addon to zips/<addon_id>/<addon_id>-<version>.zip
 - builds addons.xml and addons.xml.md5 at repo root
Usage:
    python repo_builder.py             # use current dir as repo root
    python repo_builder.py --root /path/to/repo --force --verbose
    python repo_builder.py --dry-run
"""

import os
import sys
import argparse
import zipfile
import hashlib
import xml.etree.ElementTree as ET

EXCLUDE_DIRS = {'.git', 'zips', '.github', '__pycache__'}

def find_addon_dirs(root, verbose=False):
    found = []
    root = os.path.abspath(root)
    root_depth = root.rstrip(os.sep).count(os.sep)

    # 1) Check immediate children (most common)
    for name in os.listdir(root):
        p = os.path.join(root, name)
        if not os.path.isdir(p): continue
        if name in EXCLUDE_DIRS: continue
        if os.path.isfile(os.path.join(p, 'addon.xml')):
            if verbose: print(f"Found addon.xml in top-level folder: {p}")
            found.append(p)

    # 2) Check ./addons if it exists (some people keep addons there)
    addons_dir = os.path.join(root, 'addons')
    if os.path.isdir(addons_dir):
        for name in os.listdir(addons_dir):
            p = os.path.join(addons_dir, name)
            if os.path.isdir(p) and os.path.isfile(os.path.join(p, 'addon.xml')):
                if verbose: print(f"Found addon.xml in ./addons: {p}")
                found.append(p)

    # 3) Fallback: shallow walk up to depth 3 to catch uncommon layouts
    if not found:
        if verbose: print("No top-level addons found; doing shallow scan (max depth 3)...")
    for dirpath, dirnames, filenames in os.walk(root):
        # skip excluded dirs
        parts = set(dirpath.split(os.sep))
        if parts & EXCLUDE_DIRS:
            continue
        depth = dirpath.count(os.sep) - root_depth
        if depth > 3:
            # skip deep folders for speed
            continue
        if 'addon.xml' in filenames:
            if verbose: print(f"Found addon.xml: {dirpath}")
            found.append(dirpath)
    # unique and preserve order
    unique = []
    for x in found:
        if x not in unique:
            unique.append(x)
    return unique

def parse_addon_xml(addon_xml_path):
    try:
        tree = ET.parse(addon_xml_path)
        root = tree.getroot()
        addon_id = root.attrib.get('id')
        addon_version = root.attrib.get('version')
        return addon_id, addon_version
    except ET.ParseError as e:
        raise RuntimeError(f"XML parse error in {addon_xml_path}: {e}")

def make_zip_for_addon(addon_dir, zip_root, force=False, verbose=False):
    addon_xml = os.path.join(addon_dir, 'addon.xml')
    if not os.path.isfile(addon_xml):
        if verbose: print(f"Skipping {addon_dir} — no addon.xml")
        return None

    addon_id, addon_version = parse_addon_xml(addon_xml)
    if not addon_id or not addon_version:
        if verbose:
            print(f"Skipping {addon_dir} — missing id or version (id={addon_id}, version={addon_version})")
        return None

    target_dir = os.path.join(zip_root, addon_id)
    os.makedirs(target_dir, exist_ok=True)
    zip_name = f"{addon_id}-{addon_version}.zip"
    zip_path = os.path.join(target_dir, zip_name)

    if os.path.exists(zip_path) and not force:
        if verbose: print(f"Zip exists and --force not set, skipping: {zip_path}")
        return zip_path

    if verbose: print(f"Creating zip: {zip_path}")

    try:
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            for rootdir, _, files in os.walk(addon_dir):
                # skip __pycache__ inside addon
                if '__pycache__' in rootdir:
                    continue
                for f in files:
                    # skip common unwanted files
                    if f.endswith(('.pyc', '.DS_Store', 'Thumbs.db')):
                        continue
                    filepath = os.path.join(rootdir, f)
                    arcname = os.path.relpath(filepath, start=addon_dir)
                    z.write(filepath, arcname)
        return zip_path
    except Exception as e:
        raise RuntimeError(f"Failed to zip {addon_dir} -> {e}")

def build_addons_xml(addon_dirs, output_path, verbose=False):
    snippets = []
    for addon_dir in addon_dirs:
        addon_xml_path = os.path.join(addon_dir, 'addon.xml')
        if not os.path.isfile(addon_xml_path):
            if verbose: print(f"Skipping {addon_dir} for addons.xml — no addon.xml")
            continue
        with open(addon_xml_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            # remove xml declaration if present
            if content.startswith('<?xml'):
                idx = content.find('?>')
                if idx != -1:
                    content = content[idx+2:].strip()
            snippets.append(content)
    full = "<addons>\n" + "\n\n".join(snippets) + "\n</addons>\n"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full)
    if verbose: print(f"Written {output_path} with {len(snippets)} addons.")
    return output_path

def make_md5(file_path, out_path, verbose=False):
    import hashlib
    h = hashlib.md5()
    with open(file_path, 'rb') as f:
        h.update(f.read())
    digest = h.hexdigest()
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(digest)
    if verbose: print(f"Written {out_path} (md5: {digest})")
    return digest

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', '-r', default='.', help='Repo root (default: current dir)')
    parser.add_argument('--force', '-f', action='store_true', help='Overwrite existing zips')
    parser.add_argument('--dry-run', action='store_true', help='Show actions without creating files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    zip_root = os.path.join(root, 'zips')
    addons_xml = os.path.join(root, 'addons.xml')
    addons_md5 = os.path.join(root, 'addons.xml.md5')

    if args.verbose:
        print(f"Repo root: {root}")
        print(f"Zip root: {zip_root}")

    addon_dirs = find_addon_dirs(root, verbose=args.verbose)
    if not addon_dirs:
        print("No addon directories found. Make sure you run this from the repo root and that each addon has an 'addon.xml'.")
        sys.exit(2)

    created = []
    skipped = []
    if not args.dry_run:
        os.makedirs(zip_root, exist_ok=True)

    for addon_dir in addon_dirs:
        try:
            if args.dry_run:
                print(f"[DRY] would zip: {addon_dir}")
                continue
            z = make_zip_for_addon(addon_dir, zip_root, force=args.force, verbose=args.verbose)
            if z:
                created.append(z)
            else:
                skipped.append(addon_dir)
        except Exception as e:
            print(f"ERROR zipping {addon_dir}: {e}")

    if args.dry_run:
        print("Dry run complete.")
        return

    # Build addons.xml from the same set of addon dirs (preserve order)
    build_addons_xml(addon_dirs, addons_xml, verbose=args.verbose)
    make_md5(addons_xml, addons_md5, verbose=args.verbose)

    print("\nDone.")
    print(f"Created {len(created)} zips, skipped {len(skipped)} addons.")
    if created:
        for c in created:
            print("  +", c)
    if skipped:
        print("Skipped (no id/version or other reason):")
        for s in skipped:
            print("  -", s)

if __name__ == '__main__':
    main()
