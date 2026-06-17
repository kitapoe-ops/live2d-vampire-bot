/**
 * index.js - Service Modules Entry Point
 * 
 * Export all service modules for easy importing.
 * 
 * Usage:
 *   import { TtsService, SpeechService } from './js/index.js';
 * 
 * Or import individual services:
 *   import { TtsService } from './js/TtsService.js';
 *   import { SpeechService } from './js/SpeechService.js';
 */

export { TtsService, VOICE_CATALOG, DEFAULT_VOICE_ID } from './TtsService.js';
export { SpeechService } from './SpeechService.js';

// Re-export for convenience
import { TtsService } from './TtsService.js';
import { SpeechService } from './SpeechService.js';

export default {
  TtsService,
  SpeechService,
  VOICE_CATALOG: (await import('./TtsService.js')).VOICE_CATALOG,
  DEFAULT_VOICE_ID: (await import('./TtsService.js')).DEFAULT_VOICE_ID,
};
