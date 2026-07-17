export type STTEngine = "whisper" | "vosk";
export type TTSEngine = "piper" | "edge-tts";
export type LLMModel = "llama3.2" | "llava:7b";
export type VoiceSessionStatus = "idle" | "listening" | "processing" | "speaking";

export interface STTConfig {
  engine: STTEngine;
  language: string;
  confidence: number;
  transcript: string;
}

export interface TTSConfig {
  engine: TTSEngine;
  voice: string;
  speed: number;
  pitch: number;
  isSpeaking: boolean;
  currentWord: string;
  wordIndex: number;
}

export interface TokenUsage {
  prompt: number;
  completion: number;
  total: number;
}

export interface LLMConfig {
  model: LLMModel;
  temperature: number;
  maxTokens: number;
  systemPrompt: string;
  response: string;
  tokens: TokenUsage;
}

export interface VoiceSession {
  id: string;
  userId: string;
  status: VoiceSessionStatus;
  startedAt: Date;
  stt: STTConfig;
  tts: TTSConfig;
  llm: LLMConfig;
}
