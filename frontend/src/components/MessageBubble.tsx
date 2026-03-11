// ═══════════════════════════════════════════════════════════
//  MessageBubble — renders a single chat message
// ═══════════════════════════════════════════════════════════

"use client";

import { Bot, User, Mic, Volume2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import type { Message } from "@/types";

interface MessageBubbleProps {
  message: Message;
  onSpeak?: (text: string) => void;
}

export default function MessageBubble({ message, onSpeak }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const isVoice = message.input_mode === "voice";

  return (
    <div
      className={`flex gap-3 animate-slide-up ${
        isUser ? "justify-end" : "justify-start"
      }`}
    >
      {/* Avatar — assistant */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-evon-accent to-evon-accent-dim flex items-center justify-center mt-1">
          <Bot className="w-4 h-4 text-white" />
        </div>
      )}

      {/* Bubble */}
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-evon-accent/20 border border-evon-accent/30 text-evon-text"
            : "bg-evon-card border border-evon-border text-evon-text"
        }`}
      >
        {/* Voice indicator */}
        {isVoice && (
          <div className="flex items-center gap-1.5 mb-1.5 text-xs text-evon-accent">
            <Mic className="w-3 h-3" />
            <span>Voice input</span>
          </div>
        )}

        {/* Content */}
        <div className="prose prose-invert prose-sm max-w-none prose-p:my-1 prose-headings:my-2 prose-pre:my-2 prose-ul:my-1 prose-ol:my-1 prose-code:text-evon-accent-glow prose-pre:bg-evon-bg prose-pre:border prose-pre:border-evon-border prose-pre:rounded-xl">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between mt-2">
          <span className="text-[10px] text-evon-muted">
            {new Date(message.created_at).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
          {!isUser && onSpeak && (
            <button
              onClick={() => onSpeak(message.content)}
              className="p-1 rounded-md hover:bg-evon-accent/10 text-evon-muted
                         hover:text-evon-accent transition-colors"
              title="Read aloud"
            >
              <Volume2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Avatar — user */}
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-evon-card border border-evon-border flex items-center justify-center mt-1">
          <User className="w-4 h-4 text-evon-muted" />
        </div>
      )}
    </div>
  );
}
