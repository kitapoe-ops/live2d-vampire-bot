# 吸血鬼 Widget — External Events Lite (Reactive API)

> 設計文件 v0.2 — 2026-06-14 (Updated: v35 implemented 21:18)
> Status: ✅ **Implemented in v35** (commit `b6d7e21`)
> 設計理念：**輕量 / 穩定 / 通用性**

---

## 0. 設計 pivot（回應用戶澄清）

之前 `hooks-and-yaml-actions.md` v0.1 嘅 YAML rules engine 太重。
用戶澄清真正需求：

```text
日寫日記  →  vampire 讀到我寫嘅文字 → 自動反應
英文試卷  →  vampire 知道我答啱/錯  → 自動反應
```

**核心：塞段 text 落 widget，widget 自己 judge + 反應。**
唔需要用戶預寫 rule、唔需要 schema、唔需要設定面板。
**一個 postMessage type 就夠。**

舊 YAML 方案可以做 power user advanced feature，但**唔係 MVP**。

---

## 1. 設計目標（重新對齊）

```text
✅ 輕量     - 1 個 postMessage type, ~50 行 code
✅ 穩定     - 無 YAML edge case, 全部 try/catch + fallback
✅ 通用     - 任何文字 / context 都 work
✅ 0 設定    - 貼上 iframe 即用, 唔需要 setup
⏸️ YAML     - power user advanced, deferred
```

**Layer cake（剩番 3 層）：**

```text
┌──────────────────────────────────────────────────┐
│  Layer 1 — 通訊  (postMessage: 1 個 type 'react')│
├──────────────────────────────────────────────────┤
│  Layer 2 — 判斷  (decideReaction)                │
│    context hint → LLM (DeepSeek) → 關鍵字 fallback│
├──────────────────────────────────────────────────┤
│  Layer 3 — 執行  (applyEmotion + speak + action)  │
│    widget 內部 triggerAction() / speak() 已 work   │
└──────────────────────────────────────────────────┘
```

---

## 2. 通訊 API — 一個 type 搞掂晒

### 2.1 唯一新 type: `react`

```javascript
// Parent 端（嵌入 page）
const vf = document.getElementById('vampire').contentWindow;

// 基本
vf.postMessage({
  ns: 'avatar-widget-host',
  type: 'react',
  text: '今日心情好差，個貓又死咗',
}, '*');

// 帶 context hint（推薦）
vf.postMessage({
  ns: 'avatar-widget-host',
  type: 'react',
  text: 'The cat sat on the ___',
  context: {
    source: 'test',
    correct: true,           // widget 優先用呢個 hint
    user_answer: 'mat',
    expected: 'mat',
  },
}, '*');

// 強制語音 route
vf.postMessage({
  ns: 'avatar-widget-host',
  type: 'react',
  text: '...',
  voice: 'minimax',         // 'browser' (default) | 'minimax'
  voice_id: 'female-shaonv',
}, '*');
```

### 2.2 Widget 端 listener

```javascript
// 加喺 widget boot 完之後
window.addEventListener('message', (e) => {
  const d = e.data || {};
  if (d.ns !== 'avatar-widget-host') return;

  if (d.type === 'react') {
    handleReact({
      text:    String(d.text || '').slice(0, 2000),
      context: d.context  || {},
      voice:   d.voice    || null,
      voice_id: d.voice_id || null,
    });
  }
});
```

**安全性：**
- text 用 `String().slice(0, 2000)` 防爆 buffer
- bubble render 永遠用 `textContent`，**唔好用 `innerHTML`**
- context 純 client-side 處理，唔出網（除咗 LLM call）

---

## 3. 判斷邏輯 — decideReaction()

### 3.1 三層判斷

```text
Priority 1:  context hint (e.g. correct: true)  → 直接用
Priority 2:  LLM (DeepSeek, 有 key 嘅話)         → 動態
Priority 3:  關鍵字 fallback (冇 LLM)            → 簡單 heuristic
```

### 3.2 完整 code（核心 ~50 行）

```javascript
async function handleReact({ text, context, voice, voice_id }) {
  if (!text && !context.suggested_emotion) {
    console.warn('[react] empty payload');
    return;
  }

  const result = await decideReaction(text, context);

  // ── 執行動作 ──
  if (result.emotion && typeof window.applyEmotion === 'function') {
    window.applyEmotion(result.emotion);
  }
  if (result.action) {
    triggerAction(result.action);
  }
  if (result.reply) {
    speakWithRoute({
      text:     result.reply,
      voice:    voice,
      voice_id: voice_id,
    });
  }

  // ── UI feedback ──
  if (typeof showBubble === 'function') {
    showBubble('🧛 吸血鬼聽緊你講…');
  }
}

async function decideReaction(text, context) {
  // Priority 1: context hint
  if (context.correct === true) {
    return {
      emotion: 'happy',
      action:  'mc',                  // 揸 mic 慶祝
      reply:   randomPick([
        '啱晒！你真聰明！',
        '冇錯啦，你好叻呀！',
        '答得啱，正呀！',
      ]),
    };
  }
  if (context.correct === false) {
    return {
      emotion: 'sad',
      action:  null,
      reply:   randomPick([
        '差少少啫，再諗下？',
        '唔緊要，再嚟一次！',
        '錯咗少少，加油！',
      ]),
    };
  }
  if (context.suggested_emotion) {
    return {
      emotion: context.suggested_emotion,
      action:  context.suggested_action || null,
      reply:   context.suggested_reply   || text.slice(0, 80),
    };
  }

  // Priority 2: LLM
  const dsKey = (() => { try { return localStorage.getItem('deepseek_key') || ''; } catch (e) { return ''; } })();
  if (dsKey && text) {
    try {
      const llmResult = await callDeepSeekForReaction(text, context);
      if (llmResult) return llmResult;
    } catch (e) {
      console.warn('[react] LLM failed, fallback to keywords:', e);
    }
  }

  // Priority 3: keyword fallback
  return keywordReact(text);
}
```

### 3.3 LLM 判斷（DeepSeek）

```javascript
async function callDeepSeekForReaction(text, context) {
  const key = localStorage.getItem('deepseek_key');
  if (!key) return null;

  const systemPrompt = `你係一個反應式助手，會根據用戶輸入嘅 context 決定表情、動作、簡短回覆。

只回 JSON，唔好加其他文字。JSON schema：
{
  "emotion": "happy" | "sad" | "angry" | "shy" | "surprised" | "neutral",
  "action": "Scene1" | "Idle" | "knife" | "mc" | "mouse" | "click" | "bloodFace" | "bloodBody" | null,
  "reply": "一句粵語回覆，max 60 字"
}

規則：
- 用戶情緒低落 / 悲傷 → emotion: "sad", action: null
- 用戶慶祝 / 成功 / 答啱 → emotion: "happy", action: "mc"
- 用戶犯錯 / 失敗 → emotion: "sad" 或 "shy"
- 用戶驚訝 / 意外 → emotion: "surprised"
- 用戶嬲 → emotion: "angry"
- 預設 → emotion: "neutral", action: null
- reply 要粵語口語，max 60 字
- 唔好笑講嘢，吸血鬼性格 + cute 模式`;

  const r = await fetch('https://api.deepseek.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': '***' + key,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'deepseek-chat',
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: 'Context: ' + JSON.stringify(context) + '\n\nInput: ' + text },
      ],
      max_tokens: 200,
      temperature: 0.7,
      response_format: { type: 'json_object' },
    }),
  });
  if (!r.ok) throw new Error('DeepSeek http ' + r.status);
  const data = await r.json();
  const content = data.choices?.[0]?.message?.content;
  if (!content) return null;
  const parsed = JSON.parse(content);
  // validate
  const validEmo = ['happy','sad','angry','shy','surprised','neutral'];
  if (!validEmo.includes(parsed.emotion)) parsed.emotion = 'neutral';
  if (typeof parsed.reply !== 'string') parsed.reply = '';
  parsed.reply = parsed.reply.slice(0, 60);   // TTS cap
  return parsed;
}
```

### 3.4 Keyword Fallback（無 LLM 都 work）

```javascript
function keywordReact(text) {
  const t = (text || '').toLowerCase();

  // Strong patterns
  if (/啱|correct|right|✓|✅|yes!|成功|做咗/.test(t)) {
    return { emotion: 'happy', action: 'mc',
             reply: '啱晒！你真係好叻！' };
  }
  if (/錯|wrong|✗|❌|no!|失敗|唔得/.test(t)) {
    return { emotion: 'sad', action: null,
             reply: '差少少，再諗下？' };
  }
  if (/嬲|angry|hate|嬲爆|激嬲/.test(t)) {
    return { emotion: 'angry', action: null,
             reply: '唔好嬲咁多啦，深呼吸。' };
  }
  if (/害羞|shy|不好意思|臉紅|紅臉/.test(t)) {
    return { emotion: 'shy', action: null,
             reply: '你...你望住我嚟做咩...' };
  }
  if (/驚|嚇|surprise|意外|嘩|竟然/.test(t)) {
    return { emotion: 'surprised', action: null,
             reply: '嘩，咁都得？！' };
  }
  if (/傷心|sad|哭|唔開心|慘|可憐|難過/.test(t)) {
    return { emotion: 'sad', action: null,
             reply: '唔緊要㗎，我都陪住你。' };
  }
  if (/開心|happy|好叻|叻|叻仔|棒/.test(t)) {
    return { emotion: 'happy', action: 'mc',
             reply: '叻仔！繼續加油！' };
  }

  // Default
  return { emotion: 'neutral', action: null,
           reply: '嗯嗯，我喺度聽緊。' };
}
```

### 3.5 隨機 reply pool

```javascript
const REPLY_POOL = {
  correct: [
    '啱晒！你真聰明！', '冇錯啦，你好叻呀！',
    '答得啱，正呀！', 'Bingo！', '100分！',
  ],
  wrong: [
    '差少少啫，再諗下？', '唔緊要，再嚟一次！',
    '錯咗少少，加油！', '差一啲啲咋，唔好放棄！',
  ],
  sad: [
    '唔緊要㗎，我都陪住你。',
    '我哋一齊面對啦。',
    '你唔係一個人喎。',
  ],
  happy: [
    '叻仔！繼續加油！', '好嘢！', 'Yeah！',
    '你最棒啦！',
  ],
};

function randomPick(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}
```

---

## 4. Use case 範例（完整 snippet）

### 4.1 日記

```html
<!-- 嵌入 page: diary.html -->
<textarea id="diary" rows="10" placeholder="寫低你今日嘅嘢..."></textarea>
<iframe id="v" src="https://vampire.kitahim.uk/?embed=1"></iframe>

<script>
const diary = document.getElementById('diary');
const v = document.getElementById('v').contentWindow;

let lastReactedText = '';
let reactTimer = null;

diary.addEventListener('input', () => {
  clearTimeout(reactTimer);
  reactTimer = setTimeout(() => {
    const text = diary.value.trim();
    if (text.length < 8 || text === lastReactedText) return;
    lastReactedText = text;
    v.postMessage({
      ns: 'avatar-widget-host',
      type: 'react',
      text: text.slice(-500),     // 最後 500 字，context 最新
      context: { source: 'diary' },
    }, '*');
  }, 1500);  // debounce 1.5s
});
</script>
```

**效果：**
- 用戶停寫 1.5s → widget LLM 判斷情緒 → 自動 emotion + 講嘢
- 例如寫「今日被老細鬧咗好慘」 → sad 表情 + 安慰語

### 4.2 英文試卷

```html
<!-- 嵌入 page: quiz.html -->
<p>Q1: The cat sat on the ___</p>
<input id="ans" placeholder="type answer">
<button id="submit">Submit</button>
<iframe id="v" src="https://vampire.kitahim.uk/?embed=1"></iframe>

<script>
const CORRECT = { Q1: 'mat', Q2: 'log', /* ... */ };
const v = document.getElementById('v').contentWindow;

document.getElementById('submit').addEventListener('click', () => {
  const userAns = document.getElementById('ans').value.trim();
  const expected = CORRECT.Q1;
  const isCorrect = userAns.toLowerCase() === expected.toLowerCase();
  v.postMessage({
    ns: 'avatar-widget-host',
    type: 'react',
    text: 'Q: The cat sat on the ___\nUser: ' + userAns + '\nExpected: ' + expected,
    context: {
      source: 'quiz',
      correct: isCorrect,
      question_id: 'Q1',
      user_answer: userAns,
      expected: expected,
    },
  }, '*');
});
</script>
```

**效果：**
- Submit → context.correct: true/false → 立即 emotion + reply
- 唔使 LLM（context hint 已經夠）
- 答啱：happy + 揸 mic + 「Bingo！」
- 答錯：sad + 「差少少，再諗下？」

### 4.3 通用 - 任何 SPA event

```javascript
// Tab 切換
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') {
    v.postMessage({
      ns: 'avatar-widget-host',
      type: 'react',
      text: 'User 走咗',
      context: { source: 'visibility', suggested_emotion: 'shy',
                 suggested_reply: '你... 走咗去邊呀？' },
    }, '*');
  }
});

// Form submit 成功
form.addEventListener('submit', (e) => {
  e.preventDefault();
  // ... after success
  v.postMessage({
    ns: 'avatar-widget-host',
    type: 'react',
    context: { source: 'form', correct: true,
               suggested_emotion: 'happy',
               suggested_action: 'mc',
               suggested_reply: 'Submit 成功啦！' },
  }, '*');
});
```

**效果：** 完全通用，任何 SPA / page / web app 都可以用。
`context.suggested_*` 直接 override LLM 判斷，零延遲。

---

## 5. 實作 plan（只 1 個 commit）

### Step 1：加 `react` listener（~30 行）

```javascript
// 加喺 widget.html ~line 1023 嘅 message handler 後面
window.addEventListener('message', (e) => {
  const d = e.data || {};
  if (d.ns !== 'avatar-widget-host') return;
  if (d.type !== 'react') return;        // 唔影響現有 'say' handler
  handleReact({
    text:     String(d.text || '').slice(0, 2000),
    context:  d.context  || {},
    voice:    d.voice    || null,
    voice_id: d.voice_id || null,
  });
});
```

### Step 2：寫 3 個 helper（~80 行）

- `handleReact()` - dispatcher
- `decideReaction()` - 3 priority 判斷
- `keywordReact()` - fallback heuristic
- `callDeepSeekForReaction()` - LLM
- `speakWithRoute()` - per-call voice routing

### Step 3：reply pool（~20 行）

- `REPLY_POOL` + `randomPick()`

### Step 4：測試

- 寫 1 個 test page 模擬 3 個 use case
- 確認有 / 冇 DeepSeek key 兩個 path 都 work
- 確認 context hint 100% 正確

### 交付：`feat(widget): reactive API for host pages (postMessage 'react')`

**時程：1-1.5 hr, 1 個 commit。**

---

## 6. 對比舊 YAML 方案

| 維度 | YAML v0.1 | Lite v0.2 |
|------|-----------|-----------|
| PostMessage type 數 | 5 | 1 |
| 規則寫法 | YAML schema | 唔需要 |
| 用戶設定 UI | 必要 | 唔需要 |
| 動態程度 | 半動態 (rule 預寫) | 全動態 (LLM judge) |
| 通用性 | 中（rule 寫邊個 trigger 就有邊個） | 高（任何 text） |
| 實作時間 | 5-9 hr / 4 commits | 1-1.5 hr / 1 commit |
| 維護成本 | 高（rule 愈多愈亂） | 低（system prompt + keyword） |
| 失敗模式 | YAML parse fail | LLM fail → keyword fallback |
| 適合對象 | Dev / power user | **所有 user（默認）** |

**YAML 方案唔死，只係降級做 advanced option：**
- v0.2 lite 先做，1 commit 上線
- YAML 可以遲下做 v0.3 嘅 optional add-on，掛喺 Settings → 「進階規則」tab
- 大部分用戶 99% 情況 lite 就夠

---

## 7. 安全性 + Rate limit

### 7.1 Rate limit

```javascript
const _reactCooldown = { lastCall: 0, MIN_GAP_MS: 800 };

async function handleReact(payload) {
  const now = Date.now();
  if (now - _reactCooldown.lastCall < _reactCooldown.MIN_GAP_MS) {
    console.log('[react] rate-limited, drop call');
    return;
  }
  _reactCooldown.lastCall = now;
  // ... process
}
```

避免 spam（例如 diary input event 連環 fire）。

### 7.2 DeepSeek cost control

- `max_tokens: 200` hard cap
- 1 個 react call ≈ 500 tokens input + 200 output = ¥0.0014
- 1000 觸發 = ¥1.4
- 10,000 觸發 = ¥14 ← 對用家自費 key 嚟講 OK
- rate limit 800ms min gap 已經足夠

### 7.3 XSS 防護

- bubble render 用 `textContent` 唔用 `innerHTML`（已經係現有做法）
- `text.slice(0, 2000)` 防 buffer 攻擊
- LLM output parse 必須 try/catch，唔可以 `JSON.parse` 直接信
- `applyEmotion()` 嘅 emotion name **必須** 喺 whitelist：
  ```javascript
  const VALID_EMOTIONS = ['happy','sad','angry','shy','surprised','neutral'];
  if (!VALID_EMOTIONS.includes(parsed.emotion)) parsed.emotion = 'neutral';
  ```

---

## 8. 開放問題（只 2 個，比 v0.1 少 3 個）

1. **Reply 預設長度 cap** — 60 字 / 80 字 / 100 字？
   （影響 TTS time + cost，60 字 ≈ 3-4s speech）

2. **Context 過大時 truncation** — text 超過 2000 字點處理？
   （現有：直接 slice(0, 2000)，但係咪保留頭 / 尾 / 中間？）

3. **System prompt 可唔可以由 user 自訂？** — 喺 settings 加 textarea？
   （會增加 v0.2 複雜度，default prompt 已經 OK 嘅話可以 skip）

---

## 9. 預期時程

```text
Step 1-3:  ~1-1.5 hr    postMessage listener + 3 helpers + reply pool
Step 4:    ~0.5 hr     test page + verify
Total:     ~2 hr, 1 commit
```

---

## 10. 對舊文件嘅處理

`plans/hooks-and-yaml-actions.md` v0.1 唔刪，但**降級做 advanced**：

```text
plans/
├── external-events-lite.md    ← 本文件，v0.2 (Lite, MVP)
├── hooks-and-yaml-actions.md   ← v0.1 (Advanced, power user)
└── dev-mode-settings-plan.md   ← v0 (Dev Mode Panel)
```

或者將 v0.1 重命名做 `hooks-and-yaml-actions-advanced.md` 表示佢係
optional add-on，唔係默認。

---

## 11. 開始做要你 confirm 嘅嘢

1. **OK lite v0.2 嘅方向？** (1 commit, 1-2 hr, 1 postMessage type)
2. **context hint priority 排位 OK？** (context.correct > LLM > keyword)
3. **System prompt 用我寫嘅嗰段？** 定你要調整？
4. **Reply cap 60 字 OK？** 定加到 80？
5. **YAML v0.1 處理方法？** (留低做 advanced / 刪走 / 合併入 lite doc)

揀完 1-2 個鐘就 commit 完。

---

## 12. Implementation 記錄 (v35, 2026-06-14)

**Commit：** `b6d7e21`
**Deployed：** https://vampire.kitahim.uk (Cloudflare Pages)

### 已實作

- ✅ **postMessage 'react' listener** 裝喺 widget.html 現有 message handler
- ✅ **handleReact()** dispatcher (rate-limit 800ms + apply emotion/action/speak/bubble)
- ✅ **decideReaction()** 3-priority 判斷 (context hint > DeepSeek > keyword)
- ✅ **_reactCallDeepSeek()** 抽 LLM 決定 emotion/action/reply JSON
- ✅ **_reactKeyword()** 8 個 regex pattern 覆蓋 8 種情緒
- ✅ **REPLY_POOL** 8 組粵語 random reply strings
- ✅ **_reactSpeakWithRoute()** per-call voice override (browser/MiniMax)
- ✅ **Smoke test page** 喺 `index.html` 加 3 個 control:
  - Diary textarea (debounce 1.5s)
  - Quiz yes/no button (context.correct)
  - Reset button (iframe reload + parent localStorage clear)

### 對話回應 reply pool 樣本

```text
correct:   啱晒！你真聰明！| 冇錯啦...| 答得啱，正呀！| Bingo！| 100分！
wrong:     差少少啫...| 唔緊要，再嚟一次！| 錯咗少少...
sad:       唔緊要㗎...| 我哋一齊面對啦。| 你唔係一個人喎。
happy:     叻仔！繼續加油！| 好嘢！| Yeah！| 你最棒啦！
angry:     唔好嬲咁多啦，深呼吸。| 冷靜啲，你得嘅。
shy:       你...你望住我嚟做咩...| 我會害羞㗎...
surprised: 嘩，咁都得？！| 哇！| 乜料咁都可以！
neutral:   嗯嗯，我喺度聽緊。| 我喺度。| 我聽緊你講。
```

### 完整 snippet（parent 端，3 use case）

**Use Case 1：文字輸入 (debounce 1.5s)**

```javascript
const iframe = document.querySelector('iframe');
const diary  = document.getElementById('react-diary-input');
let timer;
let lastSent = '';
diary.addEventListener('input', () => {
  clearTimeout(timer);
  timer = setTimeout(() => {
    const text = diary.value.trim();
    if (text.length < 3 || text === lastSent) return;
    lastSent = text;
    iframe.contentWindow.postMessage({
      ns: 'avatar-widget-host',
      type: 'react',
      text: text.slice(-500),
      context: { source: 'diary' },
    }, '*');
  }, 1500);
});
```

**Use Case 2：Yes/No Quiz (context.correct)**

```javascript
document.getElementById('quiz-yes').addEventListener('click', () => {
  iframe.contentWindow.postMessage({
    ns: 'avatar-widget-host',
    type: 'react',
    text: 'Q: 1+1=2 啱唔啱?\nUser: 啱',
    context: { source: 'quiz', correct: true, question_id: 'Q1' },
  }, '*');
});
```

**Use Case 3：Reset**

```javascript
document.getElementById('reset-btn').addEventListener('click', () => {
  const src = iframe.getAttribute('src');
  iframe.setAttribute('src', src.split('?')[0] + '?reset=' + Date.now());
  Object.keys(localStorage).forEach(k => {
    if (k.indexOf('xiaob_') === 0 || k === 'deepseek_key') localStorage.removeItem(k);
  });
});
```

### Smoke test 結果

- ✅ Widget live at https://vampire.kitahim.uk
- ✅ Iframe loads widget.html
- ✅ Diary textarea 觸發 postMessage (debounced)
- ✅ Quiz yes/no 觸發 postMessage (context.correct)
- ✅ Reset 重載 iframe + 清 parent localStorage
- ✅ byte-perfect deploy (0 diff vs local)

### Known limitations

- **Cooldown race**: 兩個 react 喺 800ms 內 fire，後者會被 drop。
  LLM call 本身 ~1-3s，呢個 trade-off 可以接受。
- **voice_id leak**: `_reactSpeakWithRoute` 暫時覆蓋 NEURAL_VOICE，
  finally restore。Race condition 可能。如果發現問題，move 落
  `fetchMinimaxTtsDirect()` 嘅 per-call override（speak.js 入面
  嘅參數化）。
- **跨 origin localStorage**: 父頁 reset 只可以清自己嘅 key。
  Widget 內部嘅 key 要靠 widget 自己嘅 Settings → 診斷 → 清除。
  Phase 2 可以加 `postMessage 'reset'` type，widget 自己清。
