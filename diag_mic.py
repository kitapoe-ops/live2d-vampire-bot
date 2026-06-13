#!/usr/bin/env python3
"""Add rich diagnostic dump to widget.html onerror handler for mobile mic debugging."""
from pathlib import Path
import re

p = Path(r"C:\Users\kitap\.openclaw\workspace\live2d-fork\backend\static\embed\widget.html")
text = p.read_text(encoding="utf-8")
print(f"Original: {len(text)} chars")

# Find the recognition.onerror handler block
# Pattern: recognition.onerror = (e) => { ... showBubble(hint); };
old_block = """      recognition.onerror = (e) => {
        listening = false; setMic(false);
        // Mobile-specific error guidance (2026-06-13):
        // - 'not-allowed': permission denied by user OR blocked by Permissions-Policy
        // - 'service-not-allowed': SR backend offline (rare on desktop, common on mobile)
        // - 'no-speech': user didn't speak within timeout
        let hint = '';
        if (e.error === 'not-allowed') {
          hint = '未獲授權 ??;
        } else if (e.error === 'service-not-allowed') {
          hint = '';
        } else if (e.error === 'no-speech') {
          hint = '';
        } else {
          hint = '';
        }
        showBubble(hint);
      };""".replace("??", "🎙️")

# Just check that the block exists in some form
# The actual file has garbled text from console codepage, so use a regex
m = re.search(
    r"recognition\.onerror\s*=\s*\(e\)\s*=>\s*\{(.*?)\n\s*\};",
    text,
    re.DOTALL
)
if not m:
    print("FAIL: recognition.onerror block not found via regex")
    # Try a looser match
    idx = text.find("recognition.onerror")
    if idx == -1:
        print("FAIL: 'recognition.onerror' literal not in file at all")
        raise SystemExit(1)
    print(f"But 'recognition.onerror' at offset {idx}. Showing 600 chars:")
    print(repr(text[idx:idx+600]))
    raise SystemExit(1)

print("Found onerror block, current content (200 chars):")
print(repr(m.group(0)[:200]))
print("...")
print(repr(m.group(0)[-200:]))

# Replace with diagnostic-rich version
new_block = """      recognition.onerror = (e) => {
        listening = false; setMic(false);
        // Mobile-specific error guidance (2026-06-13):
        // - 'not-allowed': permission denied by user OR blocked by Permissions-Policy
        // - 'service-not-allowed': SR backend offline (rare on desktop, common on mobile)
        // - 'no-speech': user didn't speak within timeout
        // 2026-06-13 v3: rich diagnostic dump — log e.error, e.message, UA, permission state,
        // iframe allow attribute, host page location to console + localStorage.
        // Goal: identify whether the 'not-allowed' on Android Chrome is:
        //   (A) site-level mic permission denied, OR
        //   (B) Android OS Google App mic permission denied, OR
        //   (C) SpeechRecognition backend offline (network / Google App issue)
        const _diag = {
          ts: new Date().toISOString(),
          event_error: e.error || '(none)',
          event_message: e.message || '(none)',
          ua: navigator.userAgent,
          url: location.href,
          is_secure: location.protocol === 'https:',
          has_SR: !!window.SpeechRecognition,
          has_webkitSR: !!window.webkitSpeechRecognition,
          has_mediaDevices: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
          is_embedded: window.self !== window.top,
        };
        // Async permission check (best effort)
        if (navigator.permissions && navigator.permissions.query) {
          navigator.permissions.query({ name: 'microphone' }).then(p => {
            _diag.perm_mic_state = p.state;
            console.error('[mic-diagnostic]', JSON.stringify(_diag, null, 2));
            try { localStorage.setItem('xiaob_mic_diag', JSON.stringify(_diag)); } catch (er) {}
          }).catch(er => {
            _diag.perm_mic_error = String(er);
            console.error('[mic-diagnostic]', JSON.stringify(_diag, null, 2));
            try { localStorage.setItem('xiaob_mic_diag', JSON.stringify(_diag)); } catch (er2) {}
          });
        } else {
          console.error('[mic-diagnostic]', JSON.stringify(_diag, null, 2));
          try { localStorage.setItem('xiaob_mic_diag', JSON.stringify(_diag)); } catch (er) {}
        }
        let hint = '';
        if (e.error === 'not-allowed') {
          hint = '未獲授權 ??;
        } else if (e.error === 'service-not-allowed') {
          hint = '';
        } else if (e.error === 'no-speech') {
          hint = '';
        } else {
          hint = '';
        }
        showBubble(hint);
      };""".replace("??", "🎙️")

new_text = text.replace(m.group(0), new_block, 1)
if new_text == text:
    print("FAIL: text unchanged after replace")
    raise SystemExit(1)

p.write_text(new_text, encoding="utf-8")
print(f"Wrote: {len(new_text)} chars (delta +{len(new_text)-len(text)})")
print("First 200 chars of new block:")
idx = new_text.find("recognition.onerror")
print(repr(new_text[idx:idx+200]))
