# TTS 模組化重構 - 兼容性測試計劃

## 測試環境準備

### 測試文件位置
- 主測試文件: `dist-pages/widget_fixed.html`
- TTS 服務模組: `js/TtsService.js`
- 語音服務模組: `js/SpeechService.js`
- 部署後端: `backend/static/embed/`

### 本地測試
```bash
# 啟動後端服務器
cd backend
python app.py

# 訪問測試頁面
# http://localhost:3000/static/embed/widget_fixed.html
```

---

## 測試矩陣

### 1. TTS 模式測試

| 模式 | 測試場景 | 預期結果 | 測試方法 |
|------|----------|----------|----------|
| **Browser (預設)** | 正常說話 | 瀏覽器語音播放 | 點擊按鈕觸發 speak() |
| **Browser** | 靜音模式 | 無音頻播放 | 設置 ttsMuted=true |
| **Neural (MiniMax)** | 有後端 API Key | 通過後端代理播放音頻 | 檢查 Network 標籤 |
| **Neural** | 無 API Key + Neural 模式 | 提示用戶輸入 Key | 檢查 Modal 彈出 |
| **Neural** | API Key 無效 | 顯示錯誤訊息 | 檢查 Console |
| **Neural → Browser 回退** | Neural 失敗時 | 自動切換到 Browser TTS | 故意中斷後端連接 |

### 2. 語音類型測試

| 語音 ID | 語言 | 預期行為 |
|---------|------|----------|
| cantonese-female | 粵語 | 正常播放 |
| cantonese-male | 粵語 | 正常播放 |
| cantonese-cute | 粵語 | 正常播放 |
| mandarin-female | 普通話 | 正常播放 |
| mandarin-male | 普通話 | 正常播放 |

### 3. 後端代理測試

```bash
# 測試後端 TTS 代理端點
curl -X POST http://localhost:3000/api/tts-proxy \
  -H "Content-Type: application/json" \
  -d '{"text": "測試", "voice": "cantonese-female", "speed": 1.0}'

# 預期: 返回音頻文件 (audio/mpeg)
```

### 4. 語音識別測試 (SpeechService)

| 測試場景 | 預期結果 |
|----------|----------|
| 瀏覽器支援 Web Speech API | 正常啟動識別 |
| 瀏覽器不支援 | 顯示警告，不崩潰 |
| 連續聆聽模式 | 正確處理 interim/final transcript |
| 語言設置 | 正確切換 zh-HK/zh-CN/en-US |

---

## 自動化測試腳本

### smoke_test_mobile_mic.py (現有)
```python
# 測試麥克風權限和語音識別
python smoke_test_mobile_mic.py
```

### 新增測試檢查清單

```javascript
// 在瀏覽器 Console 中執行
console.log('=== TTS 模組測試 ===');

// 1. 檢查模組是否加載
console.log('TtsService:', typeof window.TtsService);
console.log('SpeechService:', typeof window.SpeechRecognition);

// 2. 檢查方法可用性
console.log('TtsService.speak:', typeof window.TtsService.speak);
console.log('TtsService.stop:', typeof window.TtsService.stop);
console.log('TtsService.getMode:', typeof window.TtsService.getMode);

// 3. 測試 speak()
window.TtsService.speak('測試語音');
```

---

## 已知限制和注意事項

### 1. Browser TTS 音色匹配
widget_fixed.html 中的 `speakBrowser` 有特殊的 Windows Chrome 音色匹配邏輯 (v70 修復)。
如果瀏覽器 TTS 出現音色問題，需要保留該邏輯或將其整合到 TtsService.js 中。

### 2. MiniMax API Key 存儲
用戶的 MiniMax API Key 仍然存儲在 localStorage 中:
- `minimax_tts_key`
- `minimax_group_id`

### 3. 後端代理可用性
當後端 `/api/tts-proxy` 不可用時，系統會回退到:
1. 直接 MiniMax API (如果用戶有 key)
2. 瀏覽器 TTS

---

## 部署前檢查清單

- [ ] 本地測試所有 TTS 模式
- [ ] 測試語音識別功能
- [ ] 檢查瀏覽器 Console 無錯誤
- [ ] 測試移動設備兼容性
- [x] 同步更新 `backend/static/embed/` 中的文件 (2026-06-17)
- [x] 後端服務器運行測試 (2026-06-17) - 運行在 localhost:8000
- [x] TTS 代理端點測試 (2026-06-17) - /api/tts-proxy 返回 200 OK
- [x] 模組加載測試 (2026-06-17) - TtsService.js, SpeechService.js 可訪問
- [x] ES Module 導入結構驗證 (2026-06-17) - window.TtsService 和 window.SpeechRecognition 包裝器正常
