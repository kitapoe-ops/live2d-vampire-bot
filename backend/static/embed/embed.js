/* =====================================================================
 * embed.js — AI 虛擬人嵌入載入器
 * BAZOOKA / vampire.kitahim.uk adaption of YuriCrystal/ai-avatar-bot
 * Source: https://raw.githubusercontent.com/YuriCrystal/ai-avatar-bot/main/embed.js
 *
 * Usage on any website:
 *   <script src="https://vampire.kitahim.uk/static/embed/embed.js"
 *     data-model="https://vampire.kitahim.uk/static/live2d/vampire/vampire.model3.json"
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

  // 2026-06-17: Prevent duplicate widget instances
  if (document.getElementById('avatar-widget-root')) {
    console.warn('[embed.js] Widget already loaded, skipping duplicate instance');
    return;
  }

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
  var widgetUrl = (me && me.getAttribute('data-widget')) || (base + 'widget_fixed.html');
  // Cache-bust: append build version to force browser to fetch latest widget.html
  // (bypass any Cloudflare/browser cache that may hold stale polling code)
  // 2026-06-17 v45-FORCE: load widget_fixed.html instead of widget.html
  var _buildV = '20260621v48';
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
  // 2026-06-16 v42: use 'vampire.model3.json' instead of the Chinese filename
  // '吸血鬼.model3.json' because the deployed server only has the ASCII filename.
  if (!cfg.has('model')) {
    var isLocal = (location.hostname === 'localhost' || location.hostname === '127.0.0.1');
    if (isLocal) {
      cfg.set('model', '/static/live2d/vampire/vampire.model3.json');
    } else {
      cfg.set('model', 'https://vampire.kitahim.uk/static/live2d/vampire/vampire.model3.json');
    }
  }
  if (!cfg.has('knowledge')) {
    cfg.set('knowledge', base + 'knowledge.js');
  }
  // Always add cache-bust to knowledge.js (it's the most-changed file)
  var _kUrl = cfg.get('knowledge');
  if (_kUrl) cfg.set('knowledge', _kUrl + (_kUrl.indexOf('?') < 0 ? '?v=' : '&v=') + '20260621v46');
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
  iframe.title = 'AI 虛擬人助理';
  // Mobile mic fix (2026-06-13): bare `microphone` covers BOTH getUserMedia
  // AND SpeechRecognition per W3C spec. The original code only listed
  // `microphone; autoplay` which was incomplete for cross-origin embeds on
  // Android Chrome. Wildcards (*) let any descendant origin use these
  // features — fine since the iframe loads our own widget.html on the same
  // domain, and 3rd-party embed sites also need mic delegation.
  // 2026-06-13 v2: drop `speech-recognition` token. Chrome console warning
  // "Unrecognized feature: 'speech-recognition'" — it's not in W3C's
  // policy-controlled features list; the `microphone` feature covers SR.
  iframe.setAttribute('allow', 'microphone *; camera *; autoplay *');
  iframe.setAttribute('allowtransparency', 'true');
  iframe.style.cssText = 'width:100%;height:100%;border:0;background:transparent;color-scheme:normal;';

  // Collapse bubble
  var bubble = document.createElement('button');
  bubble.type = 'button';
  bubble.className = 'aw-bubble';
  bubble.setAttribute('aria-label', '開啟 AI 虛擬人助理');
  bubble.setAttribute('title', '開啟 AI 虛擬人助理');
  bubble.textContent = '💬';
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

  // Track iframe-loaded so postMessage is safe.
  // 2026-06-13 v24: replace single-shot setTimeout(500) with a message queue
  // that flushes when the iframe fires its load event. The previous code
  // dropped the message if widget.html took > 500ms to init (common on
  // slow mobile networks or with cold Cloudflare cache hits), and
  // compounded multiple pre-load say() calls into a single burst on
  // the first 500ms tick.
  var ready = false;
  var messageQueue = [];
  iframe.addEventListener('load', function () {
    ready = true;
    // Flush queued messages once loaded
    while (messageQueue.length > 0) {
      var msg = messageQueue.shift();
      try {
        if (iframe.contentWindow) {
          iframe.contentWindow.postMessage(msg, widgetOrigin || '*');
        }
      } catch (eFlush) {
        // If even the flush fails, re-queue at the front so we don't lose
        // the message; the next load (e.g. on widget reload) will retry.
        messageQueue.unshift(msg);
        break;
      }
    }
  });

  // Forward close requests from iframe
  window.addEventListener('message', function (e) {
    var d = e.data || {};
    if (d.ns !== NS_IN) return;
    if (d.type === 'close' || d.type === 'collapse') { setOpen(false); }
    if (d.type === 'open') { setOpen(true); }
    // 2026-06-14 v36: widget drag-to-reposition. The widget posts
    // incremental deltas { type: 'reposition_delta', dx, dy } while
    // user drags, and host accumulates + clamps to viewport.
    if (d.type === 'reposition_delta' && typeof d.dx === 'number' && typeof d.dy === 'number') {
      // Get current position. If right/bottom is set (default), resolve to left/top first.
      var curLeft = root.style.left;
      var curTop  = root.style.top;
      if (!curLeft || curLeft === 'auto' || !curTop || curTop === 'auto') {
        // First move: capture current rect and convert from right/bottom anchor
        var rect0 = root.getBoundingClientRect();
        curLeft = rect0.left;
        curTop  = rect0.top;
        root.style.right  = 'auto';
        root.style.bottom = 'auto';
      } else {
        curLeft = parseFloat(curLeft);
        curTop  = parseFloat(curTop);
      }
      var w = parseInt(root.style.width, 10) || EXPANDED.w;
      var h = parseInt(root.style.height, 10) || EXPANDED.h;
      var nx = Math.max(0, Math.min(window.innerWidth  - w, curLeft + d.dx));
      var ny = Math.max(0, Math.min(window.innerHeight - h, curTop  + d.dy));
      root.style.left = nx + 'px';
      root.style.top  = ny + 'px';
      // Persist on every move (cheap, no debounce needed for string setItem)
      try { localStorage.setItem('xiaob_widget_pos', JSON.stringify({ x: nx, y: ny })); } catch (eP) { /* ignore */ }
    }
    // 2026-06-14 v36: absolute reposition (used by AvatarWidget.setPosition API)
    if (d.type === 'reposition' && typeof d.x === 'number' && typeof d.y === 'number') {
      var w2 = parseInt(root.style.width, 10) || EXPANDED.w;
      var h2 = parseInt(root.style.height, 10) || EXPANDED.h;
      var nx2 = Math.max(0, Math.min(window.innerWidth  - w2, d.x));
      var ny2 = Math.max(0, Math.min(window.innerHeight - h2, d.y));
      root.style.left   = nx2 + 'px';
      root.style.top    = ny2 + 'px';
      root.style.right  = 'auto';
      root.style.bottom = 'auto';
      try { localStorage.setItem('xiaob_widget_pos', JSON.stringify({ x: nx2, y: ny2 })); } catch (eP) { /* ignore */ }
    }
  });

  // 2026-06-14 v36: restore saved widget position on init.
  // If user has dragged before, position is persisted in localStorage.
  // Otherwise, default to bottom-right (set via root.style.cssText above).
  try {
    var posRaw = localStorage.getItem('xiaob_widget_pos');
    if (posRaw) {
      var pos = JSON.parse(posRaw);
      if (pos && typeof pos.x === 'number' && typeof pos.y === 'number') {
        var w2 = EXPANDED.w, h2 = EXPANDED.h;
        var px = Math.max(0, Math.min(window.innerWidth  - w2, pos.x));
        var py = Math.max(0, Math.min(window.innerHeight - h2, pos.y));
        root.style.left   = px + 'px';
        root.style.top    = py + 'px';
        root.style.right  = 'auto';
        root.style.bottom = 'auto';
      }
    }
  } catch (ePos) { /* ignore, use default */ }

  // Public API
  window.AvatarWidget = {
    open: function () { setOpen(true); },
    close: function () { setOpen(false); },
    say: function (text) {
      var payload = { ns: NS_OUT, type: 'say', text: String(text || '') };
      try {
        if (ready && iframe.contentWindow) {
          iframe.contentWindow.postMessage(payload, widgetOrigin || '*');
        } else {
          // Queue it; load handler will flush.
          messageQueue.push(payload);
        }
      } catch (e) {
        // If the synchronous postMessage throws (e.g. cross-origin
        // restriction), fall back to queue. The load handler will retry.
        messageQueue.push(payload);
      }
    },
    // 2026-06-21: Reactive answer event — triggers vampire tutoring response.
    // @param {string} text       The question / context text
    // @param {object} context    { correct, answer, question, hint? }
    //                           correct=true/false → instant emotion reply (no LLM)
    //                           correct=undefined → LLM decides (DeepSeek required)
    react: function (text, context) {
      var payload = {
        ns: NS_OUT,
        type: 'react',
        text: String(text || ''),
        context: (context && typeof context === 'object') ? context : {},
      };
      try {
        if (ready && iframe.contentWindow) {
          iframe.contentWindow.postMessage(payload, widgetOrigin || '*');
        } else {
          messageQueue.push(payload);
        }
      } catch (e) {
        messageQueue.push(payload);
      }
    },
    // 2026-06-14 v36: programmatic position control. Useful for parent
    // pages that want to position the widget relative to a specific
    // element or anchor.
    setPosition: function (x, y) {
      if (typeof x !== 'number' || typeof y !== 'number') return;
      var w = parseInt(root.style.width, 10) || EXPANDED.w;
      var h = parseInt(root.style.height, 10) || EXPANDED.h;
      var nx = Math.max(0, Math.min(window.innerWidth  - w, x));
      var ny = Math.max(0, Math.min(window.innerHeight - h, y));
      root.style.left   = nx + 'px';
      root.style.top    = ny + 'px';
      root.style.right  = 'auto';
      root.style.bottom = 'auto';
      try { localStorage.setItem('xiaob_widget_pos', JSON.stringify({ x: nx, y: ny })); } catch (eP) { /* ignore */ }
    },
    resetPosition: function () {
      try { localStorage.removeItem('xiaob_widget_pos'); } catch (eR) { /* ignore */ }
      root.style.right  = '16px';
      root.style.bottom = '16px';
      root.style.left   = 'auto';
      root.style.top    = 'auto';
    }
  };
})();
