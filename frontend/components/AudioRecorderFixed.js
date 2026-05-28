"use client";

import React, { useCallback, useRef, useState, useEffect } from "react";
import {
  CHAT_MAX_TOKENS,
  multimodalVoiceConversation,
} from "../lib/api";

/**
 * AudioRecorder Robusto - STT com Xenova + Fallback Web Speech API
 */
export function AudioRecorder({
  token,
  mode = "transcribe",
  pipelineMode = "chat",
  onTranscript,
  onError,
  onVoiceSubmitChat,
  onVoicePipelineResult,
  buttonLabel,
  buttonIcon,
  className = "",
}) {
  const [rec, setRec] = useState(null);
  const [mediaStream, setMediaStream] = useState(null);
  const chunks = useRef([]);
  const [busy, setBusy] = useState(false);
  const [phase, setPhase] = useState("");
  const [recording, setRecording] = useState(false);
  const speechRef = useRef(null);
  const [sttReady, setSttReady] = useState(false);
  const [sttError, setSttError] = useState(null);

  // Carregar modelo STT dinamicamente
  useEffect(() => {
    const initSTT = async () => {
      try {
        // Lazy load xenova transformer
        const { pipeline } = await import("@xenova/transformers");
        // Pré-carregar modelo para melhor performance
        global.transcriber = global.transcriber || 
          await pipeline("automatic-speech-recognition", "Xenova/whisper-tiny.pt");
        setSttReady(true);
        setSttError(null);
      } catch (err) {
        setSttError("Modelo STT não disponível, usando fallback");
        setSttReady(false);
      }
    };

    if (typeof window !== "undefined") {
      initSTT();
    }
  }, []);

  const transcribeAudio = useCallback(async (file) => {
    try {
      setPhase("stt");
      
      if (!global.transcriber) {
        throw new Error("STT não inicializado");
      }

      const arrayBuffer = await file.arrayBuffer();
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const audioData = await audioContext.decodeAudioData(arrayBuffer);

      // Extrair samples de áudio
      const samples = audioData.getChannelData(0);
      
      // Usar modelo
      const { text } = await global.transcriber(samples, {
        language: "portuguese",
      });

      return text;
    } catch (err) {
      // Fallback para Web Speech API
      return new Promise((resolve, reject) => {
        try {
          const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
          if (!SR) {
            reject(new Error("Nenhum motor de voz disponível"));
            return;
          }

          const recognition = new SR();
          recognition.lang = "pt-BR";
          recognition.continuous = false;
          
          recognition.onresult = (event) => {
            const transcript = Array.from(event.results)
              .map(result => result[0].transcript)
              .join("");
            resolve(transcript);
          };

          recognition.onerror = (event) => {
            reject(new Error(`Erro STT: ${event.error}`));
          };

          recognition.start();
        } catch (err) {
          reject(err);
        }
      });
    }
  }, []);

  const stopSpeech = useCallback(() => {
    try {
      if (speechRef.current) {
        speechRef.current.stop?.();
        speechRef.current.abort?.();
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
    if (mediaStream) {
      mediaStream.getTracks().forEach((t) => t.stop());
      setMediaStream(null);
    }
    stopSpeech();
    setRec(null);
    setRecording(false);
  }, [rec, mediaStream, stopSpeech]);

  const startRecording = useCallback(async () => {
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: { 
          echoCancellation: true, 
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
    } catch (e1) {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      } catch (e2) {
        if (onError) onError("Permissão de microfone negada");
        throw e1;
      }
    }

    setMediaStream(stream);

    // Determinar MIME type
    let mime = "audio/webm";
    if (typeof MediaRecorder !== "undefined") {
      if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
        mime = "audio/webm;codecs=opus";
      } else if (!MediaRecorder.isTypeSupported("audio/webm")) {
        if (MediaRecorder.isTypeSupported("audio/mp4")) mime = "audio/mp4";
        else mime = "";
      }
    }

    const mrOpts = mime ? { mimeType: mime } : undefined;
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
            const transcript = await transcribeAudio(file);
            if (typeof onVoiceSubmitChat === "function") {
              setPhase("processing");
              await onVoiceSubmitChat(transcript);
            } else if (onError) {
              onError("Configure onVoiceSubmitChat no modo pipeline chat.");
            }
          }
        } else {
          const transcript = await transcribeAudio(file);
          if (transcript && onTranscript) {
            onTranscript(transcript);
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
  }, [mode, pipelineMode, token, onTranscript, onError, onVoiceSubmitChat, onVoicePipelineResult, transcribeAudio]);

  const handleToggle = useCallback(() => {
    if (recording) {
      stop();
    } else {
      startRecording().catch((err) => {
        if (onError) onError(err.message || "Erro ao iniciar gravação");
      });
    }
  }, [recording, stop, startRecording, onError]);

  const displayStatus = 
    recording ? "Gravando..." :
    busy && phase === "stt" ? "Transcrevendo..." :
    busy && phase === "llm" ? "Processando..." :
    busy && phase === "processing" ? "Processando..." :
    sttError ? "Erro STT" :
    buttonLabel || "🎤 Microfone";

  return (
    <button
      onClick={handleToggle}
      disabled={busy || !navigator.mediaDevices}
      className={`
        px-4 py-2 rounded-lg font-medium transition-all
        ${recording 
          ? "bg-red-500 hover:bg-red-600 text-white" 
          : "bg-blue-500 hover:bg-blue-600 text-white"
        }
        disabled:opacity-50 disabled:cursor-not-allowed
        ${className}
      `}
      title={sttError || "Clique para gravar"}
    >
      {buttonIcon || "🎤"} {displayStatus}
    </button>
  );
}
