// ═══════════════════════════════════════════════════════════
//  Sidebar — conversation list + new chat button
// ═══════════════════════════════════════════════════════════

"use client";

import { useEffect } from "react";
import {
  MessageSquarePlus,
  Trash2,
  MessageCircle,
  Settings,
  Cpu,
  Zap,
} from "lucide-react";
import type { ConversationListItem } from "@/types";

interface SidebarProps {
  conversations: ConversationListItem[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  onClearAll: () => void;
  onLoadConversations: () => void;
}

export default function Sidebar({
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
  onClearAll,
  onLoadConversations,
}: SidebarProps) {
  useEffect(() => {
    onLoadConversations();
  }, [onLoadConversations]);

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHrs = Math.floor(diffMins / 60);
    if (diffHrs < 24) return `${diffHrs}h ago`;
    const diffDays = Math.floor(diffHrs / 24);
    if (diffDays < 7) return `${diffDays}d ago`;
    return d.toLocaleDateString();
  };

  return (
    <aside className="w-72 h-full flex flex-col bg-evon-surface border-r border-evon-border">
      {/* Header */}
      <div className="p-4 border-b border-evon-border">
        <div className="flex items-center gap-3 mb-4">
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-evon-accent to-evon-accent-dim flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 rounded-full border-2 border-evon-surface" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-wide">
              E.V.O.N.
            </h1>
            <p className="text-xs text-evon-muted">Offline AI Assistant</p>
          </div>
        </div>

        <button
          onClick={onNew}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl
                     bg-evon-accent/10 text-evon-accent border border-evon-accent/20
                     hover:bg-evon-accent/20 hover:border-evon-accent/40
                     transition-all duration-200 font-medium text-sm"
        >
          <MessageSquarePlus className="w-4 h-4" />
          New Conversation
        </button>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1 scrollbar-thin">
        {conversations.length === 0 ? (
          <div className="text-center py-8 text-evon-muted text-sm">
            <MessageCircle className="w-8 h-8 mx-auto mb-2 opacity-30" />
            No conversations yet
          </div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => onSelect(conv.id)}
              className={`group flex items-center gap-3 p-3 rounded-xl cursor-pointer
                         transition-all duration-200 ${
                           activeId === conv.id
                             ? "bg-evon-accent/15 border border-evon-accent/30"
                             : "hover:bg-evon-card border border-transparent"
                         }`}
            >
              <MessageCircle
                className={`w-4 h-4 flex-shrink-0 ${
                  activeId === conv.id
                    ? "text-evon-accent"
                    : "text-evon-muted"
                }`}
              />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-evon-text truncate">
                  {conv.title}
                </p>
                <p className="text-xs text-evon-muted mt-0.5">
                  {conv.message_count} msgs · {formatDate(conv.updated_at)}
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(conv.id);
                }}
                className="opacity-0 group-hover:opacity-100 p-1 rounded-lg
                           hover:bg-red-500/20 text-evon-muted hover:text-red-400
                           transition-all duration-200"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-evon-border space-y-1">
        {conversations.length > 0 && (
          <button
            onClick={onClearAll}
            className="w-full flex items-center gap-2 py-2 px-3 rounded-lg text-sm
                       text-evon-muted hover:text-red-400 hover:bg-red-500/10
                       transition-all duration-200"
          >
            <Trash2 className="w-4 h-4" />
            Clear all conversations
          </button>
        )}
        <div className="flex items-center gap-2 py-2 px-3 text-xs text-evon-muted">
          <Cpu className="w-3.5 h-3.5" />
          <span>Running locally</span>
        </div>
      </div>
    </aside>
  );
}
