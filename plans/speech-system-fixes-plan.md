# 語音識別系統修復計劃

## 問題概述

根據架構審查發現以下四大類問題需要修復：

### 1. 邏輯與容錯機制漏洞

| 問題 | 當前行為 | 正確行為 |
|------|---------|---------|
| `network` 錯誤自動切換語言 | 網路斷線時切換到 `zh-CN` 或 `en-US` | **原地重試，保持當前語言** |
| `no-speech` 自動切換語言 | 無聲時自動切換到下一個語言 | **保持當前語言，重新聆聽** |

### 2. Echo 反饋問題

| 問題 | 當前行為 | 正確行為 |
|------|---------|---------|
| TTS 播放時麥克風未靜音 | TTS 播放中可能錄到自己的聲音 | **TTS 播放時靜音麥克風** |

### 3. API Key 安全問題

| 問題 | 當前行為 | 正確行為 |
|------|---------|---------|
| MiniMax TTS 直連 | 前端直接呼叫 MiniMax API | **透過後端 Proxy 呼叫** |

### 4. 程式碼重構

| 問題 | 當前行為 | 正確行為 |
|------|---------|---------|
| 巨型單一檔案 | widget.html 達到 3700+ 行 | **抽取獨立模組** |

---

## 修復清單

- [x] 修復 network 錯誤邏輯：不換語言，原地重試
- [x] 修復 no-speech 處理：保持當前語言，不自動切換
- [x] API Key 安全：將 MiniMax TTS 移至後端 Proxy
  - [x] 添加 `/api/tts-proxy` 端點至 backend/app.py
  - [x] 修改前端優先使用後端 proxy
- [x] 程式碼重構：創建獨立 JS 模組
  - [x] 創建 TtsService.js
  - [x] 創建 SpeechService.js
  - [x] 創建 js/index.js 入口文件
- [x] 更新 iOS Safari 文件：修正支援狀態描述
- [ ] 同步更新 dist-pages 版本
- [ ] Echo 反饋修復：TTS 播放時靜音麥克風（需更多時間）

---

## 詳細實作步驟

### Step 1: 修復 network 和 no-speech 邏輯

**檔案**: `backend/static/embed/widget.html`

```javascript
// BEFORE (錯誤):
if (e.error === 'no-speech' && this.langIndex < this.langChain.length - 1) {
  this.langIndex++;  // 自動切換語言 ❌
  this.recognition.lang = this.langChain[this.langIndex];
}

// AFTER (正確):
if (e.error === 'no-speech') {
  // 保持當前語言，直接重新聆聽 ✅
  console.warn('[ReliableGoogleSpeech] no-speech - restarting with same language:', this.langChain[this.langIndex]);
  try { this.recognition.stop(); } catch (e) {}
  try { this.recognition.start(); } catch (e) {}
}
```

### Step 2: 修復 Echo 反饋

**檔案**: `backend/static/embed/widget.html`

在 `speakBrowser()` 和 `speakNeural()` 函數中，TTS 開始播放時靜音麥克風，播放結束後恢復。

```javascript
// 在 speakBrowser/speakNeural 開始時
if (listening) {
  speech.stop();
  setMic(false);  // 靜音麥克風
}

// 在 TTS onend 回調中
u.onend = () => {
  // TTS 播放結束後，恢復麥克風
  setMic(true);
  // 可選：自動恢復聆聽
};
```

### Step 3: API Key 安全 (後端 Proxy)

**檔案**: `backend/app.py`

添加新的 Proxy 端點：

```python
@app.post("/api/tts-proxy")
async def tts_proxy(text: str = Body(...), voice: str = Body(...)):
    """MiniMax TTS Proxy - 保護 API Key"""
    api_key = os.getenv("MINIMAX_API_KEY")
    # ... 呼叫 MiniMax 並返回音頻
```

前端改為呼叫 `/api/tts-proxy` 而非直接呼叫 MiniMax。

### Step 4: 程式碼重構

建議的模組結構：

```
static/embed/
├── widget.html          # 主 HTML（保持 UI 結構）
├── js/
│   ├── speech/
│   │   ├── ReliableGoogleSpeech.js   # 語音識別類
│   │   ├── AudioRecorder.js          # 音頻錄製
│   │   └── index.js                 # 導出
│   ├── tts/
│   │   ├── TtsService.js            # TTS 服務抽象層
│   │   ├── BrowserTts.js           # 瀏覽器 TTS 實現
│   │   ├── MiniMaxTts.js           # MiniMax TTS 實現
│   │   └── index.js                 # 導出
│   └── main.js                      # 入口點
└── css/
    └── widget.css                   # 樣式抽取
```

### Step 5: iOS Safari 文件更新

**檔案**: `plans/speech-system-fixes-plan.md`

改為：
> iOS Safari 支援 Web Speech API (`webkitSpeechRecognition`)，但在 iframe 巢狀環境下有嚴格的權限與原生手勢限制，需特別處理觸發時機。

---

## Mermaid 流程圖：修復後的 Error Handling

```mermaid
flowchart TD
    A[SpeechRecognition Error] --> B{error type}
    B -->|no-speech| C[保持當前語言<br/>直接重新聆聽]
    B -->|network| D{retryCount < 3?}
    B -->|not-allowed| E[顯示麥克風權限提示]
    B -->|其他| F[顯示錯誤警告]
    
    D -->|是| G[原地重試<br/>不換語言]
    G --> H[等待 1.5 秒]
    H --> I[重啟 recognition]
    I --> J[錯誤計數 +1]
    J --> A
    
    D -->|否| K[顯示網絡錯誤提示]
    
    C --> L[聆聽中]
    E --> L
    F --> L
    K --> M[重置計數]