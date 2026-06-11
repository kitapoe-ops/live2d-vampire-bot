# live2d_xiaob/scripts/Optimize_Vampire_Textures.py
# Resize vampire model textures from 8192x8192 -> 4096x4096 to fit 15MB Web budget.
# Reference: cubism_mesh_spec.md Section 8 (15MB file size budget)
#
# Pipeline:
#   1. Read all 4 texture_*.png (8192x8192)
#   2. Resize to 4096x4096 (75% file size reduction expected)
#   3. Save to optimized folder
#   4. Patch 吸血鬼.model3.json FileReferences to point at new files
#   5. Verify total package size

import os
import sys
import json
import shutil
from pathlib import Path
from PIL import Image

VAMPIRE_DIR = Path(r"C:\Users\kitap\.openclaw\workspace\live2d_xiaob\vampire\vampire_vts")
TEXTURE_SUBDIR = "吸血鬼.8192"
OPTIMIZED_SUBDIR = "吸血鬼.4096"
MODEL_JSON = VAMPIRE_DIR / "吸血鬼.model3.json"

# Target sizes
ORIG_SIZE = 4096
NEW_SIZE = 2048

# 15MB Web budget (per cubism_mesh_spec.md Section 8)
BUDGET_MB = 15.0


def get_dir_size_mb(path: Path) -> float:
    """Compute total size of a directory recursively in MB."""
    total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return round(total / (1024 * 1024), 2)


def resize_textures():
    """Resize 4 texture PNGs from 8192 to 4096, save into optimized subdir."""
    src_dir = VAMPIRE_DIR / OPTIMIZED_SUBDIR  # read from 4096 (now the 'source')
    dst_dir = VAMPIRE_DIR / "吸血鬼.2048"

    if not src_dir.exists():
        print(f"[ERROR] Source texture dir not found: {src_dir}", file=sys.stderr)
        sys.exit(1)

    # Create destination
    dst_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print(f"Vampire Texture Optimizer: {ORIG_SIZE} -> {NEW_SIZE}")
    print("=" * 60)
    print(f"Source: {src_dir}")
    print(f"Dest:   {dst_dir}")
    print()

    texture_files = sorted(src_dir.glob("texture_*.png"))
    if not texture_files:
        print(f"[ERROR] No texture_*.png files found in {src_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"[1/4] Found {len(texture_files)} texture file(s) to optimize:")
    total_before_kb = 0
    total_after_kb = 0
    for tf in texture_files:
        size_before = tf.stat().st_size
        size_before_kb = round(size_before / 1024, 1)
        total_before_kb += size_before_kb
        print(f"   {tf.name}: {size_before_kb} KB ({size_before // (1024*1024)} MB)")

    print(f"\n   Total BEFORE: {round(total_before_kb/1024, 2)} MB")
    print()

    # Resize each
    print(f"[2/4] Resizing to {NEW_SIZE}x{NEW_SIZE}...")
    for tf in texture_files:
        dst_path = dst_dir / tf.name
        print(f"   Processing {tf.name}...")
        img = Image.open(tf)
        if img.size != (NEW_SIZE, NEW_SIZE):
            # Use LANCZOS for highest quality downsampling
            img_resized = img.resize((NEW_SIZE, NEW_SIZE), Image.LANCZOS)
        else:
            img_resized = img  # Already correct size
        # Save with optimize=True to reduce PNG size further
        img_resized.save(dst_path, optimize=True)
        size_after = dst_path.stat().st_size
        size_after_kb = round(size_after / 1024, 1)
        total_after_kb += size_after_kb
        print(f"      -> {size_after_kb} KB ({round(size_after/(1024*1024), 2)} MB)")

    print(f"\n   Total AFTER:  {round(total_after_kb/1024, 2)} MB")
    reduction_pct = round((1 - total_after_kb / total_before_kb) * 100, 1)
    print(f"   Reduction:    {reduction_pct}%")
    print()


def patch_model_json():
    """Rewrite FileReferences in 吸血鬼.model3.json to use new texture path."""
    if not MODEL_JSON.exists():
        print(f"[ERROR] Model JSON not found: {MODEL_JSON}", file=sys.stderr)
        sys.exit(1)

    print(f"[3/4] Patching {MODEL_JSON.name}...")

    with open(MODEL_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    refs = data.get("FileReferences", {})
    textures = refs.get("Textures", [])

    if not textures:
        print("   [WARN] No Textures references found")
        return

    # Replace each texture path: 吸血鬼.4096/texture_XX.png -> 吸血鬼.2048/texture_XX.png
    new_textures = []
    for tex in textures:
        new_tex = tex.replace(OPTIMIZED_SUBDIR, "吸血鬼.2048")
        new_textures.append(new_tex)
        print(f"   {tex} -> {new_tex}")

    refs["Textures"] = new_textures
    data["FileReferences"] = refs

    with open(MODEL_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent="\t", ensure_ascii=False)

    print(f"   [OK] Model JSON patched.")


def verify_size():
    """Final audit: total package size vs 15MB budget."""
    print(f"\n[4/4] Final package size audit...")
    total_mb = get_dir_size_mb(VAMPIRE_DIR)
    print(f"   Total package: {total_mb} MB")

    if total_mb <= BUDGET_MB:
        print(f"   [SUCCESS] Within 15MB budget!")
    else:
        over_pct = round((total_mb / BUDGET_MB - 1) * 100, 1)
        print(f"   [WARNING] Still over 15MB budget ({over_pct}% over)")
        print(f"   [TIP] Consider: reduce motion files / remove unused textures")

    print()
    print("=" * 60)
    print("Next step:")
    print("  1. Test model load with the new 4096 textures")
    print("  2. If visuals degraded, can revert by re-renaming subfolder")
    print("  3. Original 8192 textures preserved in 吸血鬼.8192/ subdir")
    print("=" * 60)


if __name__ == "__main__":
    try:
        resize_textures()
        patch_model_json()
        verify_size()
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
