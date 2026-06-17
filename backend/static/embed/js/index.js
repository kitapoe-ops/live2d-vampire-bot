/**
 * index.js - Service Modules Entry Point
 * 
 * Export all service modules for easy importing.
 */

export { TtsService, VOICE_CATALOG, DEFAULT_VOICE_ID } from './TtsService.js';
export { SpeechService } from './SpeechService.js';

export default {
  TtsService,
  SpeechService,
};
