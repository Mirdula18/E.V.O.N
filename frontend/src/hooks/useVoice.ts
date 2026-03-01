// ═══════════════════════════════════════════════════════════
//  useVoice — microphone recording + voice pipeline
// ═══════════════════════════════════════════════════════════

"use client";

import { useCallback, useRef, useState } from "react";
import { voicePipeline, textToSpeech } from "@/lib/api";
import type { Message, VoicePipelineResult } from "@/types";

export interface UseVoiceOptions {
  conversationId: string | null;
  onResult?: (result: VoicePipelineResult) => void;
  onTranscription?: (text: string) => void;
  onError?: (error: string) => void;
}

export function useVoice({
  conversationId,
  onResult,
  onTranscription,
  onError,
}: UseVoiceOptions) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);

  // ── Start recording ───────────────────────────────────
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000,
        },
      });

      // Setup audio analyser for waveform visualization
      const audioCtx = new AudioContext();
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);

      audioContextRef.current = audioCtx;
      analyserRef.current = analyser;
      sourceRef.current = source;

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
          ? "audio/webm;codecs=opus"
          : "audio/webm",
      });

      chunksRef.current = [];
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        // Cleanup stream
        stream.getTracks().forEach((t) => t.stop());
        source.disconnect();
        audioCtx.close();

        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        if (blob.size < 100) {
          onError?.("Recording too short");
          return;
        }
        await processRecording(blob);
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start(100); // collect data every 100ms
      setIsRecording(true);
    } catch (err) {
      console.error("Microphone access failed:", err);
      onError?.("Microphone access denied. Please allow microphone access.");
    }
  }, [conversationId, onResult, onTranscription, onError]);

  // ── Stop recording ────────────────────────────────────
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
  }, []);

  // ── Process recording through voice pipeline ──────────
  const processRecording = useCallback(
    async (blob: Blob) => {
      setIsProcessing(true);
      try {
        const result = await voicePipeline(blob, conversationId);
        onTranscription?.(result.transcription);
        onResult?.(result);

        // Play TTS response
        if (result.has_audio) {
          await playTTS(result.response);
        }
      } catch (err) {
        console.error("Voice pipeline error:", err);
        onError?.("Voice processing failed. Is the backend running?");
      } finally {
        setIsProcessing(false);
      }
    },
    [conversationId, onResult, onTranscription, onError]
  );

  // ── Play TTS audio ───────────────────────────────────
  const playTTS = useCallback(async (text: string) => {
    try {
      setIsSpeaking(true);
      const audioBlob = await textToSpeech(text);
      const url = URL.createObjectURL(audioBlob);
      const audio = new Audio(url);
      audio.onended = () => {
        setIsSpeaking(false);
        URL.revokeObjectURL(url);
      };
      audio.onerror = () => {
        setIsSpeaking(false);
        URL.revokeObjectURL(url);
      };
      await audio.play();
    } catch (err) {
      console.error("TTS playback failed:", err);
      setIsSpeaking(false);
    }
  }, []);

  // ── Toggle recording ─────────────────────────────────
  const toggleRecording = useCallback(() => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }, [isRecording, startRecording, stopRecording]);

  // ── Get analyser for waveform ────────────────────────
  const getAnalyser = useCallback(() => analyserRef.current, []);

  return {
    isRecording,
    isProcessing,
    isSpeaking,
    startRecording,
    stopRecording,
    toggleRecording,
    playTTS,
    getAnalyser,
  };
}
