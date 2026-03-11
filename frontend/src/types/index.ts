// ═══════════════════════════════════════════════════════════
//  E.V.O.N. Frontend — Type Definitions
// ═══════════════════════════════════════════════════════════

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  input_mode: "text" | "voice";
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface ConversationListItem {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ChatRequest {
  conversation_id?: string | null;
  message: string;
  input_mode: "text" | "voice";
}

export interface ChatResponse {
  conversation_id: string;
  message: Message;
  response: Message;
}

export interface StreamEvent {
  type: "meta" | "token" | "done" | "error" | "transcription" | "audio";
  content?: string;
  conversation_id?: string;
  message_id?: string;
  format?: string;
}

export interface TranscriptionResponse {
  text: string;
  language: string;
}

export interface SystemInfo {
  os: string;
  architecture: string;
  processor: string;
  python_version: string;
  cpu_count: number;
  cpu_percent: number;
  ram_total_gb: number;
  ram_used_gb: number;
  ram_percent: number;
  disk_total_gb: number;
  disk_used_gb: number;
  disk_percent: number;
  gpu?: {
    name: string;
    vram_total_mb: number;
    vram_used_mb: number;
    temperature_c: number;
  };
}

export interface VoicePipelineResult {
  conversation_id: string;
  transcription: string;
  response: string;
  user_message: Message;
  assistant_message: Message;
  has_audio: boolean;
}

export type InputMode = "text" | "voice";
