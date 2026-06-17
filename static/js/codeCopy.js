// codeCopy.js – adds copy buttons to code blocks and handles copy to clipboard

(function () {
  function addCopyButton(block) {
    // Avoid duplicate button
    if (block.querySelector('.copy-btn')) return;
    const btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.type = 'button';
    btn.textContent = 'Copy';
    btn.addEventListener('click', () => {
      const code = block.querySelector('code');
      if (!code) return;
      const text = code.innerText;
      // Use Clipboard API with fallback
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
          const orig = btn.textContent;
          btn.textContent = '已複製 ✓';
          setTimeout(() => (btn.textContent = orig), 1800);
        }).catch(() => fallbackCopy(text, btn));
      } else {
        fallbackCopy(text, btn);
      }
    });
    block.appendChild(btn);
  }

  function fallbackCopy(text, btn) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed'; // avoid scrolling to bottom
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    try {
      document.execCommand('copy');
      const orig = btn.textContent;
      btn.textContent = '已複製 ✓';
      setTimeout(() => (btn.textContent = orig), 1800);
    } catch (e) {
      console.warn('[codeCopy] copy failed', e);
    }
    document.body.removeChild(textarea);
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.code-block').forEach(addCopyButton);
  });
})();
