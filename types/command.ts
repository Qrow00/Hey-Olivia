export type CommandCategory = "system" | "device" | "media" | "smart-home";

export interface Command {
  id: string;
  name: string;
  alias: string[];
  category: CommandCategory;
  handler: string;
  requiresAuth: boolean;
  enabled: boolean;
}

export interface CommandRegistry {
  commands: Command[];
}
