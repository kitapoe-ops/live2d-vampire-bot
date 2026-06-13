#!/usr/bin/env python3
"""
Smoke test: Mobile mic permission issue on https://vampire.kitahim.uk/

Reproduces user's report:
- "網頁設置已經允許使用麥克風，手機模式仍然顯示未獲授權"

We test in mobile emulation (iPhone 12 Pro viewport + UA) and desktop Chrome
for comparison. Captures:
  - Console logs/errors
  - iframe.contentWindow.SR detection
  - Click mic button
  - Bubble text changes after click (the "hint" displayed)
  - e.error value via monkey-patch on recognition.onerror
"""
import sys
import time
from playwright.sync_api import sync_playwright

URL = "https://vampire.kitahim.uk/"

def run_test(viewport, ua_suffix, label):
    print(f"\n=== {label} ===")
    print(f"Viewport: {viewport}, UA suffix: {ua_suffix}")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream']
        )
        ctx = browser.new_context(
            viewport=viewport,
            user_agent=ua_suffix,
            permissions=['microphone'],
            is_mobile=(viewport['width'] < 600),
            has_touch=(viewport['width'] < 600),
            device_scale_factor=2,
        )
        page = ctx.new_page()
        console_logs = []
        page.on("console", lambda msg: console_logs.append((msg.type, msg.text)))
        page.on("pageerror", lambda exc: console_logs.append(("pageerror", str(exc))))
        # Capture all failed network requests
        failed_requests = []
        page.on("requestfailed", lambda req: failed_requests.append({"url": req.url, "failure": req.failure, "method": req.method}))

        print(f"Navigating to {URL}...")
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"NAV ERROR: {e}")
            browser.close()
            return

        # Wait for widget iframe to appear (or fail)
        try:
            page.wait_for_selector('iframe[title*="虛擬人"], iframe[title*="avatar"], iframe[title*="AI"]', timeout=15000)
        except Exception as e:
            print(f"IFRAME NOT FOUND: {e}")
            # Print body text
            try:
                body = page.evaluate("() => document.body.innerText")
                print(f"Body text: {body[:500]}")
            except: pass
            browser.close()
            return

        # Give the iframe some time to load and initialize
        time.sleep(5)

        # Find the iframe
        frames = page.frames
        widget_frame = None
        # Also capture failed requests inside the widget frame
        # (page.on('requestfailed') doesn't always fire for cross-frame; we add per-frame)
        # We'll loop later and attach listeners
        widget_failed = []
        # Skip the main page frame (url ends with /) — look for the actual widget iframe
        for f in frames:
            fu = f.url or ''
            if 'vampire.kitahim.uk' in fu and (fu.endswith('/') is False or 'widget' in fu):
                widget_frame = f
                break
        # Fallback: pick the frame whose URL contains 'widget' or 'v=' (cache-bust)
        if not widget_frame:
            for f in frames:
                if 'widget' in (f.url or '') or 'v=' in (f.url or ''):
                    widget_frame = f
                    break
        # Last fallback: pick the LAST frame (the nested one created by embed.js)
        if not widget_frame and len(frames) > 1:
            widget_frame = frames[-1]

        # Hook into widget frame for failed-request detection
        if widget_frame:
            try:
                page.on("frameattached", lambda f: None)  # noop
            except Exception: pass
            # Page-level requestfailed should already cover widget frame requests since
            # they're subresources of the top page. Skip per-frame hook.

        if not widget_frame:
            print("No widget frame found! Frames:", [f.url for f in frames])
            browser.close()
            return

        print(f"Widget frame: {widget_frame.url}")
        # Wait for widget boot
        time.sleep(2)

        # Test 1: Does SR exist in iframe?
        sr_check = widget_frame.evaluate("""() => {
            return {
                hasSR: !!window.SpeechRecognition,
                hasWebkitSR: !!window.webkitSpeechRecognition,
                hasMediaDevices: !!navigator.mediaDevices,
                hasGetUserMedia: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
                isSecure: window.isSecureContext,
                protocol: location.protocol,
                host: location.host,
                permissionsApi: !!navigator.permissions,
                micPermission: 'unknown'
            };
        }""")
        print(f"SR check: {sr_check}")

        # Test 2: Check navigator.permissions for microphone
        try:
            perm_state = widget_frame.evaluate("""async () => {
                try {
                    const r = await navigator.permissions.query({name: 'microphone'});
                    return {state: r.state, error: null};
                } catch (e) {
                    return {state: null, error: e.message};
                }
            }""")
            print(f"navigator.permissions microphone state: {perm_state}")
        except Exception as e:
            print(f"permissions query error: {e}")

        # Test 3: Monkey-patch recognition.onerror to capture the error
        widget_frame.evaluate("""() => {
            window.__micErrorLog = [];
            const orig = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!orig) { window.__micErrorLog.push('NO_SR_API'); return; }
            // Wrap constructor
            const wrap = function(...args) {
                const inst = new orig(...args);
                const origOnError = inst.onerror;
                Object.defineProperty(inst, 'onerror', {
                    set(fn) { inst.__userOnError = fn; },
                    get() { return inst.__userOnError; }
                });
                inst.addEventListener('error', (e) => {
                    window.__micErrorLog.push({
                        error: e.error,
                        message: e.message,
                        time: Date.now()
                    });
                });
                return inst;
            };
            window.SpeechRecognition = wrap;
            if (window.webkitSpeechRecognition) window.webkitSpeechRecognition = wrap;
        }""")

        # Test 4: Click the mic button (with wait for visibility)
        try:
            # First, deep-inspect the DOM to find why #btn-mic isn't found
            dom = widget_frame.evaluate("""() => {
                const all = document.querySelectorAll('button, [id*="btn"], [id*="mic"]');
                const out = [];
                all.forEach(el => out.push({
                    tag: el.tagName,
                    id: el.id,
                    cls: el.className,
                    display: getComputedStyle(el).display,
                    visible: el.offsetParent !== null,
                    text: (el.textContent || '').trim().slice(0, 40)
                }));
                return out;
            }""")
            print(f"\nAll buttons/btn-like elements in widget frame ({len(dom)}):")
            for d in dom[:20]:
                try:
                    safe = {}
                    for k, v in d.items():
                        try:
                            safe[k] = v.encode('ascii', 'replace').decode('ascii') if isinstance(v, str) else v
                        except Exception:
                            safe[k] = repr(v)[:60]
                    print(f"  tag={safe['tag']} id={safe['id']!r} cls={safe['cls']!r} display={safe['display']!r} visible={safe['visible']} text={safe['text']!r}")
                except Exception as ex:
                    print(f"  (unprintable: {ex})")

            mic_btn = widget_frame.locator('#btn-mic')
            print(f"Mic button count (before wait): {mic_btn.count()}")
            if mic_btn.count() == 0:
                # Widget may not be booted yet, wait longer
                print("Waiting up to 15s for btn-mic to appear...")
                try:
                    widget_frame.locator('#btn-mic').first.wait_for(state='visible', timeout=15000)
                except Exception as e:
                    print(f"btn-mic never appeared: {e}")
            print(f"Mic button count (after wait): {mic_btn.count()}")
            if mic_btn.count() > 0:
                mic_btn.first.click(force=True)
                print("Clicked mic button (force)")
            else:
                print("Cannot click - btn-mic not found in widget frame")
        except Exception as e:
            print(f"Click error: {e}")

        # Wait for bubble / error event
        time.sleep(5)

        # Test 5: Read mic error log
        err_log = widget_frame.evaluate("() => window.__micErrorLog || []")
        print(f"Captured mic errors: {err_log}")

        # Test 6: Read bubble text (with safe encode)
        try:
            bubble = widget_frame.evaluate("() => document.getElementById('bubble')?.textContent || '(no bubble)'")
            try:
                bubble_safe = bubble.encode('ascii', 'replace').decode('ascii')
            except Exception:
                bubble_safe = repr(bubble)
            print(f"Bubble text: {bubble_safe}")
            bubble_classes = widget_frame.evaluate("() => document.getElementById('bubble')?.className || ''")
            print(f"Bubble classes: {bubble_classes}")
            bubble_show = widget_frame.evaluate("() => document.getElementById('bubble')?.classList.contains('show') || false")
            print(f"Bubble has 'show' class: {bubble_show}")
        except Exception as e:
            print(f"Bubble read error: {e}")

        # Test 7: Console log dump
        print(f"\n--- Console logs ({len(console_logs)}) ---")
        for kind, text in console_logs[-30:]:
            try:
                snippet = text[:200]
                snippet = snippet.encode('ascii', 'replace').decode('ascii')
                print(f"  [{kind}] {snippet}")
            except Exception as e:
                print(f"  [{kind}] <unprintable: {type(e).__name__}>")

        # Test 7b: Failed network requests
        print(f"\n--- Failed network requests ({len(failed_requests)}) ---")
        for fr in failed_requests[:20]:
            try:
                url = fr['url'].encode('ascii', 'replace').decode('ascii')
                fail = str(fr.get('failure', '')).encode('ascii', 'replace').decode('ascii')
                print(f"  {fr['method']} {url}  (failure: {fail})")
            except Exception as e:
                print(f"  (unprintable: {e})")

        # Take a screenshot
        try:
            shot_path = f"C:\\Users\\kitap\\.openclaw\\workspace\\live2d-fork\\smoke_{label.replace(' ', '_').lower()}.png"
            page.screenshot(path=shot_path, full_page=False)
            print(f"Screenshot: {shot_path}")
        except Exception as e:
            print(f"Screenshot error: {e}")

        browser.close()


if __name__ == "__main__":
    # Mobile mode test (iPhone 12 Pro style)
    iphone = {
        'width': 390, 'height': 844
    }
    iphone_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"

    # Android Chrome (Pixel 5 style)
    pixel = {
        'width': 393, 'height': 851
    }
    pixel_ua = "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"

    # Desktop Chrome
    desktop = {
        'width': 1280, 'height': 720
    }
    desktop_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    # Run mobile + desktop (skip iOS Safari since SR is unsupported, would just confirm the hint)
    run_test(pixel, pixel_ua, "android_chrome")
    run_test(desktop, desktop_ua, "desktop_chrome")
