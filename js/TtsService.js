/**
 * TtsService.js - Text-to-Speech Service Module
 * 
 * Handles all TTS-related functionality including:
 * - Backend proxy TTS (secure, uses server-side API key)
 * - Direct MiniMax TTS (requires user-provided API key)
 * - Browser Web Speech API (free fallback)
 * - Voice catalog management
 * 
 * Usage:
 *   import { TtsService } from './js/TtsService.js';
 *   const tts = new TtsService(options);
 *   await tts.speak('你好');
 */

// Voice catalog - friendly aliases mapped to MiniMax voice_ids
export const VOICE_CATALOG = [
  { id: 'cantonese-female', lang: 'zh-HK', name: '粵語女主持 (Cantonese female host)', voice_id: 'Cantonese_GentleLady' },
  { id: 'cantonese-male', lang: 'zh-HK', name: '粵語男主持 (Cantonese male host)', voice_id: 'Cantonese_PlayfulMan' },
  { id: 'cantonese-gentle', lang: 'zh-HK', name: '粵語溫柔女聲 (Cantonese gentle lady)', voice_id: 'Cantonese_GentleLady' },
  { id: 'cantonese-cute', lang: 'zh-HK', name: '粵語可愛女孩 (Cantonese cute girl)', voice_id: 'Cantonese_CuteGirl' },
  { id: 'cantonese-playful', lang: 'zh-HK', name: '粵語活潑男聲 (Cantonese playful man)', voice_id: 'Cantonese_PlayfulMan' },
  { id: 'cantonese-kind', lang: 'zh-HK', name: '粵語善良女聲 (Cantonese kind woman)', voice_id: 'Cantonese_KindWoman' },
  { id: 'mandarin-female', lang: 'zh-CN', name: '普通話甜美女聲 (Mandarin sweet female)', voice_id: 'female-tianmei' },
  { id: 'mandarin-male', lang: 'zh-CN', name: '普通話男主播 (Mandarin male presenter)', voice_id: 'presenter_male' },
  { id: 'mandarin-shaonv', lang: 'zh-CN', name: '普通話少女音色 (Mandarin young girl)', voice_id: 'female-tianmei' },
  { id: 'mandarin-yujie', lang: 'zh-CN', name: '普通話御姐音色 (Mandarin mature lady)', voice_id: 'female-tianmei' },
  { id: 'mandarin-chengshu', lang: 'zh-CN', name: '普通話成熟女性 (Mandarin mature woman)', voice_id: 'female-tianmei' },
  { id: 'mandarin-announcer', lang: 'zh-CN', name: '普通話新聞男主播 (Mandarin news announcer)', voice_id: 'presenter_male' },
];

// Default voice
export const DEFAULT_VOICE_ID = 'cantonese-female';

export class TtsService {
  constructor(options = {}) {
    // Configuration
    this.ttsProxyEndpoint = options.ttsProxyEndpoint || '/api/tts-proxy';
    this.ttsEndpoint = options.ttsEndpoint || '/api/tts';
    this.minimaxDirectEndpoint = options.minimaxDirectEndpoint || 'https://api.minimax.chat/v1/t2a_v2';
    
    // State
    this.audioCtx = null;
    this.currentSource = null;
    this.currentRaf = 0;
    this.speakSeq = 0;
    this.isSpeaking = false;
    this.useAudioMouth = false;
    this.audioMouth = 0;
    
    // Backend proxy availability cache
    this._backendProxyAvailable = null;
    
    // Initialize settings from localStorage or defaults
    this._initSettings();
    
    // Browser voice handling
    this._browserVoicesLoaded = false;
    this._browserVoices = [];
    this._loadBrowserVoices();
  }
  
  _initSettings() {
    // MiniMax settings
    this.minimaxKey = this._getLocalStorage('minimax_tts_key') || '';
    this.minimaxGroupId = this._getLocalStorage('minimax_group_id') || '';
    
    // TTS mode: 'browser' (default, free) or 'neural' (MiniMax)
    this.ttsMode = this._getLocalStorage('xiaob_tts_mode') || 'browser';
    
    // Voice settings
    this.neuralVoice = this._getLocalStorage('xiaob_voice_id') || DEFAULT_VOICE_ID;
    this.browserVoiceUri = this._getLocalStorage('xiaob_browser_voice_uri') || '';
    this.ttsRate = parseFloat(this._getLocalStorage('xiaob_tts_rate')) || 1.0;
    this.ttsMuted = this._getLocalStorage('xiaob_tts_muted') === 'true';
    
    // TTS muted state
    this.ttsMuted = false;
  }
  
  _getLocalStorage(key) {
    try { return localStorage.getItem(key) || ''; } catch (e) { return ''; }
  }
  
  _setLocalStorage(key, value) {
    try { localStorage.setItem(key, value); } catch (e) {}
  }
  
  _loadBrowserVoices() {
    if ('speechSynthesis' in window) {
      const loadVoices = () => {
        this._browserVoices = window.speechSynthesis.getVoices();
        this._browserVoicesLoaded = true;
      };
      loadVoices();
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }
  }
  
  /**
   * Get current TTS mode
   */
  getMode() {
    return this.ttsMode;
  }
  
  /**
   * Set TTS mode
   */
  setMode(mode) {
    this.ttsMode = mode;
    this._setLocalStorage('xiaob_tts_mode', mode);
  }
  
  /**
   * Get current neural voice ID
   */
  getNeuralVoice() {
    return this.neuralVoice;
  }
  
  /**
   * Set neural voice ID
   */
  setNeuralVoice(voiceId) {
    this.neuralVoice = voiceId;
    this._setLocalStorage('xiaob_voice_id', voiceId);
  }
  
  /**
   * Get current browser voice URI
   */
  getBrowserVoiceUri() {
    return this.browserVoiceUri;
  }
  
  /**
   * Set browser voice URI
   */
  setBrowserVoiceUri(uri) {
    console.log('[TtsService:DIAG] setBrowserVoiceUri called:', JSON.stringify(uri));
    this.browserVoiceUri = uri;
    this._setLocalStorage('xiaob_browser_voice_uri', uri);
  }
  
  /**
   * Check if MiniMax API key is configured
   */
  hasMinimaxKey() {
    return !!(this.minimaxKey && this.minimaxGroupId);
  }
  
  /**
   * Set MiniMax credentials
   */
  setMinimaxCredentials(key, groupId) {
    this.minimaxKey = key;
    this.minimaxGroupId = groupId;
    this._setLocalStorage('minimax_tts_key', key);
    this._setLocalStorage('minimax_group_id', groupId);
  }
  
  /**
   * Clear MiniMax credentials
   */
  clearMinimaxCredentials() {
    this.minimaxKey = '';
    this.minimaxGroupId = '';
    try { localStorage.removeItem('minimax_tts_key'); } catch (e) {}
    try { localStorage.removeItem('minimax_group_id'); } catch (e) {}
  }
  
  /**
   * Get voice catalog
   */
  getVoiceCatalog() {
    return VOICE_CATALOG;
  }
  
  /**
   * Get browser voices
   */
  getBrowserVoices() {
    if (!this._browserVoicesLoaded) {
      this._loadBrowserVoices();
    }
    return this._browserVoices;
  }
  
  /**
   * Check if currently speaking
   */
  getIsSpeaking() {
    return this.isSpeaking;
  }
  
  /**
   * Get audio mouth value for animation
   */
  getAudioMouth() {
    return this.audioMouth;
  }
  
  /**
   * Secure TTS via backend proxy
   */
  async fetchTtsProxy(text) {
    const voiceId = this.neuralVoice || DEFAULT_VOICE_ID;
    const voiceKey = this._resolveVoiceKey(voiceId);
    
    try {
      const r = await fetch(this.ttsProxyEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: String(text || '').slice(0, 150),
          voice: voiceKey,
          speed: 1.0
        })
      });
      
      if (r.headers.get('Content-Type')?.includes('audio')) {
        const bytes = await r.arrayBuffer();
        this._backendProxyAvailable = true;
        return new Response(bytes, { status: 200, headers: { 'Content-Type': 'audio/mpeg' } });
      }
      
      // Non-audio response (error JSON)
      const j = await r.json().catch(() => ({}));
      throw new Error(j.error || j.detail || `Proxy error ${r.status}`);
    } catch (e) {
      this._backendProxyAvailable = false;
      throw e;
    }
  }
  
  /**
   * Direct MiniMax TTS API call
   */
  async fetchMinimaxTtsDirect(text) {
    if (!this.minimaxKey) throw new Error('MiniMax API key missing');
    if (!this.minimaxGroupId) throw new Error('MiniMax Group ID missing');
    
    const voiceId = this.neuralVoice || DEFAULT_VOICE_ID;
    const voiceKey = this._resolveVoiceId(voiceId);
    
    const body = {
      model: 'speech-02-hd',
      text: String(text || '').slice(0, 150),
      stream: false,
      voice_setting: {
        voice_id: voiceKey,
        speed: 1.0
      },
      audio_setting: {
        sample_rate: 32000,
        format: 'mp3',
        bitrate: 128000,
        channel: 1
      }
    };
    
    const r = await fetch(this.minimaxDirectEndpoint + '?group_id=' + encodeURIComponent(this.minimaxGroupId), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + this.minimaxKey
      },
      body: JSON.stringify(body)
    });
    
    if (!r.ok) {
      const errText = await r.text().catch(() => '');
      throw new Error('http ' + r.status + ' ' + (errText.slice(0, 200) || ''));
    }
    
    const j = await r.json();
    
    if (j && j.base_resp && j.base_resp.status_code !== undefined && j.base_resp.status_code !== 0) {
      const msg = j.base_resp.status_msg || ('MiniMax error ' + j.base_resp.status_code);
      throw new Error('MiniMax voice error: ' + msg + ' (voice_id=' + voiceId + ')');
    }
    
    if (j && j.data && j.data.audio) {
      const hex = j.data.audio;
      const bytes = new Uint8Array(hex.length / 2);
      for (let i = 0; i < bytes.length; i++) {
        bytes[i] = parseInt(hex.substr(i * 2, 2), 16);
      }
      return new Response(bytes, { status: 200, headers: { 'Content-Type': 'audio/mpeg' } });
    }
    
    throw new Error('MiniMax T2A response missing data.audio');
  }
  
  _resolveVoiceKey(voiceId) {
    // Find friendly alias from catalog
    const entry = VOICE_CATALOG.find(v => v.voice_id === voiceId || v.id === voiceId);
    return entry ? entry.id : voiceId;
  }
  
  _resolveVoiceId(voiceId) {
    // Find MiniMax voice_id from catalog
    const entry = VOICE_CATALOG.find(v => v.id === voiceId || v.voice_id === voiceId);
    return entry ? entry.voice_id : voiceId;
  }
  
  /**
   * Initialize audio context
   */
  _ensureAudioContext() {
    if (!this.audioCtx) {
      this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
    return this.audioCtx;
  }
  
  /**
   * Speak using neural (MiniMax) TTS
   */
  async speakNeural(text, seq) {
    this._ensureAudioContext();
    
    let resp;
    let lastError = null;
    
    // Priority 1: Backend proxy (uses server-side API key)
    if (this._backendProxyAvailable !== false) {
      try {
        resp = await this.fetchTtsProxy(text);
      } catch (e) {
        lastError = e;
      }
    }
    
    // Priority 2: Direct MiniMax API (if user has their own key)
    if (!resp && this.minimaxKey) {
      try {
        resp = await this.fetchMinimaxTtsDirect(text);
      } catch (e) {
        lastError = e;
      }
    }
    
    // Priority 3: Legacy /api/tts endpoint
    if (!resp && !this.minimaxKey) {
      try {
        const sep = this.ttsEndpoint.indexOf('?') < 0 ? '?' : '&';
        resp = await fetch(this.ttsEndpoint + sep + 'voice=' + encodeURIComponent(this._resolveVoiceId(this.neuralVoice)) + '&text=' + encodeURIComponent(text));
      } catch (e) {
        lastError = e;
      }
    }
    
    if (!resp) {
      throw lastError || new Error('All TTS methods unavailable');
    }
    
    if (seq !== this.speakSeq) return;
    if (!resp.ok) throw new Error('http ' + resp.status);
    
    const arr = await resp.arrayBuffer();
    if (seq !== this.speakSeq) return;
    if (arr.byteLength < 800) throw new Error('audio too small');
    
    const audioBuf = await this.audioCtx.decodeAudioData(arr);
    if (seq !== this.speakSeq) return;
    
    const src = this.audioCtx.createBufferSource();
    src.buffer = audioBuf;
    const analyser = this.audioCtx.createAnalyser();
    analyser.fftSize = 256;
    src.connect(analyser);
    analyser.connect(this.audioCtx.destination);
    
    const data = new Uint8Array(analyser.fftSize);
    this.currentSource = src;
    this.useAudioMouth = true;
    this.isSpeaking = true;
    
    const loop = () => {
      if (this.currentSource !== src) return;
      analyser.getByteTimeDomainData(data);
      let sum = 0;
      for (let i = 0; i < data.length; i++) {
        const v = (data[i] - 128) / 128;
        sum += v * v;
      }
      this.audioMouth = Math.min(1, Math.sqrt(sum / data.length) * 3.4);
      this.currentRaf = requestAnimationFrame(loop);
    };
    
    this.currentRaf = requestAnimationFrame(loop);
    
    src.onended = () => {
      if (this.currentSource !== src) return;
      if (this.currentRaf) { cancelAnimationFrame(this.currentRaf); this.currentRaf = 0; }
      this.isSpeaking = false;
      this.useAudioMouth = false;
      this.audioMouth = 0;
      this.currentSource = null;
    };
    
    src.start(0);
    return true;
  }
  
  /**
   * Speak using browser Web Speech API
   */
  speakBrowser(text, seq) {
    if (!('speechSynthesis' in window)) {
      throw new Error('Browser does not support Web Speech API');
    }
    
    // === DIAGNOSTIC: Log current speech synthesis state ===
    console.log('[TtsService:DIAG] speakBrowser called', {
      textLen: text.length,
      seq,
      speaking: window.speechSynthesis.speaking,
      paused: window.speechSynthesis.paused,
      pending: window.speechSynthesis.pending
    });
    
    // Cancel any ongoing speech
    // NOTE: Only cancel if currently speaking or pending to avoid the Chromium bug
    // where cancel() + immediate speak() silently drops the utterance.
    // This is a known issue in Chrome/Edge (crbug.com/1066031, crbug.com/1212930).
    if (window.speechSynthesis.speaking || window.speechSynthesis.pending) {
      console.log('[TtsService:DIAG] Cancelling ongoing speech before speak');
      window.speechSynthesis.cancel();
    } else {
      console.log('[TtsService:DIAG] No ongoing speech, skipping cancel()');
    }
    
    const utt = new SpeechSynthesisUtterance(text);
    utt.rate = this.ttsRate || 1.0;
    
    // Intelligent voice selection:
    // 1. If browserVoiceUri is configured, try to find the matching voice
    // 2. Otherwise, auto-select a Chinese voice as fallback
    const voices = this.getBrowserVoices();
    console.log('[TtsService:DIAG] browserVoiceUri value:', JSON.stringify(this.browserVoiceUri), 'type:', typeof this.browserVoiceUri, 'length:', this.browserVoiceUri ? this.browserVoiceUri.length : 0);
    console.log('[TtsService:DIAG] getBrowserVoices count:', voices.length, 'first 3:', voices.slice(0,3).map(v => v.name).join(', '));
    let selectedVoice = null;
    
    if (this.browserVoiceUri) {
      // On Windows Chromium, Microsoft Chinese voices share identical voiceURI,
      // so matching by name is more reliable. Try name first, then voiceURI/url.
      selectedVoice = voices.find(v => v.name === this.browserVoiceUri)
        || voices.find(v => v.voiceURI === this.browserVoiceUri)
        || voices.find(v => v.url === this.browserVoiceUri);
      
      // Fuzzy fallback: if no exact match, try extracting short English name
      // from the stored URI and find a voice whose name contains it.
      // This handles cases where hardcoded URIs (e.g. "Microsoft Zhiwei Online (Natural) - Chinese (Traditional, Taiwan)")
      // don't match actual browser voice names (e.g. "Microsoft 志偉 Online (Natural) - Chinese (Taiwanese Mandarin, Traditional)").
      if (!selectedVoice) {
        const shortName = this.browserVoiceUri
          .replace(/^Microsoft\s+/i, '')
          .replace(/\s+Online\s+\(Natural\).*$/, '')
          .replace(/\s+-\s+Chinese.*$/, '')
          .trim();
        if (shortName && shortName !== this.browserVoiceUri) {
          selectedVoice = voices.find(v => v.name.includes(shortName));
          if (selectedVoice) {
            console.log('[TtsService] Fuzzy-matched configured voice:', selectedVoice.name, '(' + selectedVoice.lang + ')');
          }
        }
      }
      
      if (selectedVoice) {
        console.log('[TtsService] Using configured voice:', selectedVoice.name, '(' + selectedVoice.lang + ')');
      }
    }
    
    // Auto-select Chinese voice if none matched via browserVoiceUri
    if (!selectedVoice) {
      selectedVoice = this._pickChineseVoice(voices);
      if (selectedVoice) {
        console.log('[TtsService] Auto-selected Chinese voice:', selectedVoice.name, '(' + selectedVoice.lang + ')');
      }
    }
    
    if (selectedVoice) {
      utt.voice = selectedVoice;
      utt.lang = selectedVoice.lang;
      console.log('[TtsService:DIAG] Assigned voice:', selectedVoice.name, selectedVoice.voiceURI);
    } else {
      utt.lang = 'zh-TW';
      console.log('[TtsService:DIAG] No voice assigned, using default lang zh-TW');
    }
    
    // === DIAGNOSTIC: Log utterance state before speak ===
    console.log('[TtsService:DIAG] Utterance ready:', {
      text: utt.text.substring(0, 50),
      lang: utt.lang,
      voice: utt.voice ? utt.voice.name : 'default',
      rate: utt.rate
    });
    
    this.isSpeaking = true;
    
    utt.onstart = () => {
      console.log('[TtsService:DIAG] Speech started');
      if (seq !== this.speakSeq) return;
    };
    
    utt.onend = () => {
      console.log('[TtsService:DIAG] Speech ended');
      if (seq !== this.speakSeq) return;
      this.isSpeaking = false;
    };
    
    utt.onerror = (e) => {
      if (seq !== this.speakSeq) return;
      this.isSpeaking = false;
      console.error('[TtsService:DIAG] Speech synthesis error:', e.error, e.message);
    };
    
    try {
      window.speechSynthesis.speak(utt);
      console.log('[TtsService:DIAG] speak() called successfully');
    } catch (e) {
      console.error('[TtsService:DIAG] speak() threw exception:', e);
      this.isSpeaking = false;
      throw e;
    }
    
    return true;
  }
  
  /**
   * Auto-select a Chinese voice from available browser voices
   * Priority: Traditional Chinese (Taiwan) female > Traditional Chinese > Mandarin > any Chinese
   */
  _pickChineseVoice(voices) {
    if (!voices || !voices.length) return null;
    const pick = (re) => voices.find(v => re.test(v.name + ' ' + v.lang) && !/Google/i.test(v.name));
    return pick(/(HsiaoChen|HsiaoYu|曉臻|曉雨).*zh/i)
      || pick(/(Yating|Zhiwei).*zh[-_]TW/i)
      || pick(/Microsoft.*zh[-_]TW/i)
      || pick(/zh[-_]TW/i)
      || pick(/^zh/i)
      || voices.find(v => /zh/i.test(v.lang))
      || null;
  }
  
  /**
   * Main speak function - dispatches to appropriate TTS backend
   */
  async speak(text) {
    if (this.ttsMuted) return;
    
    this.speakSeq++;
    const seq = this.speakSeq;
    
    // Stop any current speech
    // NOTE: For browser mode, speakBrowser() calls cancel() internally.
    // We skip stop() here to avoid the Chromium speechSynthesis bug where
    // multiple cancel() calls before speak() silently swallow utterances.
    if (this.ttsMode !== 'browser') {
      this.stop();
    }
    
    try {
      if (this.ttsMode === 'neural') {
        await this.speakNeural(text, seq);
      } else {
        this.speakBrowser(text, seq);
      }
    } catch (e) {
      console.error('TTS error:', e);
      // Auto-fallback to browser TTS if neural fails
      if (this.ttsMode === 'neural') {
        try {
          this.speakBrowser(text, seq);
        } catch (e2) {
          console.error('Browser TTS fallback also failed:', e2);
        }
      }
      throw e;
    }
  }
  
  /**
   * Stop current speech
   */
  stop() {
    // Stop audio source
    if (this.currentSource) {
      try { this.currentSource.stop(); } catch (e) {}
      this.currentSource = null;
    }
    if (this.currentRaf) {
      cancelAnimationFrame(this.currentRaf);
      this.currentRaf = 0;
    }
    this.isSpeaking = false;
    this.useAudioMouth = false;
    this.audioMouth = 0;
    
    // Stop browser speech
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  }
  
  /**
   * Test MiniMax connection with user-provided credentials
   */
  async testMinimaxConnection(key, groupId) {
    const oldKey = this.minimaxKey;
    const oldGroup = this.minimaxGroupId;
    
    this.minimaxKey = key;
    this.minimaxGroupId = groupId;
    
    try {
      const resp = await this.fetchMinimaxTtsDirect('測試');
      await resp.arrayBuffer();
      return { success: true };
    } catch (e) {
      return { success: false, error: e.message };
    } finally {
      this.minimaxKey = oldKey;
      this.minimaxGroupId = oldGroup;
    }
  }
  
  /**
   * Test backend proxy availability
   */
  async testBackendProxy() {
    try {
      await this.fetchTtsProxy('測試');
      return { success: true };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }
}

export default TtsService;
