"use client";

import React, { useCallback, useRef, useState } from "react";
import {
  CHAT_MAX_TOKENS,
  multimodalTranscribe,
  multimodalVoiceConversation,
} from "../lib/api";

/**
 * @param {"transcribe"|"pipeline"} mode
 * @param {"chat"|"server"} [pipelineMode="chat"]
 * - transcribe: STT → onTranscript (cola na caixa)
 * - pipeline + chat: STT → onVoiceSubmitChat (mesmo fluxo que enviar texto: mídia, ficheiros, chat)
 * - pipeline + server: POST /v1/multimodal/voice/conversation → onVoicePipelineResult (roteamento no backend + TTS)
 */
export function AudioRecorder({
  token,
  mode = "transcribe",
  /** Só em mode=pipeline: "chat" (padrão) ou "server" (endpoint legado). */
  pipelineMode = "chat",
  onTranscript,
  onError,
  /** @param {string} transcript */
  onVoiceSubmitChat,
  /** @param {object} data resposta JSON do /voice/conversation */
  onVoicePipelineResult,
  buttonLabel,
  buttonIcon,
  className,
}) {
  const [rec, setRec] = useState(null);
  const chunks = useRef([]);
  const [busy, setBusy] = useState(false);
  const [phase, setPhase] = useState("");

  const defaultLabel = "Microfone";

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
          if (pipelineMode === "server") {
            setPhase("llm");
            const data = await multimodalVoiceConversation(
              file,
              token || undefined,
              CHAT_MAX_TOKENS
            );
            if (typeof onVoicePipelineResult === "function") {
              onVoicePipelineResult(data);
            } else if (onError) {
              onError("Configure onVoicePipelineResult no modo pipeline server.");
            }
          } else {
            setPhase("llm");
            const data = await multimodalTranscribe(file, token || undefined);
            const t = (data && data.text) || "";
            if (!t) {
              const detail = (data && data.detail) || "Transcrição vazia.";
              if (onError) onError(detail);
              return;
            }
            if (typeof onVoiceSubmitChat === "function") {
              await onVoiceSubmitChat(t);
            } else if (onError) {
              onError("Configure onVoiceSubmitChat no modo pipeline chat.");
            }
          }
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
  }, [
    onTranscript,
    onError,
    onVoiceSubmitChat,
    onVoicePipelineResult,
    token,
    mode,
    pipelineMode,
  ]);

  var busyText =
    busy && mode === "pipeline"
      ? phase === "stt"
        ? "A transcrever…"
        : pipelineMode === "server"
          ? "A responder e gerar áudio (servidor)…"
          : "A processar (mesmo que o chat)…"
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
          <span className="inline-flex items-center gap-1.5">
            {!busy && buttonIcon ? buttonIcon : null}
            <span>{busy ? busyText || "…" : buttonLabel || defaultLabel}</span>
          </span>
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
