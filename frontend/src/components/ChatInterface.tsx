// ═══════════════════════════════════════════════════════════
//  ChatInterface — main chat area with input
// ═══════════════════════════════════════════════════════════

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Send, Bot, Sparkles, Keyboard, Mic } from "lucide-react";
import MessageBubble from "./MessageBubble";
import VoiceButton from "./VoiceButton";
import Waveform from "./Waveform";
import { useVoice } from "@/hooks/useVoice";
import type { InputMode, Message, VoicePipelineResult } from "@/types";

interface ChatInterfaceProps {
  messages: Message[];
  streamingContent: string;
  isLoading: boolean;
  activeConversationId: string | null;
  onSendMessage: (text: string, mode: InputMode) => void;
  onAddVoiceMessages: (
    userMsg: Message,
    assistantMsg: Message,
    convId: string
  ) => void;
}

export default function ChatInterface({
  messages,
  streamingContent,
  isLoading,
  activeConversationId,
  onSendMessage,
  onAddVoiceMessages,
}: ChatInterfaceProps) {
  const [input, setInput] = useState("");
  const [inputMode, setInputMode] = useState<InputMode>("text");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // ── Voice hook ─────────────────────────────────────────
  const {
    isRecording,
    isProcessing,
    isSpeaking,
    toggleRecording,
    playTTS,
    getAnalyser,
  } = useVoice({
    conversationId: activeConversationId,
    onResult: (result: VoicePipelineResult) => {
      onAddVoiceMessages(
        result.user_message,
        result.assistant_message,
        result.conversation_id
      );
    },
    onError: (err) => console.error("Voice error:", err),
  });

  // ── Auto-scroll ───────────────────────────────────────
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  // ── Focus input ───────────────────────────────────────
  useEffect(() => {
    if (inputMode === "text") {
      inputRef.current?.focus();
    }
  }, [inputMode]);

  // ── Send handler ──────────────────────────────────────
  const handleSend = useCallback(() => {
    const text = input.trim();
    if (!text || isLoading) return;
    setInput("");
    onSendMessage(text, "text");
  }, [input, isLoading, onSendMessage]);

  // ── Keyboard handler ──────────────────────────────────
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // ── Auto-resize textarea ──────────────────────────────
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const ta = e.target;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
  };

  const isEmpty = messages.length === 0 && !streamingContent;

  return (
    <div className="flex-1 flex flex-col h-full bg-jarvis-bg">
      {/* ── Messages Area ─────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4 scrollbar-thin">
        {isEmpty ? (
          <EmptyState />
        ) : (
          <>
            {messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                message={msg}
                onSpeak={playTTS}
              />
            ))}

            {/* Streaming response */}
            {streamingContent && (
              <div className="flex gap-3 animate-fade-in">
                <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-jarvis-accent to-jarvis-accent-dim flex items-center justify-center mt-1">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="max-w-[75%] rounded-2xl px-4 py-3 bg-jarvis-card border border-jarvis-border text-jarvis-text">
                  <p className="whitespace-pre-wrap">{streamingContent}</p>
                  <span className="inline-block w-2 h-4 bg-jarvis-accent animate-pulse ml-0.5" />
                </div>
              </div>
            )}

            {/* Loading indicator */}
            {isLoading && !streamingContent && (
              <div className="flex gap-3 animate-fade-in">
                <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-jarvis-accent to-jarvis-accent-dim flex items-center justify-center mt-1">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="rounded-2xl px-4 py-3 bg-jarvis-card border border-jarvis-border">
                  <div className="flex gap-1.5">
                    <span className="w-2 h-2 bg-jarvis-accent rounded-full animate-bounce [animation-delay:0ms]" />
                    <span className="w-2 h-2 bg-jarvis-accent rounded-full animate-bounce [animation-delay:150ms]" />
                    <span className="w-2 h-2 bg-jarvis-accent rounded-full animate-bounce [animation-delay:300ms]" />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* ── Waveform (visible in voice mode or when speaking) ── */}
      {(inputMode === "voice" || isRecording || isSpeaking) && (
        <div className="px-6 py-2">
          <Waveform
            isActive={isRecording || isSpeaking}
            analyser={getAnalyser()}
          />
        </div>
      )}

      {/* ── Input Area ────────────────────────────────── */}
      <div className="border-t border-jarvis-border p-4">
        <div className="max-w-4xl mx-auto">
          {/* Mode Toggle */}
          <div className="flex items-center gap-2 mb-3">
            <button
              onClick={() => setInputMode("text")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
                         transition-all duration-200 ${
                           inputMode === "text"
                             ? "bg-jarvis-accent/20 text-jarvis-accent border border-jarvis-accent/30"
                             : "text-jarvis-muted hover:text-jarvis-text hover:bg-jarvis-card"
                         }`}
            >
              <Keyboard className="w-3.5 h-3.5" />
              Chat
            </button>
            <button
              onClick={() => setInputMode("voice")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
                         transition-all duration-200 ${
                           inputMode === "voice"
                             ? "bg-jarvis-accent/20 text-jarvis-accent border border-jarvis-accent/30"
                             : "text-jarvis-muted hover:text-jarvis-text hover:bg-jarvis-card"
                         }`}
            >
              <Mic className="w-3.5 h-3.5" />
              Voice
            </button>
          </div>

          {/* Input Row */}
          {inputMode === "text" ? (
            <div className="flex items-end gap-3">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyDown}
                  placeholder="Message J.A.R.V.I.S. …"
                  rows={1}
                  disabled={isLoading}
                  className="w-full resize-none rounded-2xl bg-jarvis-card border border-jarvis-border
                             px-4 py-3 pr-12 text-sm text-jarvis-text placeholder:text-jarvis-muted
                             focus:outline-none focus:border-jarvis-accent/50 focus:shadow-[0_0_15px_rgba(168,85,247,0.1)]
                             transition-all duration-200 disabled:opacity-50 max-h-40"
                />
              </div>
              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className="flex-shrink-0 w-11 h-11 rounded-xl flex items-center justify-center
                           bg-jarvis-accent text-white hover:bg-jarvis-accent-dim
                           disabled:opacity-30 disabled:cursor-not-allowed
                           transition-all duration-200 hover:shadow-[0_0_20px_rgba(168,85,247,0.3)]"
              >
                <Send className="w-4 h-4" />
              </button>
              {/* Quick voice button in text mode */}
              <VoiceButton
                isRecording={isRecording}
                isProcessing={isProcessing}
                onClick={toggleRecording}
                size="sm"
              />
            </div>
          ) : (
            /* Voice mode — large center mic */
            <div className="flex flex-col items-center gap-4 py-4">
              <VoiceButton
                isRecording={isRecording}
                isProcessing={isProcessing}
                onClick={toggleRecording}
                size="lg"
              />
              <p className="text-sm text-jarvis-muted">
                {isRecording
                  ? "Listening… tap to stop"
                  : isProcessing
                  ? "Processing your request…"
                  : "Tap to speak"}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Empty state ────────────────────────────────────────
function EmptyState() {
  return (
    <div className="flex-1 flex items-center justify-center h-full">
      <div className="text-center space-y-6 max-w-md animate-fade-in">
        {/* Animated logo */}
        <div className="relative mx-auto w-24 h-24">
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-jarvis-accent/30 to-jarvis-accent-dim/20 animate-pulse-glow" />
          <div className="relative w-24 h-24 rounded-2xl bg-gradient-to-br from-jarvis-accent to-jarvis-accent-dim flex items-center justify-center">
            <Sparkles className="w-10 h-10 text-white" />
          </div>
        </div>

        <div>
          <h2 className="text-2xl font-bold text-white mb-2">
            Hello, I&apos;m J.A.R.V.I.S.
          </h2>
          <p className="text-jarvis-muted text-sm leading-relaxed">
            Your offline AI assistant. I can answer questions, explain code,
            open applications, and much more — all running locally on your
            machine.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3 text-left">
          {[
            { icon: "💬", text: "Ask me anything" },
            { icon: "🖥️", text: "Open applications" },
            { icon: "🧑‍💻", text: "Explain code" },
            { icon: "🎤", text: "Talk to me" },
          ].map((item) => (
            <div
              key={item.text}
              className="flex items-center gap-2 px-3 py-2.5 rounded-xl bg-jarvis-card border border-jarvis-border text-sm text-jarvis-muted"
            >
              <span>{item.icon}</span>
              {item.text}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
