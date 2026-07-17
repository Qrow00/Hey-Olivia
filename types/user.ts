export type Theme = "dark" | "light";
export type Language = "en" | "fil";

export interface UserSettings {
  theme: Theme;
  language: Language;
  voiceEnabled: boolean;
  wakeWord: string;
  autoConnect: boolean;
}

export interface UserProfile {
  id: string;
  name: string;
  avatar: string;
  createdAt: Date;
  settings: UserSettings;
}
