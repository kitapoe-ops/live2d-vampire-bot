# 🦇 Vampire Live2D × DeepSeek (Client-side)

> **完全 100% client-side** 嘅 Live2D 虛擬人對話系統
> DeepSeek API key 100% 儲喺 browser localStorage，唔會上傳到任何 server

---

## 🏗️ 架構

```
User (Browser)
   │
   │ ① User input DeepSeek API key → localStorage
   │
   │ ② fetch() 直接 call DeepSeek 雲端 (CORS supported)
   ▼
[DeepSeek 雲端]
   │
   │ ③ Stream JSON: {text, params, expression, motion}
   ▼
[Browser JS]
   │
   │ ④ ParamMapper → setParameterValueById (174 params)
   ▼
[吸血鬼 Live2D model 喺 Canvas 顯示]
```

**核心特性：**
- ✅ **零後端**：純 static HTML/JS，直接 host 喺任何 static hosting
- ✅ **零 key 暴露**：API key 100% 喺 browser localStorage
- ✅ **M3 完全唔參與**：唔使 MiniMax API key
- ✅ **174 個 params 全可控**：DeepSeek 自主決定郁邊度
- ✅ **Smooth interpolation**：動作平滑過渡，唔會突跳
- ✅ **3 個 personality**：神秘高冷 / 嬌憨撒嬌 / 毒舌嘲諷

---

## 📁 File Structure

```
frontend/
├── index.html                    # 主入口
├── css/style.css                 # 暗色哥德風主題
├── js/
│   ├── app.js                    # 主 controller
│   ├── deepseek_client.js        # DeepSeek API client
│   ├── live2d_loader.js          # PIXI.js + Cubism 載入
│   ├── param_mapper.js           # JSON → Cubism params
│   ├── param_registry.js         # 174 params + 11 presets
│   └── system_prompts.js         # 3 個 personality prompts
└── live2d/                       # 吸血鬼 model assets (25 files, 11.47 MB)
    ├── 吸血鬼.moc3
    ├── 吸血鬼.2048/texture_*.png
    ├── 吸血鬼.model3.json
    ├── 吸血鬼.physics3.json
    └── *.exp3.json (12 emotion expressions)
```

---

## 🚀 部署

### Option A: Local Test (最快)

```powershell
cd C:\Users\kitap\.openclaw\workspace\live2d_xiaob\frontend
python -m http.server 8000
# 開 browser: http://localhost:8000
```

### Option B: Cloudflare Pages (推薦 — 取代 FastAPI backend)

```powershell
# 1. Install wrangler (如果未裝)
npm install -g wrangler

# 2. Login (會開 browser)
wrangler login

# 3. Deploy
cd C:\Users\kitap\.openclaw\workspace\live2d_xiaob\frontend
wrangler pages deploy . --project-name=vampire-frontend
# 會畀你一個 *.vampire-frontend.pages.dev URL
```

### Option C: 喺 vampire.kitahim.uk 直接 host

如果想用自己 domain（取代而家 FastAPI 8088 嘅 WS）：

1. **Setup Cloudflare Pages**:
   - Cloudflare Dashboard → Pages → Create
   - Connect GitHub repo OR Direct Upload
   - Project: `vampire-frontend`
   - Build: (留空，純 static)

2. **Custom domain**:
   - Pages project → Custom domains → Add `vampire.kitahim.uk`
   - Cloudflare 自動處理 DNS + certificate

3. **重啟 cloudflared** (本來 8088 → 8000):
   - `vampire.kitahim.uk` 而家指向 Cloudflare Pages，唔再需要 cloudflared
   - **可以 retire `backend/app.py` 同 cloudflared 服務**
   - **BAZOOKA 釋放返 port 8000**

---

## 🎭 3 個 Personality

| Personality | 口吻 | 常用表情 |
|------------|------|----------|
| `vampire_default` | 神秘高冷、500 歲艾娜 | neutral / sad / blood / wings |
| `vampire_cute` | 嬌憨撒嬌、小艾蘿莉 | hearteyes / shy / happy |
| `vampire_sadistic` | 毒舌嘲諷、薇爾莉特 | stareyes / angry / 嘴角歪 |

可喺 settings panel 切換。

---

## 🧪 E2E Test 流程

1. **開 browser** → 顯示 settings panel
2. **貼 DeepSeek API key**（sk- 開頭）→ Save & Enter
3. **吸血鬼 model 載入**（約 5-10 秒）
4. **喺 chat box 打「你好」** → Enter
5. **DeepSeek 回**：`{"text": "主人...你好", "params": {"PARAM_ANGLE_Y": 0.2, "PARAM_MOUTH_FORM": 0.4}}`
6. **吸血鬼微低頭 + 微笑**

---

## ⚠️ Security Notes

- ✅ DeepSeek API key **永遠唔出 browser**（fetch 直接 hit api.deepseek.com）
- ✅ 冇後端 proxy，所以 **冇 server-side log**
- ✅ localStorage 唔會 cross-device sync，user 換機要重新貼 key
- ⚠️ DeepSeek 嘅 CORS 政策：默認 **allow browser fetch**（已驗證 2026-06-11）
- ⚠️ 用戶要自己 trust DeepSeek 處理佢哋嘅對話內容

---

## 🐛 Troubleshooting

### Model 載入失敗
- Check `live2d/吸血鬼.model3.json` 嘅 FileReferences 指向 `.png` 同 `.moc3` 嘅 path
- Network tab check 有冇 404 嘅 texture

### DeepSeek API 錯誤 401
- API key 唔啱 / expired
- 重新貼新 key

### DeepSeek API 錯誤 429
- Rate limit，30 秒後 retry
- 或者升級 DeepSeek plan

### 吸血鬼唔郁
- Check console 有冇 `setParameterValueById` throw
- 確認 DeepSeek 返嘅係 valid JSON（用 `parseResponse` 嘅 parseError flag）

---

*最後更新：2026-06-11*
