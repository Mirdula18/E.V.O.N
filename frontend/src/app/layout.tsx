import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "J.A.R.V.I.S. — Offline AI Assistant",
  description:
    "A local AI assistant powered by Whisper, Ollama, and Piper TTS. Runs fully offline.",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-jarvis-bg text-jarvis-text overflow-hidden">
        {children}
      </body>
    </html>
  );
}
