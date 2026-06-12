import os

path = 'backend/static/embed/widget.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# -------------------------------------------------------------
# 1. Update CSS to share styles between #voice-list and #emote-list
# -------------------------------------------------------------
css_target = """/* ===== Voice list popover (anchored to btn-voice) ===== */
#voice-list {
  position:absolute; left:8px; right:8px; bottom:calc(100% + 8px);
  background:var(--surface); color:var(--ink);
  border-radius:14px; padding:6px;
  box-shadow:0 10px 30px rgba(0,0,0,.22), inset 0 0 0 1px rgba(91,84,232,.18);
  max-height:50vh; overflow-y:auto; z-index:99;
  display:none;   /* toggled by .open */
}
#voice-list.open { display:block; }
#voice-list .vl-header {
  font-size:12px; font-weight:600; color:#666; padding:6px 10px 4px;
  border-bottom:1px solid #eef0f4; margin-bottom:4px;
  display:flex; justify-content:space-between; align-items:center;
}
#voice-list .vl-empty {
  padding:14px 10px; text-align:center; font-size:12px; color:#888;
}
#voice-list .vl-item {
  display:flex; flex-direction:column; gap:1px;
  padding:8px 10px; border-radius:9px; cursor:pointer;
  font-size:13.5px; line-height:1.3;
}
#voice-list .vl-item:hover { background:rgba(91,84,232,.08); }
#voice-list .vl-item.active { background:linear-gradient(135deg,var(--brand-2),var(--brand)); color:#fff; }
#voice-list .vl-item .vl-name { font-weight:600; }
#voice-list .vl-item .vl-id { font-size:11px; opacity:.65; font-family:ui-monospace,monospace; }
#voice-list .vl-item.active .vl-id { opacity:.85; }
#voice-list .vl-section {
  font-size:11px; font-weight:700; color:var(--brand);
  padding:10px 10px 4px; letter-spacing:.3px;
  text-transform:uppercase;
}"""

css_replacement = """/* ===== Popover list styles (Voice & Emote) ===== */
#voice-list, #emote-list {
  position:absolute; left:8px; right:8px; bottom:calc(100% + 8px);
  background:var(--surface); color:var(--ink);
  border-radius:14px; padding:6px;
  box-shadow:0 10px 30px rgba(0,0,0,.22), inset 0 0 0 1px rgba(91,84,232,.18);
  max-height:50vh; overflow-y:auto; z-index:99;
  display:none;   /* toggled by .open */
}
#voice-list.open, #emote-list.open { display:block; }
#voice-list .vl-header, #emote-list .vl-header {
  font-size:12px; font-weight:600; color:#666; padding:6px 10px 4px;
  border-bottom:1px solid #eef0f4; margin-bottom:4px;
  display:flex; justify-content:space-between; align-items:center;
}
#voice-list .vl-empty, #emote-list .vl-empty {
  padding:14px 10px; text-align:center; font-size:12px; color:#888;
}
#voice-list .vl-item, #emote-list .vl-item {
  display:flex; flex-direction:column; gap:1px;
  padding:8px 10px; border-radius:9px; cursor:pointer;
  font-size:13.5px; line-height:1.3;
}
#voice-list .vl-item:hover, #emote-list .vl-item:hover { background:rgba(91,84,232,.08); }
#voice-list .vl-item.active, #emote-list .vl-item.active { background:linear-gradient(135deg,var(--brand-2),var(--brand)); color:#fff; }
#voice-list .vl-item .vl-name, #emote-list .vl-item .vl-name { font-weight:600; }
#voice-list .vl-item .vl-id, #emote-list .vl-item .vl-id { font-size:11px; opacity:.65; font-family:ui-monospace,monospace; }
#voice-list .vl-item.active .vl-id, #emote-list .vl-item.active .vl-id { opacity:.85; }
#voice-list .vl-section, #emote-list .vl-section {
  font-size:11px; font-weight:700; color:var(--brand);
  padding:10px 10px 4px; letter-spacing:.3px;
  text-transform:uppercase;
}"""

# -------------------------------------------------------------
# 2. Update HTML to insert #emote-list next to #voice-list
# -------------------------------------------------------------
html_target = '<div id="voice-list" role="listbox" aria-label="語音"></div>'
html_replacement = """<div id="voice-list" role="listbox" aria-label="語音"></div>
  <div id="emote-list" role="listbox" aria-label="表情選擇"></div>"""

# -------------------------------------------------------------
# 3. Add canvas click listener for interactive motion reaction
# -------------------------------------------------------------
canvas_click_target = """  canvasEl.addEventListener('pointermove', (e) => {
    hasMouseInput = true;
    mouseX = e.clientX;
    mouseY = e.clientY;
  });"""

canvas_click_replacement = """  canvasEl.addEventListener('pointermove', (e) => {
    hasMouseInput = true;
    mouseX = e.clientX;
    mouseY = e.clientY;
  });
  canvasEl.addEventListener('click', () => {
    if (model && typeof model.motion === 'function') {
      try {
        model.motion('Scene1');
        console.log('[Live2D] Play clicked reaction motion: Scene1');
      } catch (e) {
        console.warn('[Live2D] Failed to play Scene1 motion:', e);
      }
    }
  });"""

# -------------------------------------------------------------
# 4. Update Ticker to sway dynamically when speaking
# -------------------------------------------------------------
ticker_target = """  // 身體晃動 (PARAM_BODY_ANGLE_X/Y)
  const bodySwayX = Math.sin(t * 0.4) * 2.5; // -2.5 到 2.5 度的擺動
  const bodySwayY = Math.cos(t * 0.3) * 1.5;
  safeSetParam('PARAM_BODY_ANGLE_X', bodySwayX);
  safeSetParam('PARAM_BODY_ANGLE_Y', bodySwayY);"""

ticker_replacement = """  // 身體與肩膀晃動 (PARAM_BODY_ANGLE_X/Y/Z, PARAM_shoulder)
  let bodySwayX = Math.sin(t * 0.4) * 2.5;
  let bodySwayY = Math.cos(t * 0.3) * 1.5;
  if (isSpeaking) {
    // 說話時增加晃動幅度和頻率，讓身體顯得生動
    bodySwayX += Math.sin(t * 3.0) * 3.5;
    bodySwayY += Math.cos(t * 2.5) * 2.0;
    safeSetParam('PARAM_BODY_ANGLE_Z', Math.sin(t * 2.0) * 2.0);
    safeSetParam('PARAM_shoulder', Math.sin(t * 4.0) * 3.5);
  } else {
    safeSetParam('PARAM_BODY_ANGLE_Z', 0.0);
    safeSetParam('PARAM_shoulder', 0.0);
  }
  safeSetParam('PARAM_BODY_ANGLE_X', bodySwayX);
  safeSetParam('PARAM_BODY_ANGLE_Y', bodySwayY);"""

# -------------------------------------------------------------
# Apply text replacements
# -------------------------------------------------------------
def apply_replace(src, tgt, rpl, label):
    if tgt in src:
        src = src.replace(tgt, rpl)
        print(f"[{label}] LF matching successful.")
    else:
        tgt_crlf = tgt.replace('\n', '\r\n')
        rpl_crlf = rpl.replace('\n', '\r\n')
        if tgt_crlf in src:
            src = src.replace(tgt_crlf, rpl_crlf)
            print(f"[{label}] CRLF matching successful.")
        else:
            print(f"[{label}] ERROR: Target not found.")
    return src

content = apply_replace(content, css_target, css_replacement, "CSS")
content = apply_replace(content, html_target, html_replacement, "HTML")
content = apply_replace(content, canvas_click_target, canvas_click_replacement, "Canvas Click")
content = apply_replace(content, ticker_target, ticker_replacement, "Ticker")

# -------------------------------------------------------------
# 5. Replace applyEmotion and btn-emote cycle logic with a state manager + popover
# -------------------------------------------------------------
# Let's read patch_widget.py to see where applyEmotion starts. It's around line 1114.
# We will replace everything from window.applyEmotion down to the end of the btnEmote event listener
# Let's inspect where btnEmote is used. It ends at line 1144:
#   });
#   }
#   });
js_target = """      window.applyEmotion = function(name) { // 提至全域供狀態機外部鏈路調用
        if (!window.KNOWLEDGE) { console.warn('[emotion] no KNOWLEDGE'); return; }
        const preset = EMOTION_PRESETS[name];
        if (!preset) { console.warn('[emotion] unknown:', name); return; }
        const r = window.KNOWLEDGE.bulkSet(preset);
        currentEmotion = name;

        // 呼叫 Live2D 原生表情系統播放對應的 exp3.json
        if (typeof model !== 'undefined' && model && typeof model.expression === 'function') {
          const expMap = {
            sad: 'sad',
            shy: 'shy',
            angry: 'mad',
            happy: 'hearteyes',
            surprised: 'circleeyes',
            neutral: 'vampire' // vampire 是預設服裝與正常表情
          };
          const expName = expMap[name];
          if (expName) {
            try {
              model.expression(expName);
              console.log('[Live2D] Played native expression: ' + expName);
            } catch (e) {
              console.warn('[Live2D] Failed to play native expression:', e);
            }
          }
        }

        console.log('[emotion] ' + name + ' => ok=' + r.ok + ' failed=' + r.failed);
        showBubble('表情：' + (EMOTION_LABELS[name] || name));
      }

      const btnEmote = document.getElementById('btn-emote');
      if (btnEmote) {
        let emoIdx = 0;
        btnEmote.addEventListener('click', () => {
          emoIdx = (emoIdx + 1) % EMOTION_KEYS.length;
          applyEmotion(EMOTION_KEYS[emoIdx]);
        });
      }
      document.addEventListener('keydown', (e) => {
        if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) return;
        const k = e.key;
        if (k >= '0' && k <= '7') {
          if (k === '0') {
            const pick = EMOTION_KEYS[Math.floor(Math.random() * EMOTION_KEYS.length)];
            applyEmotion(pick);
          } else {
            const idx = parseInt(k, 10) - 1;
            if (idx >= 0 && idx < EMOTION_KEYS.length) applyEmotion(EMOTION_KEYS[idx]);
          }
        }
      });"""

js_replacement = """      // 統一表情與型態狀態管理器
      const activeStates = {
        outfit: 'black', // 'black' | 'white'
        hand: 'normal',  // 'normal' | 'mc' | 'knife' | 'mouse'
        blush: false,
        sad: false,
        angry: false,
        hearteyes: false,
        stareyes: false,
        circleeyes: false,
        bloodFace: false,
        bloodBody: false
      };

      function updateModelParameters() {
        const map = {};

        // 1. 服裝與頭髮形態 (vampire=黑衣, vampire2=白衣)
        if (activeStates.outfit === 'white') {
          map['PARAMoutfit1_2'] = 0.0;
          map['PARAMhariWB'] = 0.0;
          map['PARAMhariWB2'] = 1.0;
          map['PARAMhari_3'] = 0.0;
          map['PARAMhari_4'] = 0.0;
        } else {
          map['PARAMoutfit1_2'] = 1.0;
          map['PARAMhariWB'] = 1.0;
          map['PARAMhariWB2'] = 0.0;
          map['PARAMhari_3'] = 1.0;
          map['PARAMhari_4'] = 1.0;
        }

        // 2. 手勢形態 (mc=拿麥克風, knife=拿刀, mouse=拿老鼠, normal=無手勢)
        map['PARAMhands_1'] = activeStates.hand === 'mc' ? 1.0 : 0.0;
        map['PARAMhands_2'] = activeStates.hand === 'knife' ? 1.0 : 0.0;
        map['PARAMhands_3'] = activeStates.hand === 'mouse' ? 1.0 : 0.0;

        // 3. 眼神與表情 (blush=害羞臉紅, hearteyes=愛心眼, stareyes=星星眼, circleeyes=旋轉眩暈)
        map['PARAMSHY'] = activeStates.blush ? 1.0 : 0.0;
        map['PARAMhearteye'] = activeStates.hearteyes ? 1.0 : 0.0;
        map['PARAMstareye'] = activeStates.stareyes ? 1.0 : 0.0;
        map['PARAMWHITEEYE'] = activeStates.circleeyes ? 1.0 : 0.0;

        // 淚痕與眉毛 (sad)
        if (activeStates.sad) {
          map['PARAMTEARS'] = 1.0;
          map['PARAM_BROW_L_Y'] = -0.8;
          map['PARAM_BROW_R_Y'] = -0.8;
          map['PARAM_BROW_L_FORM'] = -0.8;
          map['PARAM_BROW_R_FORM'] = -0.8;
        } else {
          map['PARAMTEARS'] = 0.0;
        }

        // 生氣眉毛 (angry)
        if (activeStates.angry) {
          map['PARAMANGRY'] = 1.0;
          map['PARAM_BROW_L_Y'] = 0.4;
          map['PARAM_BROW_R_Y'] = 0.4;
          map['PARAM_BROW_L_FORM'] = -0.7;
          map['PARAM_BROW_R_FORM'] = -0.7;
        } else if (!activeStates.sad) {
          map['PARAMANGRY'] = 0.0;
          map['PARAM_BROW_L_Y'] = 0.0;
          map['PARAM_BROW_R_Y'] = 0.0;
          map['PARAM_BROW_L_FORM'] = 0.0;
          map['PARAM_BROW_R_FORM'] = 0.0;
        }

        // 4. 血跡疊加
        map['PARAMBLOOD2'] = activeStates.bloodFace ? 1.0 : 0.0;
        map['PARAMblood1'] = activeStates.bloodBody ? 1.0 : 0.0;

        if (window.KNOWLEDGE) {
          window.KNOWLEDGE.bulkSet(map);
        }
      }

      window.applyEmotion = function(name) { // 提至全域供狀態機外部鏈路調用
        if (!window.KNOWLEDGE) { console.warn('[emotion] no KNOWLEDGE'); return; }
        
        // 重置所有暫時性的表情眼神疊加（保持服裝與手勢不變）
        activeStates.blush = false;
        activeStates.sad = false;
        activeStates.angry = false;
        activeStates.hearteyes = false;
        activeStates.stareyes = false;
        activeStates.circleeyes = false;

        if (name === 'happy') {
          activeStates.hearteyes = true;
        } else if (name === 'sad') {
          activeStates.sad = true;
        } else if (name === 'angry') {
          activeStates.angry = true;
        } else if (name === 'surprised') {
          activeStates.circleeyes = true;
        } else if (name === 'shy') {
          activeStates.blush = true;
        }

        updateModelParameters();
        currentEmotion = name;
        console.log('[emotion] ' + name + ' applied via activeStates');
        showBubble('表情：' + (EMOTION_LABELS[name] || name));
        
        // 重新繪製表情選單（如果打開著）
        const elPopover = document.getElementById('emote-list');
        if (elPopover && elPopover.classList.contains('open')) renderEmoteList();
      }

      // 表情與形態下拉選單 logic
      (function() {
        const btn = document.getElementById('btn-emote');
        const popover = document.getElementById('emote-list');

        function renderEmoteList() {
          popover.innerHTML = '';

          // 標題
          const header = document.createElement('div');
          header.className = 'vl-header';
          header.innerHTML = '<span>吸血鬼表情與形態切換</span><span style="font-size:11px;opacity:.7;">🧛 settings</span>';
          popover.appendChild(header);

          // 1. 表情與眼神組
          const secFace = document.createElement('div');
          secFace.className = 'vl-section';
          secFace.textContent = '表情與眼神效果';
          popover.appendChild(secFace);

          const faceOptions = [
            { label: '😐 正常待機', key: 'neutral', active: !activeStates.blush && !activeStates.sad && !activeStates.angry && !activeStates.hearteyes && !activeStates.stareyes && !activeStates.circleeyes, action: () => {
              activeStates.blush = activeStates.sad = activeStates.angry = activeStates.hearteyes = activeStates.stareyes = activeStates.circleeyes = false;
            }},
            { label: '😳 臉紅害羞', key: 'blush', active: activeStates.blush, action: () => { activeStates.blush = !activeStates.blush; }},
            { label: '😢 委屈流淚', key: 'sad', active: activeStates.sad, action: () => { activeStates.sad = !activeStates.sad; if (activeStates.sad) activeStates.angry = false; }},
            { label: '😡 生氣發怒', key: 'angry', active: activeStates.angry, action: () => { activeStates.angry = !activeStates.angry; if (activeStates.angry) activeStates.sad = false; }},
            { label: '😍 愛心眼神', key: 'hearteyes', active: activeStates.hearteyes, action: () => { activeStates.hearteyes = !activeStates.hearteyes; }},
            { label: '🤩 星星眼神', key: 'stareyes', active: activeStates.stareyes, action: () => { activeStates.stareyes = !activeStates.stareyes; }},
            { label: '😵 眩暈旋轉', key: 'circleeyes', active: activeStates.circleeyes, action: () => { activeStates.circleeyes = !activeStates.circleeyes; }}
          ];

          faceOptions.forEach(opt => {
            const item = document.createElement('div');
            item.className = 'vl-item' + (opt.active ? ' active' : '');
            item.innerHTML = '<div class="vl-name">' + opt.label + '</div>';
            item.addEventListener('click', () => {
              opt.action();
              updateModelParameters();
              renderEmoteList();
            });
            popover.appendChild(item);
          });

          // 2. 服裝形態組
          const secOutfit = document.createElement('div');
          secOutfit.className = 'vl-section';
          secOutfit.textContent = '服裝服飾';
          popover.appendChild(secOutfit);

          const outfitOptions = [
            { label: '🖤 經典黑衣形態', active: activeStates.outfit === 'black', action: () => { activeStates.outfit = 'black'; }},
            { label: '🤍 變身白衣形態', active: activeStates.outfit === 'white', action: () => { activeStates.outfit = 'white'; }}
          ];

          outfitOptions.forEach(opt => {
            const item = document.createElement('div');
            item.className = 'vl-item' + (opt.active ? ' active' : '');
            item.innerHTML = '<div class="vl-name">' + opt.label + '</div>';
            item.addEventListener('click', () => {
              opt.action();
              updateModelParameters();
              renderEmoteList();
            });
            popover.appendChild(item);
          });

          // 3. 手勢形態組
          const secHand = document.createElement('div');
          secHand.className = 'vl-section';
          secHand.textContent = '手勢姿勢';
          popover.appendChild(secHand);

          const handOptions = [
            { label: '👐 正常雙手', active: activeStates.hand === 'normal', action: () => { activeStates.hand = 'normal'; }},
            { label: '🎤 手持麥克風', active: activeStates.hand === 'mc', action: () => { activeStates.hand = 'mc'; }},
            { label: '🔪 手持匕首', active: activeStates.hand === 'knife', action: () => { activeStates.hand = 'knife'; }},
            { label: '🐭 手持倉鼠', active: activeStates.hand === 'mouse', action: () => { activeStates.hand = 'mouse'; }}
          ];

          handOptions.forEach(opt => {
            const item = document.createElement('div');
            item.className = 'vl-item' + (opt.active ? ' active' : '');
            item.innerHTML = '<div class="vl-name">' + opt.label + '</div>';
            item.addEventListener('click', () => {
              opt.action();
              updateModelParameters();
              renderEmoteList();
            });
            popover.appendChild(item);
          });

          // 4. 血跡疊加組
          const secBlood = document.createElement('div');
          secBlood.className = 'vl-section';
          secBlood.textContent = '特殊狀態 (血跡)';
          popover.appendChild(secBlood);

          const bloodOptions = [
            { label: '🩸 臉部血跡', active: activeStates.bloodFace, action: () => { activeStates.bloodFace = !activeStates.bloodFace; }},
            { label: '🩸 胸口血跡', active: activeStates.bloodBody, action: () => { activeStates.bloodBody = !activeStates.bloodBody; }}
          ];

          bloodOptions.forEach(opt => {
            const item = document.createElement('div');
            item.className = 'vl-item' + (opt.active ? ' active' : '');
            item.innerHTML = '<div class="vl-name">' + opt.label + '</div>';
            item.addEventListener('click', () => {
              opt.action();
              updateModelParameters();
              renderEmoteList();
            });
            popover.appendChild(item);
          });
        }

        window.renderEmoteList = renderEmoteList;

        function openPopover() {
          // 關閉語音選單以防衝突
          const vPopover = document.getElementById('voice-list');
          if (vPopover) vPopover.classList.remove('open');
          
          popover.classList.add('open');
          btn.setAttribute('aria-expanded', 'true');
          renderEmoteList();
          try { positionBubble(); } catch (e) {}
        }

        function closePopover() {
          popover.classList.remove('open');
          btn.setAttribute('aria-expanded', 'false');
        }

        function togglePopover() {
          if (popover.classList.contains('open')) closePopover();
          else openPopover();
        }

        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          togglePopover();
        });

        // 點擊外面關閉
        document.addEventListener('click', (e) => {
          if (!popover.classList.contains('open')) return;
          if (popover.contains(e.target) || btn.contains(e.target)) return;
          closePopover();
        });

        // ESC 關閉
        document.addEventListener('keydown', (e) => {
          if (e.key === 'Escape' && popover.classList.contains('open')) closePopover();
        });
      })();

      // 鍵盤快捷鍵切換表情
      document.addEventListener('keydown', (e) => {
        if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) return;
        const k = e.key;
        if (k >= '0' && k <= '7') {
          if (k === '0') {
            const pick = EMOTION_KEYS[Math.floor(Math.random() * EMOTION_KEYS.length)];
            applyEmotion(pick);
          } else {
            const idx = parseInt(k, 10) - 1;
            if (idx >= 0 && idx < EMOTION_KEYS.length) applyEmotion(EMOTION_KEYS[idx]);
          }
        }
      });"""

content = apply_replace(content, js_target, js_replacement, "JS Code")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("PATCH COMPLETED!")
