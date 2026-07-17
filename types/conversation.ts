export type MessageRole = "user" | "jarvis";
export type MessageType = "text" | "voice" | "screen";

export interface MessageMetadata {
  sttConfidence?: number;
  llmModel?: string;
  responseTime?: number;
  tokens?: number;
}

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  type: MessageType;
  timestamp: Date;
  metadata?: MessageMetadata;
}

export interface Conversation {
  id: string;
  userId: string;
  startedAt: Date;
  messages: Message[];
}
