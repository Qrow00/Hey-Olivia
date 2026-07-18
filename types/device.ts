export type DeviceType = "phone" | "pc" | "laptop" | "cctv" | "smart-home";
export type Platform = "android" | "ios" | "windows" | "linux";
export type DeviceStatus = "online" | "offline" | "sleeping";
export type SignalStrength = "strong" | "medium" | "weak";

export type DeviceCapability =
  | "screen-share"
  | "voice"
  | "camera"
  | "adb"
  | "ssh"
  | "rdp"
  | "rtsp";

export interface Device {
  id: string;
  name: string;
  type: DeviceType;
  platform: Platform;
  status: DeviceStatus;
  ip: string;
  tailscaleIp: string;
  capabilities: DeviceCapability[];
  lastSeen: Date;
  lastHeartbeat: Date | null;
  battery: number;
  signal: SignalStrength;
  osVersion: string;
  appVersion: string;
  metadata: Record<string, unknown>;
}

export interface DeviceRegistry {
  userId: string;
  devices: Device[];
}

export interface DeviceStatusSummary {
  total: number;
  online: number;
  offline: number;
  sleeping: number;
}
