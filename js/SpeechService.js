/**
 * SpeechService.js - Speech Recognition Service Module
 * 
 * Handles all speech-to-text (STT) functionality including:
 * - Browser Web Speech API recognition
 * - Continuous listening mode
 * - Interim results handling
 * 
 * Usage:
 *   import { SpeechService } from './js/SpeechService.js';
 *   const speech = new SpeechService(options);
 *   speech.start((transcript) => { ... });
 */

export class SpeechService {
  constructor(options = {}) {
    this.recognition = null;
    this.isListening = false;
    this.finalTranscript = '';
    this.interimTranscript = '';
    
    // Callbacks
    this.onInterim = options.onInterim || (() => {});
    this.onFinal = options.onFinal || (() => {});
    this.onStart = options.onStart || (() => {});
    this.onEnd = options.onEnd || (() => {});
    this.onError = options.onError || ((e) => console.error('Speech recognition error:', e));
    
    // Initialize
    this._initRecognition();
  }
  
  _initRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      console.warn('SpeechRecognition not supported in this browser');
      return;
    }
    
    this.recognition = new SpeechRecognition();
    this.recognition.continuous = true;
    this.recognition.interimResults = true;
    this.recognition.lang = 'zh-HK,zh-TW,zh-CN,en-US';
    
    this.recognition.onstart = () => {
      this.isListening = true;
      this.finalTranscript = '';
      this.interimTranscript = '';
      this.onStart();
    };
    
    this.recognition.onend = () => {
      this.isListening = false;
      this.onEnd();
    };
    
    this.recognition.onerror = (event) => {
      this.isListening = false;
      if (event.error !== 'no-speech' && event.error !== 'aborted') {
        this.onError(event.error);
      }
    };
    
    this.recognition.onresult = (event) => {
      let interim = '';
      let final = '';
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += transcript;
        } else {
          interim += transcript;
        }
      }
      
      if (final) {
        this.finalTranscript += final;
        this.onFinal(this.finalTranscript);
      }
      
      if (interim) {
        this.interimTranscript = interim;
        this.onInterim(interim);
      }
    };
  }
  
  /**
   * Check if speech recognition is supported
   */
  isSupported() {
    return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  }
  
  /**
   * Check if currently listening
   */
  getIsListening() {
    return this.isListening;
  }
  
  /**
   * Start speech recognition
   */
  start() {
    if (!this.recognition) {
      this.onError('Speech recognition not supported');
      return false;
    }
    
    if (this.isListening) {
      return false;
    }
    
    try {
      this.finalTranscript = '';
      this.interimTranscript = '';
      this.recognition.start();
      return true;
    } catch (e) {
      this.onError(e.message);
      return false;
    }
  }
  
  /**
   * Stop speech recognition
   */
  stop() {
    if (!this.recognition || !this.isListening) {
      return;
    }
    
    try {
      this.recognition.stop();
    } catch (e) {
      // Ignore errors when stopping
    }
  }
  
  /**
   * Abort speech recognition
   */
  abort() {
    if (!this.recognition) {
      return;
    }
    
    try {
      this.recognition.abort();
    } catch (e) {
      // Ignore errors when aborting
    }
    
    this.isListening = false;
  }
  
  /**
   * Set recognition language
   */
  setLanguage(lang) {
    if (this.recognition) {
      this.recognition.lang = lang;
    }
  }
  
  /**
   * Get final transcript
   */
  getFinalTranscript() {
    return this.finalTranscript;
  }
  
  /**
   * Get interim transcript
   */
  getInterimTranscript() {
    return this.interimTranscript;
  }
  
  /**
   * Clear transcripts
   */
  clear() {
    this.finalTranscript = '';
    this.interimTranscript = '';
  }
}

export default SpeechService;
