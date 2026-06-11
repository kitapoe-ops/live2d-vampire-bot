/**
 * DeepSeek Client — Browser 直接 call DeepSeek 雲端 API
 * 100% client-side，API key 只儲喺 localStorage
 * 
 * Flow:
 *   user message → system prompt + history → fetch DeepSeek
 *   → stream response → 解析 JSON → trigger Live2D
 */

class DeepSeekClient {
  constructor() {
    this.endpoint = 'https://api.deepseek.com/v1/chat/completions';
    this.model = 'deepseek-chat';
    this.apiKey = this._loadKey();
    this.history = [];  // 對話歷史
    this.maxHistory = 20;  // 最多 20 輪
  }

  // === API Key 管理 ===
  _loadKey() {
    return localStorage.getItem('vampire_deepseek_key') || '';
  }

  setKey(key) {
    this.apiKey = key;
    if (key) {
      localStorage.setItem('vampire_deepseek_key', key);
    } else {
      localStorage.removeItem('vampire_deepseek_key');
    }
  }

  hasKey() {
    return !!this.apiKey && this.apiKey.startsWith('sk-');
  }

  // === 對話歷史 ===
  clearHistory() {
    this.history = [];
  }

  // === 主要 call ===
  async chat(userMessage, systemPrompt, onChunk) {
    if (!this.hasKey()) {
      throw new Error('DeepSeek API key 未設定');
    }

    // 加 user message 入 history
    this.history.push({ role: 'user', content: userMessage });
    if (this.history.length > this.maxHistory) {
      this.history = this.history.slice(-this.maxHistory);
    }

    // 構建 messages
    const messages = [
      { role: 'system', content: systemPrompt },
      ...this.history
    ];

    const response = await fetch(this.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
      },
      body: JSON.stringify({
        model: this.model,
        messages: messages,
        temperature: 1.0,
        max_tokens: 500,
        stream: true,
        response_format: { type: 'json_object' }  // 強制 JSON output
      })
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`DeepSeek API 錯誤 ${response.status}: ${errText}`);
    }

    // Stream response
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullContent = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      fullContent += chunk;
      if (onChunk) onChunk(fullContent);
    }

    // 加 assistant response 入 history
    this.history.push({ role: 'assistant', content: fullContent });

    return fullContent;
  }

  // === 解析 JSON response ===
  static parseResponse(rawText) {
    // DeepSeek 有時會包 ```json ... ```，先 strip
    let cleaned = rawText.trim();
    cleaned = cleaned.replace(/^```json\s*/i, '');
    cleaned = cleaned.replace(/^```\s*/, '');
    cleaned = cleaned.replace(/```\s*$/, '');
    cleaned = cleaned.trim();

    try {
      const parsed = JSON.parse(cleaned);
      
      // 驗證必需 fields
      if (!parsed.text && !parsed.params) {
        throw new Error('Response 缺少 text 或 params');
      }
      
      return {
        text: parsed.text || '',
        params: parsed.params || {},
        expression: parsed.expression || null,
        motion: parsed.motion || null
      };
    } catch (e) {
      console.error('[DeepSeekClient] JSON parse failed:', e);
      console.error('[DeepSeekClient] Raw content:', rawText);
      // Fallback: 當 text response 處理
      return {
        text: rawText,
        params: {},
        expression: null,
        motion: null,
        parseError: true
      };
    }
  }
}

if (typeof window !== 'undefined') {
  window.DeepSeekClient = DeepSeekClient;
}
