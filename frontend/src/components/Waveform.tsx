// ═══════════════════════════════════════════════════════════
//  Waveform — animated audio visualizer bars
// ═══════════════════════════════════════════════════════════

"use client";

import { useEffect, useRef } from "react";

interface WaveformProps {
  isActive: boolean;
  barCount?: number;
  analyser?: AnalyserNode | null;
}

export default function Waveform({
  isActive,
  barCount = 32,
  analyser,
}: WaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animFrameRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;
    const barWidth = width / barCount;
    const bufferLength = analyser?.frequencyBinCount || barCount;
    const dataArray = new Uint8Array(bufferLength);

    let phase = 0;

    const draw = () => {
      ctx.clearRect(0, 0, width, height);

      if (isActive && analyser) {
        // Real audio data
        analyser.getByteFrequencyData(dataArray);
        for (let i = 0; i < barCount; i++) {
          const dataIndex = Math.floor((i / barCount) * bufferLength);
          const value = dataArray[dataIndex] / 255;
          const barHeight = Math.max(2, value * height * 0.9);
          const x = i * barWidth;
          const y = (height - barHeight) / 2;

          const gradient = ctx.createLinearGradient(x, y, x, y + barHeight);
          gradient.addColorStop(0, `rgba(168, 85, 247, ${0.4 + value * 0.6})`);
          gradient.addColorStop(0.5, `rgba(192, 132, 252, ${0.6 + value * 0.4})`);
          gradient.addColorStop(1, `rgba(168, 85, 247, ${0.4 + value * 0.6})`);

          ctx.fillStyle = gradient;
          ctx.beginPath();
          ctx.roundRect(x + 1, y, barWidth - 2, barHeight, 2);
          ctx.fill();
        }
      } else if (isActive) {
        // Animated sine wave (no analyser)
        phase += 0.05;
        for (let i = 0; i < barCount; i++) {
          const value =
            0.3 +
            0.7 *
              Math.abs(
                Math.sin(phase + (i * Math.PI) / barCount) *
                  Math.cos(phase * 0.7 + (i * Math.PI) / (barCount * 0.5))
              );
          const barHeight = Math.max(2, value * height * 0.8);
          const x = i * barWidth;
          const y = (height - barHeight) / 2;

          const gradient = ctx.createLinearGradient(x, y, x, y + barHeight);
          gradient.addColorStop(0, `rgba(168, 85, 247, ${0.3 + value * 0.5})`);
          gradient.addColorStop(0.5, `rgba(192, 132, 252, ${0.5 + value * 0.5})`);
          gradient.addColorStop(1, `rgba(168, 85, 247, ${0.3 + value * 0.5})`);

          ctx.fillStyle = gradient;
          ctx.beginPath();
          ctx.roundRect(x + 1, y, barWidth - 2, barHeight, 2);
          ctx.fill();
        }
      } else {
        // Idle state — flat bars
        for (let i = 0; i < barCount; i++) {
          const x = i * barWidth;
          const barHeight = 2;
          const y = (height - barHeight) / 2;
          ctx.fillStyle = "rgba(168, 85, 247, 0.15)";
          ctx.fillRect(x + 1, y, barWidth - 2, barHeight);
        }
      }

      animFrameRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(animFrameRef.current);
    };
  }, [isActive, barCount, analyser]);

  return (
    <canvas
      ref={canvasRef}
      className="w-full h-12 rounded-xl"
      style={{ imageRendering: "crisp-edges" }}
    />
  );
}
