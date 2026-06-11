# live2d_xiaob/scripts/Verify_Vampire_Model.py
# Verify vampire model integrity by parsing the model3.json with proper encoding
# and checking all FileReferences point to actual files on disk.

import os
import sys
import json
from pathlib import Path

VAMPIRE_DIR = Path(r"C:\Users\kitap\.openclaw\workspace\live2d_xiaob\vampire\vampire_vts")
MODEL_JSON = VAMPIRE_DIR / "吸血鬼.model3.json"


def main():
    if not MODEL_JSON.exists():
        print(f"[ERROR] Model JSON not found: {MODEL_JSON}", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("Vampire Model — Integrity Check")
    print("=" * 60)
    print(f"Model file: {MODEL_JSON.name}")
    print(f"Directory: {VAMPIRE_DIR}")
    print()

    # 1. Read JSON with UTF-8 (correct encoding for this file)
    try:
        with open(MODEL_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"[1/4] JSON parsed successfully (UTF-8)")
    except Exception as e:
        print(f"[ERROR] JSON parse failed: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Inspect FileReferences
    refs = data.get("FileReferences", {})
    print(f"\n[2/4] FileReferences:")
    for field, val in refs.items():
        if isinstance(val, str):
            print(f"   {field}: {val}")
        elif isinstance(val, list):
            print(f"   {field}: ({len(val)} items)")
            for i, item in enumerate(val):
                print(f"     [{i}]: {item}")

    # 3. Resolve and verify each reference
    print(f"\n[3/4] Resolving file references...")
    all_ok = True
    for field, val in refs.items():
        if isinstance(val, str):
            target = VAMPIRE_DIR / val
            exists = target.exists()
            status = "OK" if exists else "MISSING"
            size = target.stat().st_size // 1024 if exists else 0
            print(f"   {field}: {status} ({size} KB) -> {val}")
            if not exists:
                all_ok = False
        elif isinstance(val, list):
            for i, item in enumerate(val):
                target = VAMPIRE_DIR / item
                exists = target.exists()
                status = "OK" if exists else "MISSING"
                size = target.stat().st_size // 1024 if exists else 0
                print(f"   {field}[{i}]: {status} ({size} KB) -> {item}")
                if not exists:
                    all_ok = False

    # 4. Total package size
    print(f"\n[4/4] Package size audit:")
    total = sum(f.stat().st_size for f in VAMPIRE_DIR.rglob("*") if f.is_file())
    total_mb = round(total / (1024 * 1024), 2)
    print(f"   Total: {total_mb} MB")
    if total_mb > 15:
        print(f"   [WARNING] Exceeds 15MB Web budget (5.7x over)")
    else:
        print(f"   [OK] Within 15MB budget")

    print("\n" + "=" * 60)
    if all_ok:
        print("[SUCCESS] All FileReferences resolve. Model is loadable.")
    else:
        print("[FAIL] Some FileReferences are missing. Model load will fail.")
    print("=" * 60)

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
