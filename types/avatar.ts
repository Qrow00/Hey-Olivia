export type AvatarStateName = "idle" | "listening" | "thinking" | "speaking" | "error";

export interface BreathingConfig {
  speed: number;
  amplitude: number;
}

export interface BreathingParams {
  outerRing: BreathingConfig;
  middleRing: BreathingConfig;
  innerRing: BreathingConfig;
  core: BreathingConfig;
  reactor: BreathingConfig;
  glow: BreathingConfig;
}

export interface TransitionConfig {
  duration: number;
  easing?: string;
}

export interface RippleConfig {
  duration: number;
  count: number;
}

export interface RingPopConfig {
  duration: number;
  sizes: number[];
}

export interface Transitions {
  popIn: TransitionConfig;
  ripple: RippleConfig;
  ringPop: RingPopConfig;
}

export interface AvatarAnimations {
  breathing: BreathingParams;
  transitions: Transitions;
}

export interface WordPulse {
  active: boolean;
  currentWord: string;
  pulseIntensity: number;
}

export interface AvatarState {
  currentState: AvatarStateName;
  color: string;
  animations: AvatarAnimations;
  wordPulse: WordPulse;
}

export const AVATAR_COLORS: Record<AvatarStateName, string> = {
  idle: "#00d4ff",
  listening: "#00ff88",
  thinking: "#ffaa00",
  speaking: "#00ffff",
  error: "#ff4444",
};
