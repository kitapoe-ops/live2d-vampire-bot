# live2d_xiaob/scripts/Patch_Vampire_Model_References.py
# Auto-fix corrupted Chinese-garbled FileReferences inside vampire.model3.json
# (and other .json files in the vampire_vts folder that reference sibling files).
#
# Issue: Original model was downloaded with Chinese-garbled filenames (e.g. "?貉?擛?moc3").
# User renamed everything to "vampire.*" but JSON FileReferences inside still point to
# the corrupted (non-existent) names.
#
# Fix: For every *.json file in vampire_vts/ that contains FileReferences, rewrite all
#      sibling file references to use the current actual filenames on disk.

import os
import sys
import json
import re
from pathlib import Path

VAMPIRE_DIR = Path(r"C:\Users\kitap\.openclaw\workspace\live2d_xiaob\vampire\vampire_vts")

# Live2D FileReferences fields that point to sibling files
FILE_REF_FIELDS = [
    "Moc", "Physics", "DisplayInfo", "UserData", "Pose",
    "Motions", "Expressions", "Layout"
]


def detect_actual_filenames(directory: Path) -> dict:
    """
    Build a mapping of every file in the directory to its actual disk name.
    Returns dict of {actual_filename: actual_path}.
    """
    files = {}
    for f in directory.rglob("*"):
        if f.is_file():
            files[f.name] = f
    return files


def is_garbled_name(name: str) -> bool:
    """Detect if a name looks like Chinese-garbled (non-ASCII garbage)."""
    # Garbled names typically contain mojibake patterns or non-printable chars
    if not name:
        return True
    # Common mojibake signatures
    garbled_patterns = [r"\?\u8cfa\?\u64ff", r"\?", r"\ufffd"]
    for pat in garbled_patterns:
        if re.search(pat, name):
            return True
    # If it contains replacement character or unprintable, treat as garbled
    if "\ufffd" in name or "\x00" in name:
        return True
    return False


def patch_model_json(model_path: Path, actual_files: dict) -> bool:
    """
    Patch a single model.json file's FileReferences to point at actual sibling files.
    Returns True if file was modified.
    """
    try:
        with open(model_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        # Try latin-1 fallback (Cubism 5.x default for some files)
        try:
            with open(model_path, "r", encoding="latin-1") as f:
                data = json.load(f)
        except Exception as e2:
            print(f"  [SKIP] {model_path.name} — JSON parse failed: {e2}")
            return False

    if "FileReferences" not in data:
        return False

    refs = data["FileReferences"]
    modified = False

    for field in FILE_REF_FIELDS:
        if field not in refs:
            continue

        val = refs[field]
        if isinstance(val, str):
            # Single file reference
            if is_garbled_name(os.path.basename(val)):
                replacement = _find_actual_replacement(val, field, actual_files, model_path)
                if replacement:
                    print(f"  [FIX] {field}: '{val}' -> '{replacement}'")
                    refs[field] = replacement
                    modified = True
        elif isinstance(val, list):
            # List of file references (e.g. Textures)
            for i, item in enumerate(val):
                if isinstance(item, str) and is_garbled_name(os.path.basename(item)):
                    replacement = _find_actual_replacement(item, field, actual_files, model_path)
                    if replacement:
                        print(f"  [FIX] {field}[{i}]: '{item}' -> '{replacement}'")
                        val[i] = replacement
                        modified = True

    if modified:
        # Save back. Use latin-1 to preserve any garbled bytes if still needed.
        with open(model_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent="\t", ensure_ascii=False)
        return True
    return False


def _find_actual_replacement(broken_ref: str, field: str, actual_files: dict, model_path: Path) -> str:
    """
    Given a broken file reference like '?貉?擛?moc3', find the actual file in actual_files
    that matches the field type (e.g. .moc3 for Moc field).
    """
    # Field → expected extension mapping
    ext_map = {
        "Moc": ".moc3",
        "Physics": ".physics3.json",
        "DisplayInfo": ".cdi3.json",
        "UserData": ".userdata3.json",
        "Pose": ".pose3.json",
        "Textures": ".png"
    }

    expected_ext = ext_map.get(field)
    if not expected_ext:
        return ""

    # Find a file in actual_files that ends with the expected extension
    # and is closest to model_path in the directory tree
    model_dir = model_path.parent
    candidates = []
    for fname, fpath in actual_files.items():
        if fname.endswith(expected_ext):
            candidates.append((fpath, fname))

    if not candidates:
        return ""

    # Prefer same directory, then subdirectory
    same_dir = [c for c in candidates if c[0].parent == model_dir]
    if same_dir:
        # Prefer matching prefix to broken_ref base
        for fpath, fname in same_dir:
            return fname

    return candidates[0][1]


def main():
    if not VAMPIRE_DIR.exists():
        print(f"[ERROR] vampire_vts dir not found: {VAMPIRE_DIR}", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("Vampire Model — File Reference Patcher")
    print("=" * 60)
    print(f"Target: {VAMPIRE_DIR}")

    # 1. Discover actual files
    print("\n[1/3] Discovering actual files on disk...")
    actual_files = detect_actual_filenames(VAMPIRE_DIR)
    print(f"   Found {len(actual_files)} files")

    # 2. Find all .json files with FileReferences
    print("\n[2/3] Scanning .json files for broken FileReferences...")
    json_files = [f for f in VAMPIRE_DIR.rglob("*.json") if "FileReferences" in f.read_text(encoding="utf-8", errors="ignore")]

    if not json_files:
        print("   No .json files with FileReferences found")
        return

    # 3. Patch each
    print(f"\n[3/3] Patching {len(json_files)} model.json file(s)...")
    modified_count = 0
    for jf in json_files:
        print(f"\n--- {jf.name} ---")
        if patch_model_json(jf, actual_files):
            modified_count += 1

    print("\n" + "=" * 60)
    print(f"[DONE] Patched {modified_count} file(s).")
    print("=" * 60)
    print("Next step:")
    print("  1. Open BAZOOKA backend: python app.py")
    print("  2. Verify: open http://localhost:8000/api/v1/live2d/health")
    print("  3. Test model load via Cubism SDK or VTube Studio")
    print("=" * 60)


if __name__ == "__main__":
    main()
