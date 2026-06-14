# 吸血鬼 Widget — 動作/道具 觸發指南

> 對應 widget 版本：v31+（commit `c0bf293` 起）
> 對應模型：吸血鬼 Live2D（幽靈蛸 / 時鳥，2025-11-09 VTube Studio 導出）
> 部署位置：`https://vampire.kitahim.uk`（Cloudflare Pages，100% 靜態）

---

## TL;DR

吸血鬼 widget 入面有 **三類「動作」**，各有正確嘅 trigger API。
搞錯就會 silent fail、popover 冇反應、或者 LLM 出 emotion 嗰陣個臉
唔郁。

| 類別 | 觸發 API | 對應檔案 |
|------|----------|----------|
| 全身動作（motions） | `model.motion(groupName)` | `*.motion3.json` |
| 表情（emotions） | `applyEmotion(name)` ← 用呢個 | `*.exp3.json` |
| 道具/手勢（gestures） | `model.expression(name)` 直出 | `*.exp3.json` |

**關鍵陷阱：**
- ❌ `model.expression('happy')` 唔 work — 冇 `happy.exp3.json`
- ✅ `applyEmotion('happy')` 會 internal map 去 `hearteyes` + 寫眼 param
- ❌ `model.expression('vampire')` / `'vampire2'` 會 over-write 衣裝
- ✅ 衣裝 toggling 改用 `toggleOutfit()` → `applyOutfit(outfit)`
- ❌ 同一個 motion 重複 trigger 會卡住
- ✅ 用 `injectMotions()` 註冊一次，之後用 `model.motion(name)`

---

## 1. 三類動作 / 點樣分

### 1.1 全身動作（Motions）

**概念：** 連續多幀嘅 body / face 動畫，有時長。

**可用：**

```text
Scene1  →  Scene1.motion3.json
            1.167s, 30fps, 入場動畫
Idle    →  2.motion3.json
            9.987s, 60fps, loop 嘅自然姿態循環
```

> **注意：** `Idle` 內部檔名係 `2.motion3.json`（VTube Studio 預設名），
> 唔係 `Idle.motion3.json`。但 motion **group name** 叫 `Idle`。

**點樣 trigger：**

```javascript
// Step 1: 啟動時 inject 一次（widget.html ~line 2096）
await injectMotions();

// Step 2: 任何時候播
model.motion('Scene1');  // 播一次入場
model.motion('Idle');    // 入 idle loop
```

**注意：** 動作結束時要 `restoreOutfitFromEmoteState()`，
否則衣裝會被 motion 入面嗰啲空 keyframe 還原去 model default（白）。

呢個係 v12+ 嘅必修 patch，widget 已經喺 `model.on('motionFinish', …)`
自動搞掂（見 widget.html ~line 2153）。

### 1.2 表情（Emotions）

**概念：** 一次性 blend 6-13 個 Live2D param，唔係動畫。

**與 motion 嘅分別：**
- 表情係 static blend，冇時長
- 多數會 overwrite 眼睛 / 眉毛 / 嘴型嘅 base value
- 立即生效，唔會 loop

**可用（7 個 semantic name）：**

```text
neutral    →  stareyes    （forward gaze，冇特別效果）
happy      →  hearteyes   （心心眼，map 過去㗎）
sad        →  sad         （哭哭 + 眼淚 + 垂眉）
angry      →  mad         （黑化生氣）
shy        →  shy         （害羞紅臉）
surprised  →  circleeyes  （蚊香眼）
```

> 註：`happy` 冇對應 `.exp3.json`！`applyEmotion()` 內部
> 將 `happy` map 去 `hearteyes.exp3.json`，再額外寫
> `PARAM_MOUTH_FORM=1.0` / `PARAM_BROW_L_FORM=0.3` 嗰啲嘴型 param。
> 直接 `model.expression('happy')` 會 throw。

**點樣 trigger：**

```javascript
// ❌ 錯：直接用 model.expression 對住語義名
model.expression('happy');     // 冇呢個 exp3.json，silently fail
model.expression('surprised'); // 冇，都 fail

// ✅ 正確：用 wrapper
window.applyEmotion('happy');
window.applyEmotion('sad');
window.applyEmotion('neutral');
```

**`applyEmotion(name)` 做嘅嘢：**
1. `v22Invalidate()` 清 per-frame cache（v22 perf patch）
2. 將 `EMOTION_PRESETS[name]` 嘅 N 個 param 寫入 `KNOWLEDGE.bulkSet()`
3. 同步 `emoteState.{eyes,blush,tears,angry}` flag
4. 內部 map 去 `expMap[name]` 再 trigger `model.expression(expName)` 做 fallback
5. 更新 UI active state
6. Bubble 顯示「表情：開心」

### 1.3 道具 / 手勢（Gestures）

**概念：** 揸刀 / 揸 mic / 揸 mouse / 點擊 / 血跡。
全部都係 `.exp3.json` 入面嘅 static blend，唔係動畫。

**可用（6 個，**全部有獨立檔案**）：**

```text
knife      →  knife.exp3.json
mc         →  mc.exp3.json
mouse      →  mouse.exp3.json
click      →  click.exp3.json
bloodFace  →  blood-face.exp3.json
bloodBody  →  blood-body.exp3.json
```

> 注意檔名 vs 名嘅對應：`bloodFace` flag 對 `blood-face.exp3.json`、
> `bloodBody` flag 對 `blood-body.exp3.json`。Hypen 唔同 underscore。

**點樣 trigger：**

```javascript
// ✅ 直接用 model.expression()，呢類 name 全部有對應 .exp3.json
model.expression('knife');
model.expression('mc');
model.expression('mouse');
model.expression('click');
model.expression('blood-face');
model.expression('blood-body');
```

**多個道具共存：** 道具 flag 喺 `emoteState.gestures` 入面
係 **object of booleans** 而唔係 string：

```javascript
emoteState.gestures = {
  knife: false,
  mc:    false,
  mouse: false,
  click: false,
};
```

可以同時 `gestures.knife = true && gestures.mc = true`，
render loop 會自動 `v22Set('PARAMhands_1', 1.0)` + `v22Set('PARAMhands_2', 1.0)`
兩個 param 都 1.0。但 `model.expression('knife')` 同
`model.expression('mc')` 同時 trigger 嘅話，後者會 override 前者
（`.exp3.json` 係 Replace blend 唔係 Add blend），
所以**觸發單個道具之後**記得同步 `emoteState.gestures` flag。

**血跡：** 觸發後 persist 唔會自己清。要清返就：

```javascript
emoteState.bloodFace = false;
emoteState.bloodBody = false;
// 下一個 frame render loop 自動寫 0.0
```

---

## 2. 完整可用名單（reference 對照表）

> 來源：`vampire_vts/吸血鬼.model3.json` 嘅 FileReferences

### Expressions（.exp3.json，總共 14 個）

```text
Name              File                    Size   用途
─────────────────────────────────────────────────────────────
blood-body        blood-body.exp3.json    127 B  胸前血跡
blood-face        blood-face.exp3.json    127 B  臉上血跡
circleeyes        circleeyes.exp3.json    129 B  蚊香眼
click             click.exp3.json         167 B  點擊手勢
hearteyes         hearteyes.exp3.json     129 B  心心眼
knife             knife.exp3.json         272 B  揸刀
mad               mad.exp3.json           126 B  黑化生氣
mc                mc.exp3.json            272 B  揸 mic
mouse             mouse.exp3.json         272 B  揸 mouse
sad               sad.exp3.json           432 B  哭哭
shy               shy.exp3.json           124 B  害羞
stareyes          stareyes.exp3.json      128 B  forward gaze
vampire           吸血鬼.exp3.json     1460 B  黑色形態
vampire2          vampire2.exp3.json      707 B  白色形態
```

### Motions（.motion3.json，總共 2 個）

```text
Group     File                  Duration   Fps   Loop
─────────────────────────────────────────────────────
Scene1    Scene1.motion3.json   1.167 s    30    no
Idle      2.motion3.json        9.987 s    60    yes
```

---

## 3. 動作按鈕（popover）嘅 implementation reference

`#btn-actions` 撳一下會 toggle `#emote-list` popover，
入面 `renderActionList()` 動態砌 4 個 section：

```text
📋 動作列表
├── 🎬 播放 Scene1 動畫       →  model.motion('Scene1')
├── ⏸️ 播放 Idle 動畫         →  model.motion('Idle')
├── 😊 開心                   →  model.expression('hearteyes')
│                                *(注意：呢度係 hard-coded expName，
│                                 唔係 happy；UI label 同 trigger 唔同) 
├── 😢 傷心                   →  model.expression('sad')
├── 😠 生氣                   →  model.expression('mad')
├── 😳 害羞                   →  model.expression('shy')
├── 😲 驚訝                   →  model.expression('sad')   ⚠️ fallback
├── 🤔 思考                   →  model.expression('sad')   ⚠️ fallback
│
🎭 道具
├── 🔪 揸刀                   →  model.expression('knife')
├── 🎤 麥克風                 →  model.expression('mc')
├── 🖱️ 滑鼠                  →  model.expression('mouse')
├── 👆 點擊                   →  model.expression('click')
├── 🩸 臉部血跡               →  model.expression('blood-face')
└── 🩸 胸口血跡               →  model.expression('blood-body')
```

**bug 注意：**
- `happy` label 撳落去其實 trigger 嘅係 `hearteyes`（work，但 misleading）
- `surprised` 同 `thinking` 冇 native expression，跌咗落 `sad` fallback
  （視覺上會以為「傷心」唔係「驚訝」）
- `bloodFace` 嘅 flag 對 `blood-face`（hypen），唔可以串錯

**修正建議（如想加精）：**
1. 將 `expMap` 擴展去覆蓋 `surprised → circleeyes`、`thinking → stareyes`
   等 fallback
2. 將 `happy` label 改做 `❤️ 心心眼`，避免用戶誤會

---

## 4. 標準觸發 pattern（抄呢段就 work）

```javascript
// ============================================================
// 安全 wrapper：自動揀正確 API
// ============================================================

function triggerAction(name) {
  const m = window.model;
  if (!m) {
    console.warn('[triggerAction] model not ready');
    return;
  }

  // ── Motions (group names) ──
  if (name === 'Scene1' || name === 'Idle') {
    try {
      const mm = m.motionManager;
      if (mm && typeof mm.motion === 'function') {
        // Pixi Live2D 0.4.x: motionManager.motion(name) returns Promise
        mm.motion(name)
          .then(() => console.log('[action] motion done:', name))
          .catch(e => console.error('[action] motion error:', name, e));
      } else if (typeof m.motion === 'function') {
        // Some older Pixi Live2D builds expose motion() directly on model
        m.motion(name);
      } else {
        console.warn('[action] no motion API available');
      }
    } catch (e) {
      console.error('[action] motion threw:', e);
    }
    return;
  }

  // ── Emotion presets (semantic names) ──
  // ALWAYS go through applyEmotion — it knows the internal mapping
  // and writes the right param bundle.
  const EMOTION_NAMES = [
    'neutral', 'happy', 'sad', 'angry', 'shy', 'surprised',
  ];
  if (EMOTION_NAMES.includes(name)) {
    if (typeof window.applyEmotion === 'function') {
      window.applyEmotion(name);
    } else {
      console.warn('[action] applyEmotion not ready, fallback to exp3');
      m.expression(name);  // works for sad/shy/angry; fails for others
    }
    return;
  }

  // ── Gestures / props (raw .exp3.json names) ──
  // These have 1:1 mapping in the model. Direct call is fine.
  const KNOWN_EXPRESSIONS = [
    'knife', 'mc', 'mouse', 'click',
    'blood-face', 'blood-body',
    'sad', 'shy', 'mad',           // also valid as raw exp3 names
    'stareyes', 'circleeyes', 'hearteyes',
  ];
  if (KNOWN_EXPRESSIONS.includes(name)) {
    if (typeof m.expression === 'function') {
      m.expression(name)
        .then(() => console.log('[action] expression done:', name))
        .catch(e => console.error('[action] expression error:', name, e));
    } else {
      console.warn('[action] model.expression not available');
    }
    return;
  }

  console.warn('[action] unknown name:', name);
}

// ============================================================
// 用法
// ============================================================

triggerAction('Scene1');      // 播入場動畫
triggerAction('Idle');        // 入 idle
triggerAction('happy');       // 開心（會 heart eyes + 嘴型笑）
triggerAction('sad');         // 傷心
triggerAction('knife');       // 揸刀
triggerAction('blood-face');  // 面上血
```

---

## 5. 內部 mechanism 速查（給 debug / 改 code 用）

### 5.1 `injectMotions()` — 註冊 motion group

```text
位置：widget.html ~line 2096
時機：widget boot 完、Live2D load 完
做法：
  1. fetch 2 個 .motion3.json
  2. PIXI.live2d.CubismMotion.create(json)
  3. im.motionGroups.set(name, motion)        // legacy path
  4. im.motionManager.add(name, factory, 3)   // Pixi 0.4.x path
  5. install model.on('motionFinish', …) 做 outfit restore
```

### 5.2 `applyEmotion(name)` — 表情 preset

```text
位置：widget.html ~line 2375
前置：window.KNOWLEDGE.bulkSet 必須 ready
內部 map：
  sad        →  exp3 'sad'        + tears+1, brow_y-0.6
  shy        →  exp3 'shy'        + shy param
  angry      →  exp3 'mad'        + angry param
  happy      →  exp3 'hearteyes'  + mouth_form+1, brow_form+0.3
  surprised  →  exp3 'circleeyes'
  neutral    →  exp3 'stareyes'   ⚠️ v16 改，唔再用 'vampire'
```

### 5.3 `applyOutfit(outfit)` — 衣裝切換

```text
位置：widget.html ~line 2862
outfit 值：'vampire' (黑) | 'vampire2' (白)
寫入 6 個 param：
  PARAMoutfit1_2, PARAMhariWB, PARAMhariWB2,
  PARAMhari_7, PARAMhari_8, PARAMhari_3
⚠️ 唔好 trigger model.expression('vampire') 或 'vampire2' —
   嗰兩個 .exp3.json 混 outfit + face params，會撞 emotion preset。
```

### 5.4 Render loop — per-frame param write

```text
位置：widget.html ~line 2808（model.update override）
每個 frame 自動執行：
  applyOutfit(emoteState.outfit)
  v22Set('PARAMhands_1/2/3/click', gestures flag)
  v22Set eye param
  v22Set blush/tears/angry param
  v22Set blood face/body param
  blink logic
  mouth logic
```

呢個 loop 係「single source of truth」 — 即係話
**改 `emoteState` flag 就夠，唔使再手動 v22Set**。
`applyEmotion()` 同 `triggerAction()` 改 flag 之後，
下個 frame 就會自動 render。

---

## 6. 常見錯誤 & FAQ

### Q1: 撳動作按鈕冇反應？
**Checklist：**
1. `window.model` 存在？（DevTools console：`typeof window.model`）
2. Live2D load 完？（`window.Live2DIdleWatchdog.isArmed`）
3. `.exp3.json` 名有冇打錯？尤其 `blood-face` vs `blood_face`
4. CSP 阻擋咗？睇 Network tab 有冇 4xx/5xx

### Q2: `model.expression('happy')` 唔 work？
**A:** 冇 `happy.exp3.json`。改用 `applyEmotion('happy')` 會 internal
map 去 `hearteyes`。

### Q3: Play 完動作之後衣裝變返白色？
**A:** Motion 嘅空 keyframe 將 outfit param reset。
v12+ 已 fix：`injectMotions()` 註冊 `motionFinish` listener 自動
`restoreOutfitFromEmoteState()`。如果仲壞就睇下
`model.__v20_motionFinishInstalled` flag。

### Q4: 兩個道具（例如刀 + mic）可以同時 hold 住？
**A:** 視覺可以（`emoteState.gestures` 係 multi-flag）。
但唔可以連續 `model.expression('knife'); model.expression('mc')` —
後者會 replace 前者。要並存就改 flag，等 render loop 寫 param。

### Q5: 新增一個 `.exp3.json` 點樣自動出現喺動作選單？
**A:** 動作選單係 hard-coded 喺 `renderActionList()` 入面。
要加新 entry 直接改 widget.html 嘅 `emotions` / `gestures` array。
（將來 Dev Mode Panel 嘅「模型」tab 可能會 dynamic load，
但 v33 仲未做。）

---

## 7. 版本歷史

| Commit   | 版本 | 改動 |
|----------|------|------|
| `c0bf293` | v31 | 動作按鈕 popover + 12 個 entry |
| `2cf58b3` | —   | Bilingual keyword triggers (e.g. 「揸刀」→ knife) |
| `a1d548f` | —   | `applyEmotion` bind 去 native `.exp3.json` |
| `300199f` | —   | Multi-gesture coexistence (Option A) |
| `2cee5d8` | v25 | Per-file Content-Type 防止 MHTML saver 誤判 |
| `ded8fc9` | v26 | `MotionManager.add()` in-memory injection |
| `8db25d6` | v16 | Outfit decouple from emotion |

> 完整 git log 見 `live2d-fork/` 根目錄 `git log --oneline`。
> 反向 reference：`memory/2026-06-13-vampire-mobile-mic.md`（mic case,
> 同本案無關但用同一個 widget 版本 base）。
