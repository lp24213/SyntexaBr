"use client";

import React, { useCallback, useRef, useState } from "react";
import {
  CHAT_MAX_TOKENS,
  multimodalVoiceConversation,
} from "../lib/api";
import { transcribeWithXenova } from "../lib/xenova-stt";

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
  const [recording, setRecording] = useState(false);
  const speechRef = useRef(null);

  const defaultLabel = "Microfone";

  const stopSpeech = useCallback(() => {
    try {
      if (speechRef.current) {
        speechRef.current.stop();
        speechRef.current.abort();
        speechRef.current = null;
      }
    } catch (_) {}
  }, []);

  const stop = useCallback(() => {
    if (rec && rec.state !== "inactive") {
      try {
        if (rec.state === "recording") rec.requestData();
      } catch (_) {}
      rec.stop();
    }
    stopSpeech();
    setRec(null);
    setRecording(false);
  }, [rec, stopSpeech]);

  const startMediaRecorder = useCallback(async () => {
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true },
      });
    } catch (e1) {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      } catch (e2) {
        throw e1;
      }
    }
    var mime = "audio/webm";
    if (typeof MediaRecorder !== "undefined") {
      if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) mime = "audio/webm;codecs=opus";
      else if (!MediaRecorder.isTypeSupported("audio/webm")) {
        if (MediaRecorder.isTypeSupported("audio/mp4")) mime = "audio/mp4";
        else mime = "";
      }
    }
    var mrOpts = mime ? { mimeType: mime } : undefined;
    const mr = new MediaRecorder(stream, mrOpts);
    chunks.current = [];
    setRecording(true);
    mr.ondataavailable = (e) => {
      if (e.data.size) chunks.current.push(e.data);
    };
    mr.onstop = async () => {
      setRecording(false);
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
            const t = await transcribeWithXenova(file, { language: "portuguese" });
            if (typeof onVoiceSubmitChat === "function") {
              await onVoiceSubmitChat(t);
            } else if (onError) {
              onError("Configure onVoiceSubmitChat no modo pipeline chat.");
            }
          }
        } else {
          const t = await transcribeWithXenova(file, { language: "portuguese" });
          if (t && onTranscript) onTranscript(t);
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

  const startWebSpeechFallback = useCallback(() => {
    var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return false;
    stopSpeech();
    var rec = new SR();
    rec.lang = "pt-BR";
    rec.continuous = false;
    rec.interimResults = true;
    var finalTranscript = "";
    var interimTranscript = "";
    rec.onstart = function () {
      speechRef.current = rec;
      setRecording(true);
    };
    rec.onresult = function (event) {
      interimTranscript = "";
      for (var i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }
    };
    rec.onerror = function (event) {
      speechRef.current = null;
      setRecording(false);
      var msg = event.error === "not-allowed" || event.error === "service-not-allowed"
        ? "Microfone bloqueado. Clique no cadeado ao lado da URL e permita o acesso."
        : event.error === "no-speech"
          ? "Nenhuma fala detectada."
          : "Erro no reconhecimento de voz: " + event.error;
      if (onError) onError(msg);
    };
    rec.onend = function () {
      speechRef.current = null;
      setRecording(false);
      if (finalTranscript) {
        if (typeof onTranscript === "function") onTranscript(finalTranscript);
        else if (typeof onVoiceSubmitChat === "function") onVoiceSubmitChat(finalTranscript);
      }
    };
    try {
      rec.start();
      return true;
    } catch (e) {
      return false;
    }
  }, [onError, onTranscript, onVoiceSubmitChat, stopSpeech]);

  const start = useCallback(async () => {
    try {
      await startMediaRecorder();
    } catch (e) {
      var errName = e && e.name ? e.name : "";
      var isPermissionDenied = errName === "NotAllowedError" || errName === "PermissionDeniedError";
      if (isPermissionDenied) {
        var started = startWebSpeechFallback();
        if (!started && onError) {
          onError("Microfone bloqueado pelo navegador. Clique no cadeado ao lado da URL → Microfone → Permitir. Depois recarregue a página.");
        }
      } else {
        if (onError) onError(e instanceof Error ? e.message : "Microfone indisponível (HTTPS e permissão necessários).");
      }
    }
  }, [startMediaRecorder, startWebSpeechFallback, onError]);

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
      {!recording ? (
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
