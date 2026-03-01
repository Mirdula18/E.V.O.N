// ═══════════════════════════════════════════════════════════
//  J.A.R.V.I.S. — Main Page
// ═══════════════════════════════════════════════════════════

"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import ChatInterface from "@/components/ChatInterface";
import { useChat } from "@/hooks/useChat";
import { healthCheck } from "@/lib/api";
import { Menu, X, Wifi, WifiOff } from "lucide-react";

export default function Home() {
  const {
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
  } = useChat();

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");

  // ── Check backend health ──────────────────────────────
  useEffect(() => {
    const check = async () => {
      try {
        await healthCheck();
        setBackendStatus("online");
      } catch {
        setBackendStatus("offline");
      }
    };
    check();
    const interval = setInterval(check, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex h-screen w-screen overflow-hidden">
      {/* ── Mobile sidebar overlay ─────────────────────── */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ── Sidebar ────────────────────────────────────── */}
      <div
        className={`fixed lg:relative z-40 h-full transition-transform duration-300 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0 lg:w-0 lg:overflow-hidden"
        }`}
      >
        <Sidebar
          conversations={conversations}
          activeId={activeConversationId}
          onSelect={(id) => {
            loadConversation(id);
            setSidebarOpen(false);
          }}
          onNew={() => {
            newConversation();
            setSidebarOpen(false);
          }}
          onDelete={deleteConversation}
          onClearAll={clearAll}
          onLoadConversations={loadConversations}
        />
      </div>

      {/* ── Main area ──────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="flex items-center justify-between px-4 py-2 border-b border-jarvis-border bg-jarvis-surface/50 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 rounded-lg hover:bg-jarvis-card text-jarvis-muted transition-colors"
            >
              {sidebarOpen ? (
                <X className="w-5 h-5" />
              ) : (
                <Menu className="w-5 h-5" />
              )}
            </button>
            <div className="text-sm font-medium text-jarvis-text">
              {activeConversationId
                ? conversations.find((c) => c.id === activeConversationId)?.title || "Conversation"
                : "New Conversation"}
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Backend status indicator */}
            <div
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                backendStatus === "online"
                  ? "bg-green-500/10 text-green-400 border border-green-500/20"
                  : backendStatus === "offline"
                  ? "bg-red-500/10 text-red-400 border border-red-500/20"
                  : "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20"
              }`}
            >
              {backendStatus === "online" ? (
                <Wifi className="w-3 h-3" />
              ) : (
                <WifiOff className="w-3 h-3" />
              )}
              {backendStatus === "checking"
                ? "Checking…"
                : backendStatus === "online"
                ? "Backend Online"
                : "Backend Offline"}
            </div>
          </div>
        </header>

        {/* Chat interface */}
        <ChatInterface
          messages={messages}
          streamingContent={streamingContent}
          isLoading={isLoading}
          activeConversationId={activeConversationId}
          onSendMessage={sendMessage}
          onAddVoiceMessages={addVoiceMessages}
        />
      </div>
    </div>
  );
}
