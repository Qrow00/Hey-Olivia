export type WSEventType =
  | "user-message"
  | "jarvis-response"
  | "voice-data"
  | "screen-data"
  | "avatar-state";

export interface WSConfig {
  url: string;
  events: Record<WSEventType, string>;
}

export interface RESTEndpoints {
  GET_DEVICES: string;
  GET_CONVERSATIONS: string;
  GET_SETTINGS: string;
  UPDATE_SETTINGS: string;
  SEND_COMMAND: string;
}

export interface APIConfig {
  ws: WSConfig;
  rest: RESTEndpoints;
}

export const API: APIConfig = {
  ws: {
    url: "ws://100.x.x.x:8000/ws",
    events: {
      "user-message": "user-message",
      "jarvis-response": "jarvis-response",
      "voice-data": "voice-data",
      "screen-data": "screen-data",
      "avatar-state": "avatar-state",
    },
  },
  rest: {
    GET_DEVICES: "/api/devices",
    GET_CONVERSATIONS: "/api/conversations",
    GET_SETTINGS: "/api/settings",
    UPDATE_SETTINGS: "/api/settings",
    SEND_COMMAND: "/api/command",
  },
};
