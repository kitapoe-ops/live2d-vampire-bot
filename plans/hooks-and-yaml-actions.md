# 吸血鬼 Widget — 外部事件觸發系統 (Hooks & YAML Actions) — ADVANCED / SUPERSEDED

> 設計文件 v0.1 — 2026-06-14 (已 superseded)
> Status: **Superseded by `external-events-lite.md` v0.2**
>
> 留低做 power user advanced add-on，**唔係 MVP**。
> 一般用戶請睇新文件：`plans/external-events-lite.md`
>
> 對比：
> - v0.1 (本文件): YAML rules engine, 5 trigger types, 5-9 hr / 4 commits
> - v0.2 (新): 1 個 postMessage type 'react', LLM auto-judge, 1-2 hr / 1 commit
>
> 用戶 2026-06-14 feedback：「要保持輕量，穩定及通用性」
> → lite v0.2 先做，YAML v0.1 排喺 advanced optional

---

---

## 1. 目標

將 widget 由「**被動 chat 角色**」升級做「**頁面事件響應助手**」：

- 嵌入頁面（blog / shop / portfolio）有事件發生時
  → 自動觸發 widget 嘅動作 / 表情 / 道具 / 台詞
- 台句可以係：
  - 預寫靜態
  - 由 DeepSeek 根據 context 動態生成
  - 從外部 URL / KV 拉
- 語音可以係：
  - Browser Web Speech API（**FREE**）
  - MiniMax T2A v2（付費，NEURAL_VOICE id）
- 規則用 **YAML 寫**，喺 settings modal 一個新 tab 貼住即可

### Use case 例

```text
🛒 電商頁
  user 撳「加入購物車」→ 揸 mic → DeepSeek 生成一句推廣語
  user idle 30s        → Idle 動作 + 「仲有嘢想知？」

📝 個人 blog
  user scroll 到 80%   → surprise 表情 + 「嘩你睇咗好多！」
  user hover [作者照片] → shy + 紅臉 + 隨機自我介紹

🎮 Web game
  過關 → knife + 開心 + 慶祝語
  受傷 → blood face + sad + 鼓勵語
```

---

## 2. 架構總覽（4 層）

```text
┌──────────────────────────────────────────────────────────────┐
│  Layer 1 — 通訊層  (postMessage iframe API)                 │
│    parent page → widget: { ns, type, ... }                   │
│    widget → parent: { ns, type, ... }  (可選 acknowledgement)│
├──────────────────────────────────────────────────────────────┤
│  Layer 2 — 規則層  (YAML Rules Engine)                       │
│    parse YAML → install event listeners → match triggers     │
├──────────────────────────────────────────────────────────────┤
│  Layer 3 — 內容層  (Phrase Source)                           │
│    static | llm (DeepSeek) | http (KV / API)                 │
├──────────────────────────────────────────────────────────────┤
│  Layer 4 — 執行層  (Action + TTS)                            │
│    triggerAction()  → 動作 / 表情 / 道具                    │
│    speak()  →  Browser TTS (FREE)  | MiniMax T2A v2         │
└──────────────────────────────────────────────────────────────┘
```

每層獨立可測試，未來 Phase 5+ 可以 swap。

---

## 3. 通訊層 — postMessage API 擴展

### 3.1 Widget 已經有嘅 pattern

```javascript
// widget.html ~line 1018
function postToParent(type, payload) {
  try {
    window.parent.postMessage(
      Object.assign({ ns: 'avatar-widget', type }, payload || {}),
      '*'
    );
  } catch (e) {}
}
```

`ns` 已經用咗 `'avatar-widget'`（widget → parent 方向）
而 parent → widget 已經有 listener 識認 `ns: 'avatar-widget-host'`
（widget.html ~line 1023）。

### 3.2 擴展：parent → widget 嘅新 type

```javascript
// 喺 widget boot 完之後安裝
window.addEventListener('message', (e) => {
  const d = e.data || {};
  if (d.ns !== 'avatar-widget-host') return;

  switch (d.type) {
    case 'say':
      // { ns, type:'say', text, voice?, voice_id?, emotion?, gesture? }
      speakWithRoute(d);
      break;

    case 'emote':
      // { ns, type:'emote', name:'happy'|'sad'|... }
      if (typeof window.applyEmotion === 'function') {
        window.applyEmotion(d.name);
      }
      break;

    case 'action':
      // { ns, type:'action', name:'Scene1'|'knife'|... }
      triggerAction(d.name);
      break;

    case 'sequence':
      // { ns, type:'sequence', steps:[ {...}, {...} ] }
      runSequence(d.steps || []);
      break;

    case 'ruleset':
      // { ns, type:'ruleset', yaml:'...' }  // 動態 push 規則
      installRulesFromYaml(d.yaml);
      break;
  }
});
```

### 3.3 Parent 端 embed snippet

```html
<iframe
  id="vampire"
  src="https://vampire.kitahim.uk/?embed=1"
  style="position:fixed; bottom:0; right:0;
         width:320px; height:480px; border:0; z-index:9999;">
</iframe>

<script>
const vf = document.getElementById('vampire');
const send = (msg) => vf.contentWindow.postMessage(msg, '*');

document.getElementById('btn-buy').addEventListener('click', () => {
  send({
    ns: 'avatar-widget-host',
    type: 'sequence',
    steps: [
      { action: 'gesture', name: 'knife' },
      { say: '想買嘢呀？我幫你切！', voice: 'minimax',
        voice_id: 'female-shaonv', emotion: 'happy' },
    ],
  });
});
</script>
```

**安全性：**
- `*` origin 太鬆，建議 production 改 `targetOrigin: 'https://vampire.kitahim.uk'`
- Widget 端要 validate `d.type` 係 known string
- 唔好 trust parent 傳入嘅 `text`（XSS 風險喺 bubble HTML render）—
  必須用 `textContent` 而唔係 `innerHTML`，或者 escape

---

## 4. 規則層 — YAML Schema

### 4.1 完整 schema

```yaml
# vampire widget action rules v1
# 貼喺 Settings → Hooks tab

version: 1

# 全域 default（每個 step 唔指明就用呢個）
defaults:
  voice: browser              # browser | minimax
  voice_id: ""                # MiniMax voice_id，例如 female-shaonv
  emotion: neutral
  tts_cap: 120                # 字數上限，避免 LLM 響應過長
  cooldown_ms: 2000           # 同一個 rule 觸發後 N ms 內唔再觸發

rules:
  - id: greet-on-load
    # widget boot 完觸發一次
    trigger: boot
    steps:
      - action: motion
        name: Scene1
      - wait_ms: 1500
      - say: "哈囉，歡迎來到 XX 頁！"
        emotion: happy
        voice: browser

  - id: scroll-near-bottom
    trigger: scroll_pct
    when: "scroll_pct >= 0.8"
    # 嵌入頁需要喺 postMessage 入面傳 scroll_pct
    # 或者 widget 內部裝 window.addEventListener('scroll', ...)
    steps:
      - emote: surprised
      - say: "嘩，你睇到最底啦！"
        voice: browser

  - id: idle-poke
    trigger: idle
    when: "idle_ms >= 30000"
    steps:
      - action: motion
        name: Idle
      - say: "喂，仲喺度呀？有咩想問我？"
        voice: browser
        cooldown_ms: 60000   # 60s 內唔重複

  - id: buy-button
    trigger: host_event
    when: "event.name === 'click_buy'"
    # parent 端：
    #   vf.contentWindow.postMessage({
    #     ns: 'avatar-widget-host',
    #     type: 'host_event',
    #     name: 'click_buy',
    #     context: { product: 'XX', price: 100 }
    #   }, '*');
    steps:
      - action: gesture
        name: knife
      - emote: happy
      # ── LLM 動態話句 ──
      - say:
          source: llm
          prompt: |
            用戶撳咗「加入購物車」，產品係 {{context.product}}，
            價格 {{context.price}}。用 30 字內粵語 sales pitch。
            角色：吸血鬼 + cute 性格。
          fallback: "要買嘢呀？我幫你切！"
        voice: minimax
        voice_id: female-shaonv
        tts_cap: 80

  - id: hover-author-photo
    trigger: dom_event
    when: "selector === '.author-photo' && event === 'mouseenter'"
    # widget 內部用 document.querySelectorAll('.author-photo')
    # 自動安裝 mouseenter listener
    steps:
      - emote: shy
      - say: "你... 你望住我嚟做咩..."
        voice: browser
```

### 4.2 Schema 速查

```text
頂層 keys:
  version       int   必填，固定 1
  defaults      obj   選填
  rules         list  必填，每個 rule 一條

rule keys:
  id            str   必填，唯一識別
  trigger       str   必填，trigger type（見下）
  when          str   選填，JS expression，context 內變數可引用
  steps         list  必填，執行動作
  cooldown_ms   int   選填，同 rule 觸發後冷卻

trigger types:
  boot                 widget 載入完
  scroll_pct           scroll 百分比，需用 when
  idle                 用戶冇操作，需用 when + idle_ms
  host_event           parent postMessage 嚟嘅自訂 event
  dom_event            widget 內部 DOM 監聽，需用 when
  timer                setInterval，固定週期

step types:
  action       obj   { motion | expression, name: 'Scene1' | 'happy' | 'knife' }
  emote        str   'happy' | 'sad' | 'angry' | 'shy' | 'surprised' | 'neutral'
  gesture      str   'knife' | 'mc' | 'mouse' | 'click' | 'bloodFace' | 'bloodBody'
  say          obj   { text | (source: static|llm|http), ... }
  wait_ms      int   暫停 N 毫秒
  run_script   str   eval（⚠️ 只係 dev mode 開）
```

### 4.3 `say` step 詳細

```yaml
# 1. 純靜態
- say: "你好"

# 2. 靜態 + options
- say:
    text: "你好"
    emotion: happy
    voice: browser
    cooldown_ms: 5000

# 3. LLM 動態
- say:
    source: llm
    prompt: |
      用戶問：{{event.text}}
      請用 30 字內粵語回答。
    fallback: "我諗緊..."   # LLM 失敗時用呢個
    tts_cap: 80

# 4. HTTP fetch
- say:
    source: http
    url: "https://my.site/api/quotes/{{user_id}}"
    method: GET
    field: "text"   # JSON 入面拎呢個 key
    cache_ttl: 600  # 10 分鐘 cache
    fallback: "..."

# 5. 隨機 template
- say:
    source: random
    pool:
      - "你嚟啦！"
      - "咁啱嘅，我啱啱好悶"
      - "想傾下偈"
    cooldown_ms: 10000
```

---

## 5. 內容層 — Phrase Source

### 5.1 三種 source 對比

```text
            延遲    成本    適合場景
──────────────────────────────────────────
static      ~0     FREE    固定台詞（greeting / idle poke）
llm         1-3s   $$     動態回應（context-aware 推廣）
http        0.5-1s FREE$   從 KV / DB 拉
                          （個人化台詞、AB test 結果）
```

### 5.2 LLM 整合（DeepSeek）

```javascript
async function resolveLlmPhrase(rule) {
  const ctx = currentEventContext;  // 觸發時嘅 context snapshot
  const prompt = rule.prompt
    .replace(/\{\{(\w+(?:\.\w+)*)\}\}/g, (_, path) => {
      return path.split('.').reduce(
        (o, k) => (o == null ? '' : o[k]),
        ctx
      ) ?? '';
    });

  const key = localStorage.getItem('deepseek_key');
  if (!key) return rule.fallback || '';

  try {
    const r = await fetch('https://api.deepseek.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + key,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'deepseek-chat',
        messages: [{
          role: 'system',
          content: '你係一個吸血鬼助手，用粵語對話。'
        }, {
          role: 'user',
          content: prompt
        }],
        max_tokens: rule.tts_cap || 80,
        temperature: 0.7,
      }),
    });
    if (!r.ok) throw new Error('http ' + r.status);
    const data = await r.json();
    return data.choices?.[0]?.message?.content?.trim()
      || rule.fallback || '';
  } catch (e) {
    console.warn('[llm-phrase] failed:', e);
    return rule.fallback || '';
  }
}
```

**Cost control：**
- `tts_cap` 限制 max_tokens
- `cooldown_ms` 避免 LLM 被 spam
- DeepSeek 約 ¥1/1M tokens，30 字粵語 ≈ 60 tokens，
  1000 個觸發 = ¥0.06，唔肉赤

### 5.3 HTTP 整合（外部 KV）

```javascript
async function resolveHttpPhrase(rule) {
  const cacheKey = `http_phrase:${rule.id}:${rule.url}`;
  const cached = sessionStorage.getItem(cacheKey);
  if (cached) {
    const { ts, text } = JSON.parse(cached);
    if (Date.now() - ts < (rule.cache_ttl || 300) * 1000) return text;
  }

  try {
    const r = await fetch(rule.url);
    if (!r.ok) throw new Error('http ' + r.status);
    const data = await r.json();
    const text = data[rule.field] || rule.fallback || '';
    sessionStorage.setItem(cacheKey, JSON.stringify({ ts: Date.now(), text }));
    return text;
  } catch (e) {
    return rule.fallback || '';
  }
}
```

適合場景：個人化招呼語（用戶名 / 喜好）、A/B test 文案、
從 CF KV / Supabase / Notion 拉。

---

## 6. 執行層 — TTS 路由

widget 已經有 `speak()` 同 `speakBrowser()` + `speakNeural()`，
需要擴展 `speakWithRoute()` 支援 per-call 嘅 voice 設定。

```javascript
function speakWithRoute({ text, voice, voice_id, emotion, gesture, tts_cap }) {
  if (!text) return;
  if (text.length > (tts_cap || 200)) text = text.slice(0, tts_cap);

  if (emotion) {
    if (typeof window.applyEmotion === 'function') {
      window.applyEmotion(emotion);
    }
  }
  if (gesture) {
    triggerAction('gesture:' + gesture);  // 或 model.expression
  }

  const useVoice = voice || defaults.voice || 'browser';
  if (useVoice === 'minimax' && voice_id) {
    NEURAL_VOICE = voice_id;  // 暫時覆蓋
    speakNeural(text);        // 內部用 NEURAL_VOICE call MiniMax
  } else {
    speakBrowser(text);
  }
}
```

> 警告：直接 `NEURAL_VOICE = voice_id` 會影響之後嘅 speak。
> 如果要嚴格 scope per-rule，要用 call-by-call 嘅 `voice_id`
> override 傳入 `fetchMinimaxTtsDirect()`。Phase 1 簡化版可以
> 容許呢個 leak，因為同一個 rule 嘅 LLM 通常都會一路用同一個 voice。

---

## 7. 設定 UI — Settings 新 Tab

### 7.1 整合去 Dev Mode Panel

跟 `plans/dev-mode-settings-plan.md` 嘅 4 個 tab 一致，
新加 **第 5 個 tab「Hooks」**：

```text
一般  │ 模型  │ 對話  │ 診斷  │ [Hooks ★]   ← 新
─────────────────────────────────────
[YAML 編輯區域（textarea）]
   ┌──────────────────────────────────────┐
   │ version: 1                           │
   │ rules:                               │
   │   - id: greet                        │
   │     trigger: boot                    │
   │     steps:                           │
   │       - say: "你好"                  │
   │                                      │
   └──────────────────────────────────────┘

[Validate YAML] [Test run] [Clear all rules] [Import from URL]

Status:
  ✓ Parsed 3 rules
  ✓ Boot listener installed
  ✓ Scroll listener installed (id: scroll-near-bottom)
  ✗ HTTP source skipped (no API key)
```

### 7.2 設定儲存

```javascript
const KEY_RULES = 'vampire_widget_rules_v1';

// 儲存
try { localStorage.setItem(KEY_RULES, yamlText); } catch (e) {}

// 讀取
let rulesYaml = '';
try { rulesYaml = localStorage.getItem(KEY_RULES) || ''; } catch (e) {}

// 啟動時 parse
if (rulesYaml) installRulesFromYaml(rulesYaml);
```

### 7.3 YAML 解析方案

**Option A：js-yaml CDN（推薦）**
- `<script src="https://cdn.jsdelivr.net/npm/js-yaml@4.1.0/dist/js-yaml.min.js">`
- 12 KB minified
- 成熟 battle-tested

**Option B：自寫 tiny parser**
- 只支援 subset（key: value, list `-`, block scalar `|`）
- ~50 行 code，0 KB
- 適合驚 CSP 嘅極端 case

**推薦：** Option A，CDN 已喺 widget vendor dir。
如怕 CDN 故障，可以 vendor 一份。

---

## 8. 分階段實作 plan

### Phase 1 — 基礎 postMessage（1 個 commit）

**Goal：** parent 可以 trigger 動作 / 表情 / 道具 / say，無 YAML

**Step：**
1. 加 `window.message` listener 處理 4 個 type（say / emote / action / sequence）
2. 寫 `speakWithRoute()` 支援 per-call voice
3. 寫 `runSequence()` 順序執行 steps
4. Test snippet：父頁 inline JS 撳 button → 觸發 widget knife + 「你好」

**交付：** `feat(widget): external event postMessage API`
**風險：** 低，純加 listener，唔影響現有功能

### Phase 2 — YAML Rules Engine（1 個 commit）

**Goal：** 支援 YAML 規則，安裝 listener

**Step：**
1. vendor `js-yaml.min.js` 落 `backend/static/embed/vendor/`
2. 寫 `installRulesFromYaml(yamlText)` 解析 + 註冊 listeners
3. 支援 5 個 trigger：boot / scroll_pct / idle / host_event / dom_event
4. Settings modal 加新 tab「Hooks」+ textarea
5. Test：paste YAML 包含 1 條 boot rule，reload 確認觸發

**交付：** `feat(widget): YAML rules engine for host events`
**風險：** 中，YAML edge cases 多

### Phase 3 — LLM / HTTP Phrase（1 個 commit）

**Goal：** `say.source: llm` 同 `say.source: http` work

**Step：**
1. 寫 `resolveLlmPhrase(rule, context)` （DeepSeek API call）
2. 寫 `resolveHttpPhrase(rule, context)` （fetch + cache）
3. 喺 `runSequence` 入面 detect `source` field dispatch
4. LLM call 嘅 DeepSeek key 由現有 `localStorage.deepseek_key` 攞
5. Test：trigger 一條 LLM rule，confirm phrase 出 + MiniMax TTS 讀出

**交付：** `feat(widget): dynamic phrase sources (LLM + HTTP)`
**風險：** 中，DeepSeek API error handling 要好

### Phase 4 — 完整 UI + Doc（1 個 commit）

**Goal：** Settings 入面完整 YAML editor + 即時 validate

**Step：**
1. Syntax highlight（可選，用簡單 regex）
2. 即時 parse + error 行數
3. 「Test run」按鈕手動 trigger 一條 rule
4. 「Import from URL」輸入 remote YAML URL
5. Doc：`docs/external-events-guide.md` 寫 parent 端 embed snippet + YAML spec

**交付：** `feat(widget): hooks UI polish + parent-side guide`

---

## 9. 完整 example — 嵌入 page 端

### 9.1 簡單版（只 trigger 動作）

```html
<iframe id="v" src="https://vampire.kitahim.uk/?embed=1"
        style="position:fixed;bottom:0;right:0;width:320px;height:480px;border:0;">
</iframe>
<script>
  const v = document.getElementById('v').contentWindow;
  document.body.addEventListener('click', (e) => {
    if (e.target.matches('.trigger-knife')) {
      v.postMessage({ ns:'avatar-widget-host', type:'action', name:'knife' }, '*');
    }
  });
</script>
```

### 9.2 完整版（用 YAML）

```html
<!-- Same iframe as above -->
<script>
  const v = document.getElementById('v').contentWindow;

  // 推送 YAML 規則
  fetch('/assets/vampire-rules.yaml').then(r => r.text()).then(yaml => {
    v.postMessage({ ns:'avatar-widget-host', type:'ruleset', yaml }, '*');
  });

  // 推送 context（例如登入用戶 ID）
  v.postMessage({
    ns:'avatar-widget-host',
    type:'host_event',
    name:'user_login',
    context: { user_id: 'abc123', name: 'Him' }
  }, '*');
</script>
```

對應 YAML 入面：

```yaml
- id: personalized-greet
  trigger: host_event
  when: "event.name === 'user_login'"
  steps:
    - say: "Hi {{context.name}}，好耐冇見！"
      voice: browser
      cooldown_ms: 60000
```

---

## 10. 風險 + 對策

| 風險 | 對策 |
|------|------|
| YAML parse error 中斷 widget | Try/catch 全部包住，parse fail 只 log warn |
| Parent 傳 malicious text（XSS） | `textContent` 寫入 bubble，絕對唔用 `innerHTML` |
| LLM cost 爆煲 | `tts_cap` + `cooldown_ms` + DeepSeek key 由 user 自備 |
| MiniMax voice_id 唔存在 | TTS call 失敗 fallback 返 `speakBrowser()` |
| scroll listener 影響 scroll perf | passive listener + rAF throttle |
| 多個 rule 同時 trigger race | sequence 入面逐個 await，前一個做完先落一個 |
| YAML 太大（>100 rules）影響 load | 加 size warning，>50KB 提示 user split |

---

## 11. 對比「全部 embed inline JS」vs「YAML」

| 維度 | inline JS | YAML |
|------|-----------|------|
| 寫低 | 1 個 rule 都要 30+ 行 JS | 1 個 rule 通常 5-10 行 |
| 維護 | 要 touch code base + redeploy | 純 paste + save |
| 動態 | 可以 | 可以 |
| 邏輯複雜 | 無限 | 受 schema 限 |
| 適合 | dev 寫客製行為 | 行銷 / content 同事寫流程 |

**結論：兩者並存。** Phase 1-2 嘅 postMessage API 已經夠用嚟做
inline JS 版本；YAML 係畀非技術 user 嘅薄包裝。

---

## 12. 預期時程

```text
Phase 1  (1-2 hr)   postMessage 4 個 type + runSequence
Phase 2  (2-3 hr)   YAML engine + Settings tab
Phase 3  (1-2 hr)   LLM + HTTP phrase source
Phase 4  (1-2 hr)   UI polish + parent-side doc

Total:   5-9 hr, 4 commits
```

每個 Phase 一個獨立 commit，每段都 production-safe
（failed parse 只 log warn，唔影響 boot）。

---

## 13. 開放問題（等用戶決定）

1. **YAML storage quota** — localStorage ~5MB / origin，
   100 rules 大約 30 KB，唔擔心。OK？

2. **LLM provider 限制** — Phase 3 預設用 DeepSeek（已有 key gate）。
   如果想 support OpenAI / Claude，要再 +1-2 hr。

3. **Trigger 種類 priority** — 我預設 5 個（boot / scroll / idle /
   host_event / dom_event）。要唔要加 mouse position、URL change
   （SPA）、visibility change（tab 切）？

4. **Sequence 限制** — 暫定每個 sequence max 20 steps，
   timeout 30s。多咗會 cancel + warn。要唔要鬆？

5. **語音 route per-rule 嘅 race** — 多個 rule 同時 trigger，
   點樣 queue？（簡單版：用現有 `speakSeq` counter，新嘅會
   cancel 舊嘅。）

---

## 14. 參考連結

- 既有 doc：`docs/vampire_widget_actions.md`（動作/道具 觸發 API）
- Dev Mode Panel plan：`plans/dev-mode-settings-plan.md`
- 對外 API 速查：`docs/deployment_spec.md`（部署 + BAZOOKA-free）
- MiniMax T2A v2 endpoint：`https://api.minimax.chat/v1/t2a_v2?group_id=...`
- DeepSeek endpoint：`https://api.deepseek.com/v1/chat/completions`

---

_草稿 v0.1。Review 完之後會 commit 落 git，
跟住開 Phase 1。_
