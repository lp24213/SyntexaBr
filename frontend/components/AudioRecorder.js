"use client";

import React, { useCallback, useRef, useState } from "react";
import { CHAT_MAX_TOKENS, multimodalTranscribe, multimodalVoiceConversation } from "../lib/api";

/**
 * @param {"transcribe"|"pipeline"} mode
 * - transcribe: STT → onTranscript (cola na caixa)
 * - pipeline: STT → chat → TTS no servidor → onVoicePipelineResult
 */
export function AudioRecorder({
  token,
  mode = "transcribe",
  onTranscript,
  onError,
  onVoicePipelineResult,
  buttonLabel,
  className,
}) {
  const [rec, setRec] = useState(null);
  const chunks = useRef([]);
  const [busy, setBusy] = useState(false);
  const [phase, setPhase] = useState("");

  const defaultLabel =
    mode === "pipeline"
      ? "Perguntar em voz (IA)"
      : "Gravar voz";

  const stop = useCallback(() => {
    if (rec && rec.state !== "inactive") {
      try {
        if (rec.state === "recording") rec.requestData();
      } catch (_) {}
      rec.stop();
    }
    setRec(null);
  }, [rec]);

  const start = useCallback(async () => {
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true },
      });
    } catch (e) {
      if (onError) onError(e instanceof Error ? e.message : "Microfone indisponível (HTTPS e permissão necessários).");
      return;
    }
    const mr = new MediaRecorder(stream, {
      mimeType: MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : undefined,
    });
    chunks.current = [];
    mr.ondataavailable = (e) => {
      if (e.data.size) chunks.current.push(e.data);
    };
    mr.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      const blob = new Blob(chunks.current, { type: mr.mimeType || "audio/webm" });
      const file = new File([blob], "gravacao.webm", { type: blob.type || "audio/webm" });
      setBusy(true);
      setPhase("stt");
      try {
        if (mode === "pipeline") {
          setPhase("llm");
          const data = await multimodalVoiceConversation(
            file,
            token || undefined,
            CHAT_MAX_TOKENS
          );
          if (typeof onVoicePipelineResult === "function") onVoicePipelineResult(data);
        } else {
          const data = await multimodalTranscribe(file, token || undefined);
          const t = (data && data.text) || "";
          if (t) {
            if (onTranscript) onTranscript(t);
          } else {
            const detail = (data && data.detail) || "Transcrição vazia.";
            if (onError) onError(detail);
          }
        }
      } catch (e) {
        if (onError) onError(e instanceof Error ? e.message : String(e));
      } finally {
        setBusy(false);
        setPhase("");
      }
    };
    mr.start(250);
    setRec(mr);
  }, [onTranscript, onError, onVoicePipelineResult, token, mode]);

  var busyText =
    busy && mode === "pipeline"
      ? phase === "stt"
        ? "A transcrever…"
        : "A responder e gerar áudio…"
      : busy
        ? "A transcrever…"
        : "";

  return (
    <div className={className}>
      {!rec ? (
        <button
          type="button"
          disabled={busy}
          className={
            mode === "pipeline"
              ? "rounded-lg border border-sky-700/80 bg-sky-950/50 px-3 py-2 text-sm text-sky-100"
              : "rounded-lg border border-emerald-700/80 bg-emerald-950/50 px-3 py-2 text-sm text-emerald-100"
          }
          onClick={() => void start()}
        >
          {busy ? busyText || "…" : buttonLabel || defaultLabel}
        </button>
      ) : (
        <button
          type="button"
          className="rounded-lg border border-red-700/80 bg-red-950/50 px-3 py-2 text-sm text-red-100"
          onClick={stop}
        >
          Parar
        </button>
      )}
    </div>
  );
}
