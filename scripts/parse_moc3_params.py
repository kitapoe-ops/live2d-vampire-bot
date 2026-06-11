# live2d_xiaob/scripts/parse_moc3_params.py
# Reverse-engineer the .moc3 binary to find ALL parameter IDs (194 of them)
# This complements our Scene1.motion3.json anchors (Paramtears3/4, Paramcircle2)
#
# Strategy:
#  1. Find all UTF-8 strings of length 6-30 (typical Live2D param ID length)
#  2. Filter to "Param*" prefix (Live2D convention)
#  3. Count unique matches
#  4. Compare with binary structure to deduce param order

import re
import struct
from collections import Counter

MOC3_PATH = r"C:\Users\kitap\.openclaw\workspace\live2d_xiaob\vampire\vampire_vts\吸血鬼.moc3"
OUTPUT_PATH = r"C:\Users\kitap\.openclaw\workspace\live2d_xiaob\scripts\vampire_param_ids.txt"


def find_all_strings(data: bytes, min_len: int = 4, max_len: int = 40) -> list:
    """Extract all UTF-8 readable strings from binary."""
    pattern = re.compile(rb"[\x20-\x7e]{%d,%d}" % (min_len, max_len))
    return [m.group(0).decode("ascii", errors="replace") for m in pattern.finditer(data)]


def main():
    with open(MOC3_PATH, "rb") as f:
        data = f.read()

    print(f"File: {MOC3_PATH}")
    print(f"Size: {len(data)} bytes ({len(data)/1024/1024:.2f} MB)")
    print()

    # 1. Find all ASCII strings
    all_strings = find_all_strings(data, min_len=4, max_len=40)
    print(f"Total ASCII strings (4-40 chars): {len(all_strings)}")

    # 2. Filter to Live2D param convention: starts with "Param"
    param_ids = [s for s in all_strings if s.startswith("Param")]
    print(f"  Starting with 'Param': {len(param_ids)}")

    # 3. Unique param IDs (in order of first appearance)
    seen = set()
    unique_params = []
    for s in all_strings:
        if s.startswith("Param") and s not in seen:
            seen.add(s)
            unique_params.append(s)
    print(f"  Unique param IDs: {len(unique_params)}")

    # 4. Compare with Scene1.motion3.json anchors
    known = ["Paramtears3", "Paramtears4", "Paramcircle2"]
    print()
    print("Anchor verification (from Scene1.motion3.json):")
    for kid in known:
        found = kid in unique_params
        print(f"  {kid:25s} {'FOUND' if found else 'MISSING'}")

    # 5. Try common Cubism 5.x param names (to see what's MISSING)
    common = [
        "ParamAngleX", "ParamAngleY", "ParamAngleZ",
        "ParamEyeLOpen", "ParamEyeROpen", "ParamMouthOpenY",
        "ParamMouthForm", "ParamBodyAngleX", "ParamBodyAngleY", "ParamBodyAngleZ",
        "ParamBreath",
    ]
    print()
    print("Standard Cubism 5.x param search (might be missing in vampire model):")
    for c in common:
        found = c in unique_params
        print(f"  {c:25s} {'FOUND' if found else 'MISSING (vampire uses custom names)'}")

    # 6. Write all unique params to file
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Vampire model parameter IDs\n")
        f.write(f"# Source: {MOC3_PATH}\n")
        f.write(f"# Total unique Param* IDs: {len(unique_params)}\n\n")
        for i, p in enumerate(unique_params):
            f.write(f"[{i:3d}] {p}\n")

    print()
    print(f"Wrote {len(unique_params)} unique param IDs to:")
    print(f"  {OUTPUT_PATH}")

    # 7. Show first 20 + last 20 as preview
    print()
    print("First 20 params:")
    for p in unique_params[:20]:
        print(f"  {p}")
    print("...")
    print("Last 20 params:")
    for p in unique_params[-20:]:
        print(f"  {p}")


if __name__ == "__main__":
    main()
