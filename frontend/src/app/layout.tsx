import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "E.V.O.N. — Enhanced Voice-Operated Nexus",
  description:
    "An offline AI assistant powered by Whisper, Ollama, and Piper TTS. Runs fully local.",
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
      <body className="min-h-screen bg-evon-bg text-evon-text overflow-hidden">
        {children}
      </body>
    </html>
  );
}
