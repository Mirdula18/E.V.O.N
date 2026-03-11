// ═══════════════════════════════════════════════════════════
//  VoiceButton — animated microphone button
// ═══════════════════════════════════════════════════════════

"use client";

import { Mic, MicOff, Loader2 } from "lucide-react";

interface VoiceButtonProps {
  isRecording: boolean;
  isProcessing: boolean;
  onClick: () => void;
  size?: "sm" | "md" | "lg";
}

export default function VoiceButton({
  isRecording,
  isProcessing,
  onClick,
  size = "md",
}: VoiceButtonProps) {
  const sizeClasses = {
    sm: "w-10 h-10",
    md: "w-12 h-12",
    lg: "w-16 h-16",
  };

  const iconSize = {
    sm: "w-4 h-4",
    md: "w-5 h-5",
    lg: "w-7 h-7",
  };

  if (isProcessing) {
    return (
      <button
        disabled
        className={`${sizeClasses[size]} rounded-full flex items-center justify-center
                    bg-evon-accent/20 border border-evon-accent/30 cursor-wait`}
      >
        <Loader2 className={`${iconSize[size]} text-evon-accent animate-spin`} />
      </button>
    );
  }

  return (
    <button
      onClick={onClick}
      className={`${sizeClasses[size]} rounded-full flex items-center justify-center
                  transition-all duration-300 relative group
                  ${
                    isRecording
                      ? "bg-red-500/20 border-2 border-red-500 text-red-400 animate-pulse-glow shadow-[0_0_30px_rgba(239,68,68,0.3)]"
                      : "bg-evon-accent/10 border border-evon-accent/30 text-evon-accent hover:bg-evon-accent/20 hover:border-evon-accent/50 hover:shadow-[0_0_20px_rgba(168,85,247,0.2)]"
                  }`}
      title={isRecording ? "Stop recording" : "Start recording"}
    >
      {/* Pulsing ring when recording */}
      {isRecording && (
        <>
          <span className="absolute inset-0 rounded-full border-2 border-red-500/50 animate-ping" />
          <span className="absolute inset-[-4px] rounded-full border border-red-500/20 animate-pulse" />
        </>
      )}

      {isRecording ? (
        <MicOff className={iconSize[size]} />
      ) : (
        <Mic className={iconSize[size]} />
      )}
    </button>
  );
}
