import { UserProfile } from "./user";
import { Device, DeviceRegistry } from "./device";
import { Conversation } from "./conversation";
import { AvatarState } from "./avatar";
import { VoiceSession } from "./voice";
import { ScreenShareSession } from "./screen";

export type ScreenName = "home" | "devices" | "settings" | "chat";
export type ConnectionStatus = "connected" | "disconnected" | "connecting";

export interface UIState {
  sidebarOpen: boolean;
  settingsOpen: boolean;
  currentScreen: ScreenName;
}

export interface ConnectionState {
  status: ConnectionStatus;
  wsUrl: string;
  reconnectAttempts: number;
  lastPing: Date | null;
}

export interface AppState {
  user: UserProfile;
  devices: DeviceRegistry;
  activeDevice: Device | null;
  conversations: Conversation[];
  currentConversation: Conversation | null;
  avatar: AvatarState;
  voice: VoiceSession;
  screen: ScreenShareSession;
  ui: UIState;
  connection: ConnectionState;
}
