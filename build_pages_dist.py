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
  # 2026-06-13: X-Frame-Options: ALLOW-FORM is deprecated (Chrome shows
  # "is not a recognized directive" warning). Replace with modern
  # Content-Security-Policy: frame-ancestors which Chrome respects.
  X-Frame-Options: ALLOW-FROM https://*
  Content-Security-Policy: frame-ancestors *; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://api.deepseek.com; connect-src 'self' https://api.deepseek.com https://api.minimax.chat https://static.cloudflareinsights.com
  Referrer-Policy: strict-origin-when-cross-origin
  # 2026-06-13 mobile mic fix: change microphone=(self) to microphone=*
  # so that the embedded widget iframe (also vampire.kitahim.uk) is
  # explicitly allowed to use mic. Same for camera. geolocation stays
  # disabled. Trade-off: any 3rd-party page that embeds the widget now
  # has mic/camera delegated, but they could already render the widget
  # and capture permissions via the bubble UI; not a meaningful expansion.
  Permissions-Policy: camera=*, microphone=*, geolocation=()
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

    # Legacy BAZOOKA path rewrites for third-party embeds.
    # 2026-06-12 16:06 BUG FIX: third-party sites that embedded
    # <script src="https://vampire.kitahim.uk/static/embed/embed.js"> are now
    # broken because Pages SPA fallback returns 200 + text/html for that path,
    # which the browser blocks via strict MIME check. Rewriting to root.
    redirects = """\
# Cloudflare Pages _redirects
# 2026-06-12: vampire.kitahim.uk -> static widget (no /api/* proxy).
# /api/* paths would 404 here; widget code falls back to direct MiniMax TTS API
# when the user supplies their own key via the in-widget modal.

# === 2026-06-12 16:06 BUG FIX: third-party embeds using legacy BAZOOKA paths ===
# Browser console error: "Refused to execute script from
# 'https://vampire.kitahim.uk/static/embed/embed.js?v=20260612v04' because its
# MIME type ('text/html') is not executable, and strict MIME type checking is
# enabled." Third-party sites that embedded the widget via the legacy BAZOOKA
# path /static/embed/embed.js get a 200 + HTML fallback from Pages (SPA-style
# routing for unknown paths), not a 404 — so the browser blocks the script.
# Rewrite legacy paths to root via 301 (permanent) so the redirect is cached
# client-side and the browser fetches the new path with the correct MIME type.

# 1. Explicit directory slugs (must come BEFORE splat — Pages matches first
#    matching rule)
/static/embed/                 /                          301
/static/embed                  /                          301

# 2. Explicit per-file rules (so /static/embed/embed.js returns 301 not
#    SPA-fallback 200). Pages quirk: when no rule matches and no file exists,
#    Pages returns SPA 200; explicit rules bypass the SPA fallback.
/static/embed/embed.js         /embed.js                  301
/static/embed/widget.html      /widget                    301
/static/embed/widget           /widget                    301
/static/embed/index.html       /                          301
/static/embed/knowledge.js     /knowledge.js              301
/static/embed/demo.html        /                          301

# 3. Catch-all for any other /static/embed/* path (handles vendor/* and
#    future files)
/static/embed/*                /:splat                    301

# === 2026-06-12 16:10: also redirect legacy model path /static/live2d/ -> /live2d/ ===
# widget.html DEFAULT_MODEL was patched to ./live2d/vampire/... at build time,
# but if any external page cached the old hardcoded URL, this preserves them.
/static/live2d/*               /live2d/:splat              301
"""
    (DIST / "_redirects").write_text(redirects, encoding="utf-8")
    print("Wrote _redirects (with legacy /static/embed/* rewrite)")

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
