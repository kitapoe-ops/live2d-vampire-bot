# Live2D 吸血鬼助理 (BAZOOKA fork)

> A fork of [YuriCrystal/ai-avatar-bot](https://github.com/YuriCrystal/ai-avatar-bot) for the
> BAZOOKA personal-cloud deployment. Drops a self-contained Live2D AI assistant on any
> website via a one-line `<script>` embed, with full control over TTS voice, LLM backend,
> and motion library.

## 🌙 與上游 (YuriCrystal/ai-avatar-bot) 嘅分別

| | 上游 | BAZOOKA fork |
|---|------|------------|
| TTS | Edge 非官方端點（README 自己列咗風險） | **MiniMax Cloud** 正式 API，11 個 curated voices（6 粵 + 5 普）|
| Backend | Vercel serverless | **FastAPI / uvicorn** |
| 部署 | 純 SaaS | 個人 PC + Cloudflare Tunnel |
| 對嘴 | Web Audio RMS | Web Audio RMS（相同）|
| 大腦 | DeepSeek / WebLLM | **DeepSeek**（max_tokens 200, 串流截斷, 情緒標籤過濾）|
| Model | Haru 範例 | **自訂吸血鬼模型**（含 10 秒完整 idle motion + 物理擺動）|
| Emotion | 冇 | `<neutral> <happy> <sad> <angry>...` tag 串流驅動 |
| 部署目標 | 任何靜態 host | **BAZOOKA 個人 PC** (`vampire.kitahim.uk`) |

皮肉分離哲學同上游一致 — **embed.js (loader) + widget.html (engine) + knowledge.js (content)**，配 data-* 換皮。

---

## 🏗 架構

```
┌─────────────────┐   postMessage    ┌────────────────────┐
│ Host page       │ <──────────────> │ iframe widget      │
│ <script>        │                  │  Live2D + STT/TTS  │
│  embed.js       │                  │  LLM  + knowledge  │
└─────────────────┘                  └────────────────────┘
                                            │
                                            ▼ fetch /api/tts, /api/voices
                                  ┌────────────────────┐
                                  │ FastAPI (uvicorn)  │
                                  │  MiniMax TTS proxy │
                                  │  voice catalog     │
                                  │  CORS allowlist    │
                                  └────────────────────┘
                                            │
                                            ▼
                                  ┌────────────────────┐
                                  │ MiniMax Cloud API  │
                                  │ speech-02-hd       │
                                  └────────────────────┘
```

---

## 🚀 快速部署

### 1. Backend (FastAPI)

```bash
cd backend
pip install fastapi uvicorn requests
export MINIMAX_API_KEY="sk-cp-..."
export MINIMAX_GROUP_ID="2031609952837050448"   # optional, defaults above
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

### 2. Frontend (embed)

Serve `backend/static/` via any static host (Caddy, nginx, Vercel, etc.), or use
the FastAPI app itself (it already mounts `/static`).

```html
<script src="https://your-host/static/embed/embed.js"
        data-model="https://your-host/static/live2d/your-model/your.model3.json"
        data-knowledge="https://your-host/static/embed/knowledge.js"
        data-api="https://your-host/api/tts"
        data-voice="cantonese-female"
        data-widget="widget.html"></script>
```

### 3. Model files

The Live2D model assets (`*.moc3`, `*.png`, motion files) are **not included**
in this repo for licensing reasons. Place your own model at
`backend/static/live2d/<your-model>/` and point `data-model` at its `model3.json`.

---

## 🎙 支援嘅 TTS Voices

`/api/voices` returns the full catalog. Friendly aliases:

| ID | Lang | 描述 |
|---|---|---|
| `cantonese-female` | zh-HK | 粵語女主持 (default) |
| `cantonese-male`   | zh-HK | 粵語男主持 |
| `cantonese-gentle` | zh-HK | 粵語溫柔女聲 |
| `cantonese-cute`   | zh-HK | 粵語可愛女孩 |
| `cantonese-playful` | zh-HK | 粵語活潑男聲 |
| `cantonese-kind`   | zh-HK | 粵語善良女聲 |
| `mandarin-female`  | zh-CN | 普通話甜美女聲 |
| `mandarin-male`    | zh-CN | 普通話男主播 |
| `mandarin-shaonv`  | zh-CN | 普通話少女音色 |
| `mandarin-yujie`   | zh-CN | 普通話御姐音色 |
| `mandarin-chengshu` | zh-CN | 普通話成熟女性 |

Azure voice names (e.g. `zh-TW-HsiaoChenNeural`, `zh-HK-HiuMaanNeural`) are also
auto-mapped. The widget's 🗣️ button cycles through voices with localStorage persistence.

---

## 🧠 DeepSeek integration

Default LLM. Set `DEEPSEEK_API_KEY` in browser localStorage (or via `data-ds-key`).

Hard limits to keep TTS clean:
- `max_tokens: 200` (≈ 150 Chinese chars)
- `temperature: 0.7`
- Stream terminates at first sentence boundary after 50 chars
- TTS cap 150 chars (smart-truncated at sentence boundary)

System prompt forces:
- 繁體中文
- 80–120 字，最多三句
- 句首情緒標籤 (`<happy> <sad> <angry> <surprised> <shy> <thinking> <neutral>`)
- No English, no Markdown, no simplified Chinese

---

## 🔧 Files

```
backend/
  app.py                    # FastAPI: /api/tts, /api/voices, /api/v1/...
  static/
    embed/
      embed.js              # One-line loader + iframe + window.AvatarWidget API
      index.html            # Landing page demo
      widget.html           # The actual avatar (Live2D + STT + TTS + LLM)
      knowledge.js          # 140 channels emotion + knowledge base
    live2d/<your-model>/    # ⛔ NOT IN REPO — supply your own
    viewer.html             # Local model viewer (test page)

frontend/                   # Optional hosted landing page assets
scripts/                    # Verify / Patch / Optimize / Parse model scripts
docs/                       # Deployment spec
```

---

## 📜 License

Fork code: MIT (matches upstream).

Third-party assets (Live2D Cubism Core, model files, MiniMax API) retain their own licenses.
This fork does not redistribute any model files; you must obtain your own.

---

## 🙏 Credits

- Upstream: [YuriCrystal/ai-avatar-bot](https://github.com/YuriCrystal/ai-avatar-bot) — original "皮肉分離" architecture
- Live2D Cubism SDK
- Pixi.js + pixi-live2d-display
- MiniMax TTS (speech-02-hd)
- DeepSeek chat completions
