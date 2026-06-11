/**
 * App — 主 controller
 * 處理：settings panel → main screen → chat loop
 */

(function() {
  'use strict';

  let deepseek = null;
  let live2d = null;
  let currentPersonality = 'vampire_default';

  // === DOM ready ===
  document.addEventListener('DOMContentLoaded', async () => {
    deepseek = new DeepSeekClient();

    // 檢查有冇 saved key
    if (deepseek.hasKey()) {
      // Skip settings panel
      showMainScreen();
    } else {
      showSettings();
    }

    bindEvents();
  });

  function bindEvents() {
    // Settings save
    document.getElementById('save-settings').addEventListener('click', () => {
      const key = document.getElementById('api-key').value.trim();
      currentPersonality = document.getElementById('character-name').value;
      if (!key || !key.startsWith('sk-')) {
        alert('請輸入有效嘅 DeepSeek API key（sk- 開頭）');
        return;
      }
      deepseek.setKey(key);
      localStorage.setItem('vampire_personality', currentPersonality);
      showMainScreen();
    });

    // Reset (clear key)
    document.getElementById('reset-btn').addEventListener('click', () => {
      if (confirm('清除 DeepSeek API key？')) {
        deepseek.setKey('');
        deepseek.clearHistory();
        showSettings();
      }
    });

    // Send chat
    document.getElementById('send-btn').addEventListener('click', sendMessage);
    document.getElementById('chat-input').addEventListener('keypress', (e) => {
      if (e.key === 'Enter') sendMessage();
    });
  }

  function showSettings() {
    document.getElementById('settings-panel').classList.remove('hidden');
    document.getElementById('main-screen').classList.add('hidden');
  }

  async function showMainScreen() {
    document.getElementById('settings-panel').classList.add('hidden');
    document.getElementById('main-screen').classList.remove('hidden');

    // 加 system message
    addChatMessage('system', '🦇 艾娜已經醒咗...請講嘢。');

    // Init Live2D
    try {
      setStatus('loading', '載入 Live2D model...');
      const canvas = document.getElementById('live2d-canvas');
      live2d = new Live2DLoader(canvas);
      await live2d.init();
      setStatus('connected', '✓ Ready · DeepSeek connected');

      // 自動 idle reaction
      setTimeout(() => {
        if (live2d && live2d.paramMapper) {
          live2d.paramMapper.setTarget({
            'PARAM_ANGLE_X': 0.2,
            'PARAM_MOUTH_FORM': 0.3,
            'PARAM_EYE_L_SMILE': 0.3
          });
          setTimeout(() => { live2d.paramMapper.targetParams = {}; }, 1500);
        }
      }, 1500);

    } catch (e) {
      setStatus('error', '❌ Live2D 載入失敗: ' + e.message);
      console.error(e);
    }

    // Resize handler
    window.addEventListener('resize', () => {
      if (live2d) live2d.resize();
    });
  }

  async function sendMessage() {
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text) return;
    input.value = '';

    addChatMessage('user', text);

    try {
      setStatus('thinking', '艾娜諗緊...');

      const systemPrompt = SYSTEM_PROMPTS[currentPersonality] || SYSTEM_PROMPTS.vampire_default;
      
      // Stream response
      let rawResponse = '';
      const response = await deepseek.chat(text, systemPrompt, (chunk) => {
        rawResponse = chunk;
      });

      // Parse JSON
      const parsed = DeepSeekClient.parseResponse(response);
      
      if (parsed.parseError) {
        addChatMessage('system', '⚠️ LLM response 唔係有效 JSON。請 retry。');
        console.error('Raw:', response);
      } else {
        addChatMessage('character', parsed.text);
        
        // Trigger Live2D
        if (live2d && live2d.paramMapper) {
          live2d.paramMapper.applyResponse(parsed);
        }

        console.log('[app] Applied:', parsed);
      }

      setStatus('connected', '✓ Ready · DeepSeek connected');

    } catch (e) {
      console.error('[app] Chat error:', e);
      setStatus('error', '❌ ' + e.message);
      addChatMessage('system', '❌ 錯誤: ' + e.message);
    }
  }

  function addChatMessage(role, text) {
    const div = document.createElement('div');
    div.className = 'message ' + role;
    div.textContent = text;
    document.getElementById('chat-messages').appendChild(div);
    
    // Auto scroll
    const container = document.getElementById('chat-messages');
    container.scrollTop = container.scrollHeight;
  }

  function setStatus(type, text) {
    const status = document.getElementById('status');
    status.className = type;
    status.textContent = text;
  }

})();
