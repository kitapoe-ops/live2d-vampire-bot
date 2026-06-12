/* =====================================================================
 * embed.js ??AI ?›æ“¬äººå??¥è??¥å™¨
 * BAZOOKA / vampire.kitahim.uk adaption of YuriCrystal/ai-avatar-bot
 * Source: https://raw.githubusercontent.com/YuriCrystal/ai-avatar-bot/main/embed.js
 *
 * Usage on any website:
 *   <script src="https://vampire.kitahim.uk/static/embed/embed.js"
 *     data-model="https://vampire.kitahim.uk/static/live2d/vampire/%E5%90%B8%E8%A1%80%E9%AC%BC.model3.json"
 *     data-knowledge="https://vampire.kitahim.uk/static/embed/knowledge.js"
 *     data-api="/api/tts"></script>
 *
 * Defaults:
 *   data-model     -> vampire model on vampire.kitahim.uk
 *   data-knowledge -> <embed.js base>/knowledge.js
 *   data-api       -> '/api/tts' (absolute path, avoids static-dir 404 trap)
 * ===================================================================== */
(function () {
  'use strict';

  // Inject collapse-bubble hover / pulse animation
  var awStyle = document.createElement('style');
  awStyle.textContent =
    '#avatar-widget-root .aw-bubble{transition:transform .15s, box-shadow .15s;}'
    + '#avatar-widget-root .aw-bubble:hover{transform:scale(1.07);}'
    + '#avatar-widget-root .aw-bubble:active{transform:scale(.95);}'
    + '#avatar-widget-root .aw-bubble:focus-visible{outline:3px solid rgba(91,84,232,.45);outline-offset:3px;}'
    + '#avatar-widget-root .aw-bubble::after{content:"";position:absolute;inset:0;border-radius:50%;animation:awpulse 2.2s ease-out infinite;pointer-events:none;}'
    + '@keyframes awpulse{0%{box-shadow:0 0 0 0 rgba(91,84,232,.5);}70%{box-shadow:0 0 0 13px rgba(91,84,232,0);}100%{box-shadow:0 0 0 0 rgba(91,84,232,0);}}';
  (document.head || document.documentElement).appendChild(awStyle);

  // Locate our position to derive widget.html URL
  var me = document.currentScript || (function () {
    var ss = document.getElementsByTagName('script');
    for (var i = ss.length - 1; i >= 0; i--) { if (/embed\.js(\?|$)/.test(ss[i].src || '')) return ss[i]; }
    return null;
  })();
  var base = me ? me.src.replace(/[^/]*$/, '') : '';
  var widgetUrl = (me && me.getAttribute('data-widget')) || (base + 'widget.html');
  // Cache-bust: append build version to force browser to fetch latest widget.html
  // (bypass any Cloudflare/browser cache that may hold stale polling code)
  var _buildV = '20260612v03';
  if (widgetUrl.indexOf('?') < 0) widgetUrl += '?v=' + _buildV;
  else widgetUrl += '&v=' + _buildV;
  var startOpen = (me && me.getAttribute('data-open') !== 'false');
  var widgetOrigin = (function () { try { return new URL(widgetUrl, location.href).origin; } catch (e) { return '*'; } })();

  // Forward config: skin (model), backend (api), content (knowledge), voice
  var cfg = new URLSearchParams();
  ['model', 'api', 'knowledge', 'voice'].forEach(function (k) {
    var v = me && me.getAttribute('data-' + k);
    if (v) cfg.set(k, v);
  });
  // Default to vampire model. If running locally on localhost/127.0.0.1, use relative path to prevent CORS issues.
  if (!cfg.has('model')) {
    var isLocal = (location.hostname === 'localhost' || location.hostname === '127.0.0.1');
    if (isLocal) {
      cfg.set('model', '/static/live2d/vampire/' + encodeURIComponent('?¸è?é¬?) + '.model3.json');
    } else {
      cfg.set('model', 'https://vampire.kitahim.uk/static/live2d/vampire/' + encodeURIComponent('?¸è?é¬?) + '.model3.json');
    }
  }
  if (!cfg.has('knowledge')) {
    cfg.set('knowledge', base + 'knowledge.js');
  }
  // Always add cache-bust to knowledge.js (it's the most-changed file)
  var _kUrl = cfg.get('knowledge');
  if (_kUrl && _kUrl.indexOf('v=') < 0) cfg.set('knowledge', _kUrl + (_kUrl.indexOf('?') < 0 ? '?v=' : '&v=') + '20260611v13');
  // Default TTS endpoint to absolute /api/tts (avoid 404 from relative path
  // resolution into the static /static/embed/ directory). This is the critical
  // path that the user-facing 3rd-party widget sites will use.
  if (!cfg.has('api')) {
    cfg.set('api', '/api/tts');
  }
  var cfgQs = cfg.toString();
  var iframeSrc = widgetUrl + (cfgQs ? (widgetUrl.indexOf('?') < 0 ? '?' : '&') + cfgQs : '');

  var EXPANDED = { w: 340, h: 480 };
  var NS_OUT = 'avatar-widget-host';
  var NS_IN  = 'avatar-widget';

  // Outer container
  var root = document.createElement('div');
  root.id = 'avatar-widget-root';
  root.style.cssText = [
    'position:fixed', 'right:16px', 'bottom:16px',
    'z-index:2147483000', 'width:' + EXPANDED.w + 'px', 'height:' + EXPANDED.h + 'px'
  ].join(';');

  // iframe
  var iframe = document.createElement('iframe');
  iframe.src = iframeSrc;
  iframe.title = 'AI ?›æ“¬äººåŠ©??;
  iframe.setAttribute('allow', 'microphone; autoplay');
  iframe.setAttribute('allowtransparency', 'true');
  iframe.style.cssText = 'width:100%;height:100%;border:0;background:transparent;color-scheme:normal;';

  // Collapse bubble
  var bubble = document.createElement('button');
  bubble.type = 'button';
  bubble.className = 'aw-bubble';
  bubble.setAttribute('aria-label', '?‹å? AI ?›æ“¬äººåŠ©??);
  bubble.setAttribute('title', '?‹å? AI ?›æ“¬äººåŠ©??);
  bubble.textContent = '?’¬';
  bubble.style.cssText = [
    'position:absolute', 'right:2px', 'bottom:2px', 'width:64px', 'height:64px',
    'border:0', 'border-radius:50%', 'cursor:pointer', 'font-size:28px',
    'background:linear-gradient(135deg,#7d78f0,#5b54e8)', 'color:#fff',
    'box-shadow:0 8px 22px rgba(0,0,0,.3)',
    'display:none', 'align-items:center', 'justify-content:center'
  ].join(';');

  root.appendChild(iframe);
  root.appendChild(bubble);
  (document.body || document.documentElement).appendChild(root);

  function setOpen(open) {
    if (open) {
      root.style.width = EXPANDED.w + 'px';
      root.style.height = EXPANDED.h + 'px';
      iframe.style.display = 'block';
      bubble.style.display = 'none';
    } else {
      root.style.width = '60px';
      root.style.height = '60px';
      iframe.style.display = 'none';
      bubble.style.display = 'flex';
    }
  }

  // Set initial state
  setOpen(startOpen);
  if (startOpen) { try { iframe.focus(); } catch (e) {} }

  // Bubble click -> open
  bubble.addEventListener('click', function () { setOpen(true); try { iframe.focus(); } catch (e) {} });
  bubble.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setOpen(true); } });

  // Track iframe-loaded so postMessage is safe
  var ready = false;
  iframe.addEventListener('load', function () { ready = true; });

  // Forward close requests from iframe
  window.addEventListener('message', function (e) {
    var d = e.data || {};
    if (d.ns !== NS_IN) return;
    if (d.type === 'close' || d.type === 'collapse') { setOpen(false); }
    if (d.type === 'open') { setOpen(true); }
  });

  // Public API
  window.AvatarWidget = {
    open: function () { setOpen(true); },
    close: function () { setOpen(false); },
    say: function (text) {
      try {
        if (ready && iframe.contentWindow) {
          iframe.contentWindow.postMessage({ ns: NS_OUT, type: 'say', text: String(text || '') }, widgetOrigin || '*');
        } else {
          setTimeout(function () {
            try { iframe.contentWindow.postMessage({ ns: NS_OUT, type: 'say', text: String(text || '') }, widgetOrigin || '*'); } catch (e) {}
          }, 500);
        }
      } catch (e) {}
    }
  };
})();
