# 🧛 吸血鬼少女 — AI 虛擬人助理

> 基於 Live2D Cubism 5 的互動式虛擬角色，搭載 DeepSeek AI 大腦與雙引擎語音系統。
> 一行程式碼即可嵌入任何網站，讓你的網頁擁有會聽、會說、會反應的 AI 夥伴。

<p align="center">
  <a href="https://vampire.kitahim.uk/" target="_blank" rel="noopener">
    <img src="https://img.shields.io/badge/Live%20Demo-vampire.kitahim.uk-8b5cf6?style=for-the-badge&logo=cloudflare&logoColor=white" alt="Live Demo" />
  </a>
  <a href="https://github.com/kitahim/vampire-live2d" target="_blank" rel="noopener">
    <img src="https://img.shields.io/badge/Source-GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub" />
  </a>
  <a href="https://www.buymeacoffee.com/kitahim" target="_blank" rel="noopener">
    <img src="https://img.shields.io/badge/Donate-Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black" alt="Buy Me A Coffee" />
  </a>
</p>

---

## ✨ 功能亮點

| 功能 | 說明 |
|------|------|
| 🖼️ **Live2D 動態模型** | Cubism 5 原生渲染，流暢表情切換與肢體動作，支援多種表情參數與物理效果 |
| 🧠 **DeepSeek AI 大腦** | 整合 DeepSeek 語言模型，支援上下文對話與知識庫檢索 |
| 🎙️ **雙引擎語音** | 瀏覽器 Web Speech API（免費）或 MiniMax Neural TTS（HD 粵語/國語，12 種聲線） |
| 🌐 **跨平台嵌入** | 透過 `<script>` 或 `<iframe>` 嵌入任何網站，支援自訂位置、尺寸、主題與語言 |
| ⚡ **Reactive API** | 透過 `postMessage` 與虛擬人即時互動，支援日記模式、隨堂測驗、重置對話 |
| 🔒 **安全可靠** | CSP 安全標頭、連線限制、速率控制，支援 Cloudflare Access 整合 |

---

## 🌐 多語言入口頁面

入口頁面 ([`vampire.kitahim.uk`](https://vampire.kitahim.uk/)) 支援三種語言即時切換：

- **繁體中文** (zh-TW)
- **簡體中文** (zh-CN)
- **English** (en)

自動偵測瀏覽器語言，手動切換後儲存至 `localStorage`。

---

## 🏗 架構

```
┌─────────────────┐   postMessage    ┌──────────────────────────┐
│ Host page       │ <──────────────> │ iframe widget.html       │
│ <script>        │                  │  Live2D Cubism 5        │
│  embed.js       │                  │  Web Speech API / STT   │
│  index.html     │                  │  MiniMax TTS            │
│  (landing)      │                  │  DeepSeek LLM           │
└─────────────────┘                  │  knowledge.js           │
                                     └──────────────────────────┘
                                               │
                                               ▼ fetch /api/tts, /api/voices
                                     ┌──────────────────────────┐
                                     │ FastAPI (uvicorn)        │
                                     │  MiniMax TTS proxy       │
                                     │  Voice catalog           │
                                     │  CSP headers             │
                                     │  Connection rate limit   │
                                     └──────────────────────────┘
                                               │
                                               ▼
                                     ┌──────────────────────────┐
                                     │ MiniMax Cloud API        │
                                     │ speech-02-hd             │
                                     └──────────────────────────┘
```

### 部署架構

```
┌──────────┐    Cloudflare Tunnel     ┌───────────┐
│ Browser  │ ──────────────────────>  │  Backend  │
│          │    wss://tunnel          │  FastAPI  │
│ CF Pages │    https://backend:8000  │  :8000    │
│ :443     │                          │           │
└──────────┘                          └───────────┘
     │                                      │
     │ Cloudflare Pages                     │ MiniMax API
     │ (static: index.html,                 │ DeepSeek API
     │  embed.js, widget.html,              │
     │  Live2D model)                       │
     ▼                                      ▼
┌──────────┐                       ┌───────────────┐
│ CF Edge  │                       │ External APIs │
└──────────┘                       └───────────────┘
```

---

## 🚀 快速開始

### 1. 一行嵌入

將以下程式碼貼到任何 HTML 頁面的 `<body>` 中：

```html
<div id="vampire-live2d-root"></div>
<script src="https://vampire.kitahim.uk/embed.js"
        data-live2d-widget
        data-position="bottom-right"
        data-size="280"
        data-theme="dark"
        data-greeting="你好，我是吸血鬼少女！"
        data-lang="zh-TW"
        defer></script>
```

### 2. 可用參數

| 參數 | 說明 | 預設值 |
|------|------|--------|
| `data-position` | 位置：`bottom-right` / `bottom-left` / `top-right` / `top-left` | `bottom-right` |
| `data-size` | Widget 寬度 (px) | `280` |
| `data-theme` | 主題：`dark` / `light` | `dark` |
| `data-greeting` | 自訂初次見面問候語 | — |
| `data-lang` | 語言：`zh-TW` / `zh-CN` / `en` | `zh-TW` |
| `data-backend` | 自訂後端 URL（可選） | — |

### 3. 後端部署 (FastAPI)

```bash
cd backend
pip install fastapi uvicorn requests
set MINIMAX_API_KEY=<your_minimax_api_key>
set MINIMAX_GROUP_ID=<your_minimax_group_id>
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

### 4. Cloudflare Pages 部署

```bash
# 安裝 wrangler
npm install -g wrangler

# 登入 Cloudflare
wrangler login

# 構建並部署
python build_pages_dist.py
wrangler pages deploy dist-pages --project-name vampire-widget
```

---

## 🎙 支援的 TTS 語音

`/api/voices` 回傳完整語音目錄。常用別名：

| ID | 語言 | 描述 |
|----|------|------|
| `cantonese-female` | zh-HK | 粵語女主持 (default) |
| `cantonese-male` | zh-HK | 粵語男主持 |
| `cantonese-gentle` | zh-HK | 粵語溫柔女聲 |
| `cantonese-cute` | zh-HK | 粵語可愛女孩 |
| `cantonese-playful` | zh-HK | 粵語活潑男聲 |
| `cantonese-kind` | zh-HK | 粵語善良女聲 |
| `mandarin-female` | zh-CN | 普通話甜美女聲 |
| `mandarin-male` | zh-CN | 普通話男主播 |
| `mandarin-shaonv` | zh-CN | 普通話少女音色 |
| `mandarin-yujie` | zh-CN | 普通話御姐音色 |
| `mandarin-chengshu` | zh-CN | 普通話成熟女性 |

Azure voice names（如 `zh-TW-HsiaoChenNeural`、`zh-HK-HiuMaanNeural`）也會自動映射。

---

## 🧠 DeepSeek 整合

預設 LLM。可透過瀏覽器 `localStorage` 或 `data-ds-key` 設定 `DEEPSEEK_API_KEY`。

限制參數以保持 TTS 清晰：
- `max_tokens: 200`（≈ 150 中文字）
- `temperature: 0.7`
- 串流在 50 字後的第一個句子邊界終止
- TTS 上限 150 字（在句子邊界智慧截斷）

System prompt 強制：
- 繁體中文（可依 `data-lang` 切換）
- 80–120 字，最多三句
- 句首情緒標籤（`<happy> <sad> <angry> <surprised> <shy> <thinking> <neutral>`）
- 無英文、無 Markdown

---

## 📁 專案結構

```
├── backend/
│   ├── app.py                    # FastAPI: /api/tts, /api/voices, /api/v1/...
│   └── static/
│       ├── embed/
│       │   ├── embed.js          # 一行載入器 + iframe + window.AvatarWidget API
│       │   ├── index.html        # 入口頁面（部署用）
│       │   ├── widget.html       # 虛擬人引擎（Live2D + STT + TTS + LLM）
│       │   ├── knowledge.js      # 知識庫 + 情緒系統
│       │   └── js/               # 模組化 JS（SpeechService, TtsService, index）
│       ├── live2d/<your-model>/  # ⛔ 不包含在 repo 中 — 自行提供
│       └── viewer.html           # 本地模型檢視器
├── dist-pages/                   # Cloudflare Pages 部署目錄（gitignored）
│   ├── index.html                # 美化版入口頁面（三語言支援）
│   ├── widget.html               # 部署用 widget
│   ├── embed.js                  # 部署用 loader
│   └── live2d/vampire/           # Live2D 模型靜態檔
├── scripts/                      # 驗證 / 修補 / 最佳化 / 解析模型腳本
├── docs/
│   └── deployment_spec.md        # 部署規格文件
├── plans/                        # 功能規劃與重構計畫
├── build_pages_dist.py           # Pages 部署建構腳本
├── deploy_pages.ps1              # 一鍵部署 PowerShell 腳本
└── wrangler.toml                 # Cloudflare Pages 設定
```

---

## 🔧 與上游的差異

本專案 fork 自 [YuriCrystal/ai-avatar-bot](https://github.com/YuriCrystal/ai-avatar-bot)，主要差異：

| 項目 | 上游 | 本專案 |
|------|------|--------|
| TTS | Edge 非官方端點 | **MiniMax Cloud** 正式 API，11 個 curated voices |
| Backend | Vercel serverless | **FastAPI / uvicorn** |
| 部署 | 純 SaaS | 個人 PC + Cloudflare Tunnel |
| 對嘴 | Web Audio RMS | Web Audio RMS（相同） |
| 大腦 | DeepSeek / WebLLM | **DeepSeek**（max_tokens 200, 串流截斷, 情緒標籤過濾） |
| Model | Haru 範例 | **自訂吸血鬼模型**（含 10 秒完整 idle motion + 物理擺動） |
| Emotion | 無 | `<neutral> <happy> <sad> <angry>...` tag 串流驅動 |
| 入口頁面 | 基本 HTML | **暗黑吸血鬼主題**，三語言支援，動畫背景，響應式設計 |

皮肉分離哲學一致 — **embed.js (loader) + widget.html (engine) + knowledge.js (content)**，配 `data-*` 換皮。

---

## ☕ 撐腰一下

如果這個 widget 對你有幫助，請我飲杯咖啡支持繼續開發：

<a href="https://www.buymeacoffee.com/kitahim" target="_blank" rel="noopener noreferrer">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="180" />
</a>

👉 **[https://www.buymeacoffee.com/kitahim](https://www.buymeacoffee.com/kitahim)**

所有捐款會用於 MiniMax TTS API、DeepSeek API、Cloudflare Pages 升級、Live2D 授權等開支。多謝支持！🧛‍♂️☕

---

## 📜 License

Fork code: MIT（與上游一致）。

第三方資產（Live2D Cubism Core、模型檔案、MiniMax API）保留其各自授權。本專案不重新分發任何模型檔案；您需要自行取得。

## 🙏 Credits

- 上游：[YuriCrystal/ai-avatar-bot](https://github.com/YuriCrystal/ai-avatar-bot) — 原始「皮肉分離」架構
- Live2D Cubism SDK
- Pixi.js + pixi-live2d-display
- MiniMax TTS (speech-02-hd)
- DeepSeek chat completions
