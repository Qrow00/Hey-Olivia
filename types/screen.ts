export type ScreenSource = "phone" | "pc";
export type ScreenStatus = "inactive" | "starting" | "active" | "paused";

export interface CaptureConfig {
  fps: number;
  quality: number;
  resolution: { width: number; height: number };
  format: "jpeg" | "png";
}

export interface ScreenAnalysis {
  enabled: boolean;
  interval: number;
  lastAnalysis: Date | null;
  description: string;
  objects: string[];
  text: string;
}

export interface ScreenShareSession {
  id: string;
  deviceId: string;
  source: ScreenSource;
  status: ScreenStatus;
  startedAt: Date;
  capture: CaptureConfig;
  analysis: ScreenAnalysis;
}
