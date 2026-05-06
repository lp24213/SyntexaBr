"use client";

import React, { useEffect, useRef } from "react";

/** Reproduz URL data: ou https: devolvida pelo TTS (edge-tts no backend). */
export function VoicePlayer({ src, className }) {
  const ref = useRef(null);

  useEffect(() => {
    const el = ref.current;
    if (!el || !src) return;
    el.src = src;
    void el.play().catch(() => {});
  }, [src]);

  if (!src) return null;

  return <audio ref={ref} controls className={className} preload="auto" />;
}
