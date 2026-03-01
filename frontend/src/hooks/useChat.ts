// ═══════════════════════════════════════════════════════════
//  useChat — manages conversation state & streaming
// ═══════════════════════════════════════════════════════════

"use client";

import { useCallback, useRef, useState } from "react";
import type { ConversationListItem, Message, StreamEvent } from "@/types";
import {
  getConversation,
  getConversations,
  streamMessage,
  deleteConversation as apiDeleteConversation,
  clearConversations as apiClearConversations,
} from "@/lib/api";

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversations, setConversations] = useState<ConversationListItem[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const abortRef = useRef<AbortController | null>(null);

  // ── Load conversations list ────────────────────────────
  const loadConversations = useCallback(async () => {
    try {
      const convs = await getConversations();
      setConversations(convs);
    } catch (err) {
      console.error("Failed to load conversations:", err);
    }
  }, []);

  // ── Load a specific conversation ──────────────────────
  const loadConversation = useCallback(async (id: string) => {
    try {
      const conv = await getConversation(id);
      setMessages(conv.messages);
      setActiveConversationId(id);
    } catch (err) {
      console.error("Failed to load conversation:", err);
    }
  }, []);

  // ── Start a new conversation ──────────────────────────
  const newConversation = useCallback(() => {
    setMessages([]);
    setActiveConversationId(null);
    setStreamingContent("");
  }, []);

  // ── Send message with streaming ───────────────────────
  const sendMessage = useCallback(
    async (text: string, inputMode: "text" | "voice" = "text") => {
      if (!text.trim() || isLoading) return;
      setIsLoading(true);
      setStreamingContent("");

      // Optimistic user message
      const tempUserMsg: Message = {
        id: `temp-${Date.now()}`,
        conversation_id: activeConversationId || "",
        role: "user",
        content: text,
        input_mode: inputMode,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, tempUserMsg]);

      try {
        let convId = activeConversationId;
        let fullResponse = "";

        for await (const event of streamMessage({
          conversation_id: activeConversationId,
          message: text,
          input_mode: inputMode,
        })) {
          switch (event.type) {
            case "meta":
              if (event.conversation_id) {
                convId = event.conversation_id;
                setActiveConversationId(convId);
              }
              break;
            case "token":
              fullResponse += event.content || "";
              setStreamingContent(fullResponse);
              break;
            case "done":
              // Add the complete assistant message
              const assistantMsg: Message = {
                id: event.message_id || `asst-${Date.now()}`,
                conversation_id: convId || "",
                role: "assistant",
                content: event.content || fullResponse,
                input_mode: "text",
                created_at: new Date().toISOString(),
              };
              setMessages((prev) => [...prev, assistantMsg]);
              setStreamingContent("");
              break;
            case "error":
              console.error("Stream error:", event.content);
              break;
          }
        }

        await loadConversations();
      } catch (err) {
        console.error("Send message failed:", err);
        // Remove optimistic message on error
        setMessages((prev) => prev.filter((m) => m.id !== tempUserMsg.id));
      } finally {
        setIsLoading(false);
        setStreamingContent("");
      }
    },
    [activeConversationId, isLoading, loadConversations]
  );

  // ── Add messages from voice pipeline ──────────────────
  const addVoiceMessages = useCallback(
    (userMsg: Message, assistantMsg: Message, convId: string) => {
      setActiveConversationId(convId);
      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      loadConversations();
    },
    [loadConversations]
  );

  // ── Delete conversation ───────────────────────────────
  const deleteConversation = useCallback(
    async (id: string) => {
      try {
        await apiDeleteConversation(id);
        if (activeConversationId === id) {
          newConversation();
        }
        await loadConversations();
      } catch (err) {
        console.error("Delete failed:", err);
      }
    },
    [activeConversationId, loadConversations, newConversation]
  );

  // ── Clear all conversations ───────────────────────────
  const clearAll = useCallback(async () => {
    try {
      await apiClearConversations();
      newConversation();
      setConversations([]);
    } catch (err) {
      console.error("Clear failed:", err);
    }
  }, [newConversation]);

  return {
    messages,
    conversations,
    activeConversationId,
    isLoading,
    streamingContent,
    sendMessage,
    loadConversations,
    loadConversation,
    newConversation,
    deleteConversation,
    clearAll,
    addVoiceMessages,
  };
}
