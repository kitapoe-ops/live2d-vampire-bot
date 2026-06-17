# 🌙 吸血鬼 WebUI 美化計劃

**目標：** 美化 https://vampire.kitahim.uk/ 入口頁，重新撰寫介紹和功能說明  
**範圍：** `dist-pages/index.html`（入口頁）  
**語言支援：** 繁體中文 / 簡體中文 / English  
**最後更新：** 2026-06-17

---

## 0. 多語言架構

### 🌐 語言切換方式
- **頂部導航欄：** 三個語言按鈕 [繁中] [简体] [EN]
- **自動偵測：** 根據瀏覽器語言自動選擇（可覆寫）
- **本地存儲：** 用戶選擇記錄在 localStorage，下次訪問記住偏好

### 📝 三語言內容對照表

| 區塊 | 繁體中文 | 簡體中文 | English |
|------|----------|----------|---------|
| 標題 | 🧛 吸血鬼 — 會說話的 AI 虛擬人助理 | 🧛 吸血鬼 — 会说话的 AI 虚拟人助理 | 🧛 Vampire — AI Virtual Assistant |
| 副標題 | 將智能虛擬人嵌入你的網站... | 将智能虚拟人嵌入你的网站... | Embed an intelligent virtual assistant... |
| 功能1 | 智能語音輸入 | 智能语音输入 | Smart Voice Input |
| 功能2 | 自然語音合成 | 自然语音合成 | Natural Voice Synthesis |
| 功能3 | AI 智能大腦 | AI 智能大脑 | AI Intelligence |
| 功能4 | 豐富表情動作 | 丰富表情动作 | Rich Expressions |
| 功能5 | 一行代碼嵌入 | 一行代码嵌入 | One-Line Embed |
| 功能6 | Reactive API | Reactive API | Reactive API |
| 按鈕-體驗 | 即時體驗 | 即时体验 | Try Now |
| 按鈕-代碼 | 查看代碼 | 查看代码 | View Code |
| 按鈕-BMAC | Buy me a coffee | Buy me a coffee | Buy me a coffee |

### 🔧 技術實現
```javascript
// 語言切換邏輯
const translations = {
  'zh-TW': { /* 繁體中文 */ },
  'zh-CN': { /* 簡體中文 */ },
  'en': { /* English */ }
};

// 自動偵測瀏覽器語言
const browserLang = navigator.language || navigator.userLanguage;
const defaultLang = browserLang.startsWith('zh-CN') ? 'zh-CN' : 
                    browserLang.startsWith('zh') ? 'zh-TW' : 'en';
```

---

## 1. 設計方向

### 🎨 視覺風格
- **主題：** 吸血鬼暗黑風 + 現代科技感
- **色彩方案：**
  - 主色：深紫 `#5b54e8` → 暗紫 `#1a1a2e`
  - 強調色：血紅 `#8B0000`、金色 `#FFD700`
  - 背景：深色漸變 `#0d0d1a` → `#1a1a2e`
  - 文字：`#e8e8e8`（淺色文字）、`#a0a0a0`（次要文字）

### 📐 佈局結構
```
┌─────────────────────────────────────────────┐
│  頂部導航欄                                    │
│  [🌙 Logo]          [繁中 | 简体 | EN]        │
├─────────────────────────────────────────────┤
│  HERO 區塊                                    │
│  ┌─────────────────────────────────────────┐ │
│  │ 🧛 吸血鬼 AI 虛擬人助理                   │ │
│  │ 副標題：一行介紹                           │ │
│  │ [即時體驗] [嵌入代碼] [☕ Support]        │ │
│  └─────────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│  功能展示區 (3列卡片)                          │
│  ┌───────┐ ┌───────┐ ┌───────┐            │
│  │ 🎤     │ │ 🗣️     │ │ 🧠     │            │
│  │ 語音輸入 │ │ 智能語音 │ │ AI 大腦 │            │
│  └───────┘ └───────┘ └───────┘            │
│  ┌───────┐ ┌───────┐ ┌───────┐            │
│  │ 🎭     │ │ 📦     │ │ 🔗     │            │
│  │ 表情動作 │ │ 一行嵌入 │ │ API    │            │
│  └───────┘ └───────┘ └───────┘            │
├─────────────────────────────────────────────┤
│  使用說明區                                   │
│  步驟式引導（重新編寫）                        │
├─────────────────────────────────────────────┤
│  技術特色區                                   │
│  標籤展示 + 嵌入範例                          │
├─────────────────────────────────────────────┤
│  API 測試區（保留 Reactive API Smoke Test）   │
├─────────────────────────────────────────────┤
│  FOOTER                                     │
│  [☕ Buy me a coffee]                       │
└─────────────────────────────────────────────┘
```

---

## 2. 重新撰寫的內容

### 🏠 Hero 區塊

**標題（繁中）：**
```
🧛 吸血鬼 — 會說話的 AI 虛擬人助理
```
**標題（簡中）：**
```
🧛 吸血鬼 — 会说话的 AI 虚拟人助理
```
**標題（EN）：**
```
🧛 Vampire — AI Virtual Assistant
```

**副標題（繁中）：**
```
將智能虛擬人嵌入你的網站，一行代碼即可擁有會聽、會說、會反應的 AI 助理
支援粵語、普通話，即刻提升用戶體驗
```
**副標題（簡中）：**
```
将智能虚拟人嵌入你的网站，一行代码即可拥有会听、会说、会反应的 AI 助理
支持粤语、普通话，即刻提升用户体验
```
**副標題（EN）：**
```
Embed an intelligent virtual assistant on your website with just one line of code.
Supports Cantonese and Mandarin, instantly elevates user experience.
```

**按鈕（繁中/簡中/EN）：**
| 繁中 | 簡中 | EN |
|------|------|-----|
| 💬 即時體驗 | 💬 即时体验 | 💬 Try Now |
| 📋 查看代碼 | 📋 查看代码 | 📋 View Code |
| ☕ Buy me a coffee | ☕ Buy me a coffee | ☕ Buy me a coffee |

---

### ✨ 功能展示（6 大核心功能）

#### 1. 🎤 智能語音輸入 / Smart Voice Input

| 繁中 | 簡中 | EN |
|------|------|-----|
| 告別打字時代 | 告别打字时代 | Say goodbye to typing |
| 支援中文、英文、粵語即時語音識別 | 支持中文、英文、粤语即时语音识别 | Supports Chinese, English, Cantonese speech recognition |
| 一鍵開始，隨時暫停 | 一键开始，随时暂停 | One-click start, pause anytime |

#### 2. 🗣️ 自然語音合成 / Natural Voice Synthesis

| 繁中 | 簡中 | EN |
|------|------|-----|
| 雙引擎 TTS 系統 | 双引擎 TTS 系统 | Dual-engine TTS system |
| 瀏覽器引擎：完全免費，無需任何設定 | 浏览器引擎：完全免费，无需任何设定 | Browser engine: 100% free, no setup |
| MiniMax 神經引擎：HD 粵語/普通話，12種聲線任選 | MiniMax 神经引擎：HD 粤语/普通话，12种声线任选 | MiniMax Neural: HD Cantonese/Mandarin, 12 voices |

#### 3. 🧠 AI 智能大腦 / AI Intelligence

| 繁中 | 簡中 | EN |
|------|------|-----|
| DeepSeek LLM 加持 | DeepSeek LLM 加持 | Powered by DeepSeek LLM |
| 理解上下文、生成自然回覆 | 理解上下文、生成自然回复 | Understands context, generates natural responses |
| 可選本地知識庫問答模式 | 可选本地知识库问答模式 | Optional local knowledge base Q&A mode |

#### 4. 🎭 豐富表情動作 / Rich Expressions

| 繁中 | 簡中 | EN |
|------|------|-----|
| 12種表情 + 4種手勢 | 12种表情 + 4种手势 | 12 expressions + 4 gestures |
| 開心、害羞、憤怒、驚訝... | 开心、害羞、愤怒、惊讶... | Happy, shy, angry, surprised... |
| 根據對話內容自動切換 | 根据对话内容自动切换 | Auto-switches based on conversation |

#### 5. 📦 一行代碼嵌入 / One-Line Embed

| 繁中 | 簡中 | EN |
|------|------|-----|
| 一行 script 標籤 | 一行 script 标签 | One script tag |
| 即可在任何網站展示吸血鬼助理 | 即可在任何网站展示吸血鬼助理 | Display the vampire assistant on any website |
| 支援自訂模型、聲線、知識庫 | 支持自订模型、声线、知识库 | Custom model, voice, and knowledge base |

#### 6. 🔗 Reactive API

| 繁中 | 簡中 | EN |
|------|------|-----|
| 與你的應用深度整合 | 与你的应用深度整合 | Deep integration with your app |
| postMessage 觸發表情、回覆、動作 | postMessage 触发表情、回复、动作 | Trigger expressions, replies, actions |
| 適合教育遊戲、客服系統、問答模塊 | 适合教育游戏、客服系统、问答模块 | Perfect for educational games, customer service, Q&A |

---

### 📖 使用說明（重新編寫）

| 繁中 | 簡中 | EN |
|------|------|-----|
| **怎麼開始？** | **怎么开始？** | **How to Start?** |
| 1️⃣ 體驗虛擬人 | 1️⃣ 体验虚拟人 | 1️⃣ Try the Assistant |
| 滾動到頁面右下角，點擊吸血鬼開始對話 | 滚动到页面右下角，点击吸血鬼开始对话 | Scroll to bottom-right corner, click vampire to start |
| 2️⃣ 選擇輸入方式 | 2️⃣ 选择输入方式 | 2️⃣ Choose Input Method |
| 🎤 點擊麥克風用聲音提問 | 🎤 点击麦克风用声音提问 | 🎤 Click mic to speak |
| ⌨️ 或直接輸入文字 | ⌨️ 或直接输入文字 | ⌨️ Or type directly |
| 3️⃣ 切換語音模式 | 3️⃣ 切换语音模式 | 3️⃣ Switch Voice Mode |
| 🌐 免費模式：瀏覽器內建語音 | 🌐 免费模式：浏览器内置语音 | 🌐 Free mode: Browser built-in speech |
| 💎 HD 模式：MiniMax 神經語音（需 API Key） | 💎 HD 模式：MiniMax 神经语音（需 API Key） | 💎 HD mode: MiniMax Neural (needs API Key) |
| 4️⃣ 自訂設定 | 4️⃣ 自订设定 | 4️⃣ Customize Settings |
| ⚙️ 調整聲線、語速、表情靈敏度 | ⚙️ 调整声线、语速、表情灵敏度 | ⚙️ Adjust voice, speed, expression sensitivity |
| 5️⃣ 嵌入你的網站 | 5️⃣ 嵌入你的网站 | 5️⃣ Embed on Your Site |
| 複製一行代碼，吸血鬼即刻上線 | 复制一行代码，吸血鬼即刻上线 | Copy one line of code, vampire goes live |

---

### 🔧 技術棧展示

| 繁中 | 簡中 | EN |
|------|------|-----|
| Live2D Cubism 5.x | Live2D Cubism 5.x | Live2D Cubism 5.x |
| PIXI.js 渲染引擎 | PIXI.js 渲染引擎 | PIXI.js Rendering |
| 粵語/普通話 TTS | 粤语/普通话 TTS | Cantonese/Mandarin TTS |
| DeepSeek LLM | DeepSeek LLM | DeepSeek LLM |
| Web Speech API | Web Speech API | Web Speech API |
| MiniMax Neural | MiniMax Neural | MiniMax Neural |
| Cloudflare CDN | Cloudflare CDN | Cloudflare CDN |
| iframe 安全嵌入 | iframe 安全嵌入 | Secure iframe Embed |
| 一行 script | 一行 script | One-Line Script |

---

## 3. CSS 樣式改進

### 🌙 新增樣式變量
```css
:root {
  --vampire-dark: #0d0d1a;
  --vampire-purple: #5b54e8;
  --vampire-gold: #FFD700;
  --vampire-blood: #8B0000;
  --vampire-glow: rgba(91, 84, 232, 0.3);
}
```

### ✨ 動畫效果
- Hero 標題：打字機效果或淡入動畫
- 卡片：懸停時發光效果 (`box-shadow` glow)
- 按鈕：漸變動畫 + hover 上浮
- 背景：微妙的粒子/星星動畫（可選）

### 📱 響應式設計
- Desktop: 3列功能卡片
- Tablet: 2列卡片
- Mobile: 單列堆疊，字體縮放

---

## 4. 實現步驟

### Phase 1: 結構重構
- [ ] 添加頂部導航欄 + 語言切換器
- [ ] 添加 Hero 區塊
- [ ] 重組功能展示為 2x3 卡片式佈局
- [ ] 保留 Reactive API 測試區

### Phase 2: 樣式美化
- [ ] 更新 CSS 變量（暗黑吸血鬼主題）
- [ ] 實現卡片樣式和懸停發光動畫
- [ ] 優化按鈕漸變和交互效果
- [ ] 添加滾動視差效果

### Phase 3: 三語言內容
- [ ] 撰寫繁體中文文案
- [ ] 撰寫簡體中文文案
- [ ] 撰寫英文文案
- [ ] 實現 JavaScript 語言切換邏輯
- [ ] 添加 localStorage 記憶功能

### Phase 4: 測試優化
- [ ] 響應式測試（桌面/平板/手機）
- [ ] 三語言切換測試
- [ ] 動畫流暢度檢查
- [ ] 確保 widget 演示正常運作

---

## 5. 預期成果

### Before（當前）：
- 簡單的白色/淺色背景
- 基礎卡片佈局
- 平淡的技術說明

### After（美化後）：
- 暗黑吸血鬼主題
- 現代卡片 + 動畫效果
- 清晰的價值主張
- 專業的產品展示頁

---

## 6. 技術備註

- 所有修改將同步到 `dist-pages/index.html`
- `backend/static/viewer.html` 保持獨立（純模型查看器）
- 動畫使用 CSS `@keyframes` 避免 JavaScript 負擔
- 保持 `embed.js` 嵌入功能正常運作
