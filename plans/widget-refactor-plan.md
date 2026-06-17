# Widget.html 重構計劃

## 概述
將 4788+ 行的 `widget.html` 重構為使用模組化架構，提高代碼可維護性和可測試性。

## ✅ 已完成 (2026-06-17)

### 1. 模組導入和包裝器（第 788-869 行）
- 添加 ES 模組導入 `TtsService` 和 `SpeechService`
- 創建延遲初始化工廠函數 `getTtsService()` 和 `getSpeechService()`
- 導出全域包裝器：
  - `window.TtsService` - TTS 服務接口
  - `window.SpeechService` - 可選的標準 Web Speech API 封裝

### 2. TTS 功能重構（第 1774-1810 行）
- ✅ `speak()` 函數重構為調用 `TtsService.speak()`
- ✅ 添加 `stopSpeaking()` 和 `getTtsAudioMouth()` 包裝函數
- ✅ 移除重複函數：
  - ❌ `fetchMinimaxTtsDirect()` - 已遷移到 TtsService
  - ❌ `speakNeural()` - 已遷移到 TtsService
  - ❌ `speakBrowser()` - 已遷移到 TtsService

### 3. 語音識別策略
- ✅ 保持 `ReliableGoogleSpeech` 類（自動重連+語言鏈功能）
- ✅ 將 `SpeechService` 保留為可選的標準 Web Speech API 封裝
- ✅ 原有的 `startListening()` 和 `stopListening()` 邏輯保持不變

## 目標
- 使用 ES 模組導入 `TtsService` 和 `SpeechService`
- 保持向後兼容性（`window.TtsService` 全域對象）
- 移除重複的 TTS 和語音識別代碼
- 提高代碼可讀性和可維護性

## 架構設計

### 現有模組
1. **TtsService.js** - 完整的 TTS 功能
   - 後端代理 TTS
   - 直接 MiniMax API
   - 瀏覽器 Web Speech API
   - 嘴巴動畫同步

2. **SpeechService.js** - 語音識別功能
   - 瀏覽器 Web Speech API
   - 連續聆聽模式
   - 即時/最終結果處理

### 重構策略

#### 階段 1：模組導入和包裝器
位置：`<script type="module">` 塊

```javascript
import { TtsService } from './js/TtsService.js';
import { SpeechService } from './js/SpeechService.js';

// 延遲初始化服務實例
window._ttsService = null;
window._speechService = null;

// 獲取 TTS 服務（延遲初始化）
function getTtsService() { ... }

// 獲取 Speech 服務（延遲初始化）
function getSpeechService() { ... }

// 導出兼容性包裝器
window.TtsService = {
  speak: (text) => getTtsService().speak(text),
  stop: () => getTtsService().stop(),
  // ... 其他方法
};

window.SpeechRecognition = {
  start: () => getSpeechService().start(),
  stop: () => getSpeechService().stop(),
  // ... 其他方法
};
```

#### 階段 2：替換 TTS 功能

**需要移除的函數：**
- `fetchTtsProxy()` → 使用 `TtsService.fetchTtsProxy()`
- `fetchMinimaxTtsDirect()` → 使用 `TtsService.fetchMinimaxTtsDirect()`
- `speakNeural()` → 使用 `TtsService.speakNeural()`
- `speakBrowser()` → 使用 `TtsService.speakBrowser()`
- `speak()` → 重寫為調用 `window.TtsService.speak()`

**需要保留的函數：**
- `_ttsTruncate()` - 文本截斷邏輯
- `stopSpeaking()` - 停止動畫

**需要更新的狀態同步：**
- `isSpeaking` → `window.TtsService.getIsSpeaking()`
- `audioMouth` → `window.TtsService.getAudioMouth()`
- `ttsMode` → `window.TtsService.getMode()`

#### 階段 3：替換語音識別功能

**需要移除的函數：**
- `startListening()` → 使用 `SpeechService.start()`
- `stopListening()` → 使用 `SpeechService.stop()`
- 內聯的 `SpeechRecognition` 初始化邏輯

**需要保留的變量：**
- `listening` - UI 狀態標誌
- `interimTranscript` - 即時轉錄顯示

**需要更新的回調：**
- `onInterim` → 使用 `SpeechService.onInterim`
- `onFinal` → 使用 `SpeechService.onFinal`
- `onError` → 使用 `SpeechService.onError`

#### 階段 4：清理和驗證

**清理任務：**
- 移除未使用的變量
- 移除重複的語音目錄定義
- 統一錯誤處理

**驗證檢查點：**
1. TTS 神經模式正常播放音頻
2. TTS 瀏覽器模式正常工作
3. 語音識別開始/停止正常
4. 嘴巴動畫同步正常
5. 設置面板正確反映服務狀態
6. 回退機制正常（神經→瀏覽器）

## 文件結構

```
backend/static/embed/
├── widget.html          # 主文件（將重構）
├── widget_fixed.html     # 已有部分模組化（參考）
├── widget_clean.html     # 清理版本（原始）
├── widget_clean_v35.html # v35 清理版本
├── js/
│   ├── TtsService.js    # TTS 服務模組 ✓
│   └── SpeechService.js  # 語音識別服務模組 ✓
└── vendor/
    ├── live2dcubismcore.min.js
    ├── pixi.min.js
    └── cubism4.min.js
```

## 兼容性策略

### 全域 API
```javascript
// TTS 服務
window.TtsService = {
  speak(text),
  stop(),
  getMode(),
  setMode(mode),
  getNeuralVoice(),
  setNeuralVoice(voiceId),
  getVoiceCatalog(),
  getBrowserVoices(),
  hasMinimaxKey(),
  setMinimaxCredentials(key, groupId),
  getIsSpeaking(),
  getAudioMouth(),
  testMinimaxConnection(key, groupId),
  testBackendProxy()
};

// 語音識別服務
window.SpeechRecognition = {
  start(),
  stop(),
  isListening(),
  isSupported()
};
```

### 回調接口
```javascript
// 語音識別回調
SpeechService.onInterim = (transcript) => { ... };
SpeechService.onFinal = (transcript) => { ... };
SpeechService.onStart = () => { ... };
SpeechService.onEnd = () => { ... };
SpeechService.onError = (error) => { ... };
```

## 風險和緩解

### 風險 1：CORS 和跨域問題
- **緩解**：使用後端代理端點 `/api/tts-proxy`

### 風險 2：舊瀏覽器不支持 ES 模組
- **緩解**：主要目標瀏覽器（Chrome、Edge、Safari、Firefox）都支持 ES 模組

### 風險 3：localStorage 跨域隔離
- **緩解**：服務實例在正確的域上下文中初始化

### 風險 4：嘴巴動畫同步丟失
- **緩解**：保持 `getAudioMouth()` 接口和動畫循環

## 時間估算
- 階段 1：15 分鐘
- 階段 2：45 分鐘
- 階段 3：30 分鐘
- 階段 4：30 分鐘
- **總計**：約 2 小時

## 測試清單
- [ ] 直接 URL 訪問 widget
- [ ] 嵌入模式（iframe）運行
- [ ] TTS 神經語音播放
- [ ] TTS 瀏覽器語音播放
- [ ] 語音識別開始/停止
- [ ] 麥克風權限處理
- [ ] 設置面板保存/載入
- [ ] DeepSeek API 串流回應
- [ ] 表情和動作觸發
- [ ] 緊急回應關鍵詞觸發
