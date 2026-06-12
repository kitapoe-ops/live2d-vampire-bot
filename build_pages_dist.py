#!/usr/bin/env python3
"""
build_pages_dist.py — Build Cloudflare Pages deploy directory
================================================================
2026-06-12 BAZOOKA-free deployment.

Merges:
  - backend/static/embed/*         → dist-pages/  (root, widget files)
  - vampire/vampire_vts/*          → dist-pages/live2d/vampire/  (Live2D model)
  - _headers, _redirects           → dist-pages/  (security config)

After this script runs, the dist-pages/ directory is ready for
`wrangler pages deploy dist-pages --project-name vampire-widget`.

The widget's DEFAULT_MODEL path is patched in-place to match the new
live2d/vampire/ subdirectory layout (no longer vampire.kitahim.uk BAZOOKA URL).
"""
import os, shutil, sys, re
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
DIST = ROOT / "dist-pages"
EMBED_SRC = ROOT / "backend" / "static" / "embed"
MODEL_SRC = ROOT / "vampire" / "vampire_vts"
DEST_MODEL = DIST / "live2d" / "vampire"

def clean():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

def copy_embed():
    print(f"Copying embed sources from {EMBED_SRC}")
    for src in EMBED_SRC.rglob("*"):
        if src.is_file():
            rel = src.relative_to(EMBED_SRC)
            dst = DIST / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    print(f"  -> {len(list(EMBED_SRC.rglob('*')))} entries copied")

def copy_model():
    print(f"Copying Live2D model from {MODEL_SRC} -> {DEST_MODEL}")
    DEST_MODEL.mkdir(parents=True, exist_ok=True)
    n = 0
    for src in MODEL_SRC.rglob("*"):
        if src.is_file():
            rel = src.relative_to(MODEL_SRC)
            dst = DEST_MODEL / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            n += 1
    print(f"  -> {n} files copied ({sum(f.stat().st_size for f in DEST_MODEL.rglob('*') if f.is_file()) / 1e6:.1f} MB)")

def patch_widget_model_path():
    """Update DEFAULT_MODEL in widget.html to use relative path on Pages."""
    wh = DIST / "widget.html"
    if not wh.exists():
        print("WARNING: widget.html not in dist, skipping patch")
        return
    text = wh.read_text(encoding="utf-8")
    # BAZOOKA URL -> relative path that Pages will serve
    old_pattern = r"'https://vampire\.kitahim\.uk/static/live2d/vampire/' \+ encodeURIComponent\('吸血鬼'\) \+ '\.model3\.json'"
    new_replacement = "'./live2d/vampire/' + encodeURIComponent('吸血鬼') + '.model3.json'"
    new_text, count = re.subn(old_pattern, new_replacement, text)
    if count == 0:
        print("WARNING: DEFAULT_MODEL pattern not found in widget.html — patch may be already applied or pattern changed")
    else:
        wh.write_text(new_text, encoding="utf-8")
        print(f"Patched DEFAULT_MODEL in widget.html ({count} occurrence)")

def write_security_files():
    """Write _headers and _redirects for Cloudflare Pages."""
    headers = """\
/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: ALLOW-FROM https://*
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(self), microphone=(self), geolocation=()
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload

/static/embed/*
  Cache-Control: public, max-age=300, must-revalidate
  X-Content-Type-Options: nosniff

/static/embed/widget.html
  Cache-Control: public, max-age=0, must-revalidate

/live2d/*
  Cache-Control: public, max-age=86400, immutable
  X-Content-Type-Options: nosniff

/live2d/*/*.moc3
  Cache-Control: public, max-age=86400, immutable

/live2d/*/*.model3.json
  Cache-Control: public, max-age=0, must-revalidate
"""
    (DIST / "_headers").write_text(headers, encoding="utf-8")
    print("Wrote _headers")

    # No rewrites needed for static widget; the existing routes are direct file lookups
    redirects = """\
# Cloudflare Pages _redirects
# 2026-06-12: vampire.kitahim.uk -> static widget (no /api/* proxy).
# /api/* paths would 404 here; widget code falls back to direct MiniMax TTS API
# when the user supplies their own key via the in-widget modal.
"""
    (DIST / "_redirects").write_text(redirects, encoding="utf-8")
    print("Wrote _redirects")

if __name__ == "__main__":
    print("=== build_pages_dist.py ===")
    clean()
    copy_embed()
    copy_model()
    patch_widget_model_path()
    write_security_files()
    # Summary
    files = list(DIST.rglob("*"))
    file_count = sum(1 for f in files if f.is_file())
    total_size = sum(f.stat().st_size for f in files if f.is_file())
    print(f"\nDone. dist-pages/ contains {file_count} files, {total_size / 1e6:.1f} MB total")
    print(f"Path: {DIST}")
