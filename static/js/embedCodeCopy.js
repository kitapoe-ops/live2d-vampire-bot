// embedCodeCopy.js – copy embed snippet to clipboard for one‑line integration

(function () {
  function copyEmbedCode() {
    const codeEl = document.getElementById('embed-code-snippet');
    if (!codeEl) return;
    const text = codeEl.innerText.trim();
    // Use Clipboard API with fallback
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        showCopyLabel('已複製 ✓');
      }).catch(() => fallbackCopy(text));
    } else {
      fallbackCopy(text);
    }
  }

  function fallbackCopy(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    document.body.appendChild(textarea);
    textarea.select();
    try {
      document.execCommand('copy');
      showCopyLabel('已複製 ✓');
    } catch (e) {
      console.warn('[embedCodeCopy] copy failed', e);
    }
    document.body.removeChild(textarea);
  }

  function showCopyLabel(message) {
    const label = document.getElementById('copy-label');
    if (!label) return;
    const original = label.innerHTML;
    label.innerHTML = message;
    setTimeout(() => { label.innerHTML = original; }, 1800);
  }

  // Expose globally for button onclick
  window.copyEmbedCode = copyEmbedCode;
})();
