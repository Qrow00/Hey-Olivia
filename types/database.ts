export interface DBUser {
  id: string;
  name: string;
  avatar: string;
  created_at: string;
  settings: string; // JSON string
}

export interface DBDevice {
  id: string;
  user_id: string;
  name: string;
  type: string;
  platform: string;
  ip: string;
  tailscale_ip: string;
  capabilities: string; // JSON string
  status: string;
  last_seen: string;
  battery?: number;
  signal?: string;
}

export interface DBConversation {
  id: string;
  user_id: string;
  started_at: string;
  ended_at: string | null;
}

export interface DBMessage {
  id: string;
  conversation_id: string;
  role: string;
  content: string;
  type: string;
  timestamp: string;
  metadata: string; // JSON string
}

export interface DBCommand {
  id: string;
  name: string;
  alias: string; // JSON string
  category: string;
  handler: string;
  enabled: boolean;
}
