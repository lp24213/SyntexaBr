"use client";

import React, { useCallback, useRef, useState, useEffect } from "react";
import {
  CHAT_MAX_TOKENS,
  multimodalVoiceConversation,
} from "../lib/api";
import { useLanguage } from "../lib/i18n";

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
  const { t, locale } = useLanguage();
  const [rec, setRec] = useState(null);
  const [mediaStream, setMediaStream] = useState(null);
  const chunks = useRef([]);
  const [busy, setBusy] = useState(false);
  const [phase, setPhase] = useState("");
  const [recording, setRecording] = useState(false);
  const speechRef = useRef(null);
  const [sttReady, setSttReady] = useState(false);
  const [sttError, setSttError] = useState(null);

  // ✅ Carregar modelo STT dinamicamente (lazy + cache)
  useEffect(() => {
    const initSTT = async () => {
      try {
        // ✅ Usar Web Worker se disponível para não bloquear UI
        if (typeof window !== "undefined" && global.transcriber) {
          setSttReady(true);
          setSttError(null);
          return;
        }

        // Show loading feedback
        setPhase("loading_stt");
        
        // Lazy load xenova transformer
        const { pipeline } = await import("@xenova/transformers");
        
        // Timeout para evitar hang indefinido
        const timeoutPromise = new Promise((_, reject) =>
          setTimeout(() => reject(new Error("STT initialization timeout")), 30000)
        );

        const initPromise = pipeline(
          "automatic-speech-recognition", 
          "Xenova/whisper-tiny.pt"
        );

        global.transcriber = await Promise.race([initPromise, timeoutPromise]);
        setSttReady(true);
        setSttError(null);
        setPhase(""); // Clear loading
      } catch (err) {
        console.warn("STT initialization failed:", err);
        setSttError(t("sttNotAvailable", locale));
        setSttReady(false); // Fallback will be used
        setPhase("");
      }
    };

    if (typeof window !== "undefined") {
      // ✅ Init STT de forma não-blocking
      if (!global.transcriber) {
        initSTT();
      }
    }
  }, [locale, t]);

  const transcribeAudio = useCallback(async (file) => {
    try {
      setPhase("stt");
      
      // ✅ Timeout para não travar indefinidamente
      const transcriptionTimeout = new Promise((_, reject) =>
        setTimeout(() => reject(new Error("Transcrição expirou (timeout 60s)")), 60000)
      );

      let transcription;
      
      if (global.transcriber && sttReady) {
        // ✅ Tentar Xenova (com timeout)
        try {
          const arrayBuffer = await file.arrayBuffer();
          const audioContext = new (window.AudioContext || window.webkitAudioContext)();
          const audioData = await audioContext.decodeAudioData(arrayBuffer);
          const samples = audioData.getChannelData(0);
          
          const transcriptPromise = global.transcriber(samples, {
            language: "portuguese",
          }).then(result => result.text);

          transcription = await Promise.race([transcriptPromise, transcriptionTimeout]);
          setPhase("");
          return transcription;
        } catch (xenovaErr) {
          console.warn("Xenova transcription failed, falling back to Web Speech:", xenovaErr);
          // Continua para fallback
        }
      }

      // ✅ Fallback: Web Speech API (mais rápido, menos preciso)
      return new Promise((resolve, reject) => {
        try {
          const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
          if (!SR) {
            reject(new Error(t("voiceEngineNotAvailable", locale)));
            return;
          }

          const recognition = new SR();
          recognition.lang = "pt-BR";
          recognition.continuous = false;
          recognition.interimResults = true;
          
          let finalTranscript = "";
          
          recognition.onresult = (event) => {
            for (let i = event.resultIndex; i < event.results.length; i++) {
              const transcript = event.results[i][0].transcript;
              if (event.results[i].isFinal) {
                finalTranscript += transcript + " ";
              }
            }
          };

          recognition.onend = () => {
            setPhase("");
            resolve(finalTranscript.trim() || "");
          };

          recognition.onerror = (event) => {
            setPhase("");
            reject(new Error(t("sttError", locale).replace("{error}", event.error)));
          };

          // ✅ Timeout para Web Speech também
          const webSpeechTimeout = setTimeout(() => {
            recognition.abort();
            setPhase("");
            reject(new Error("Web Speech timeout"));
          }, 30000);

          recognition.start();
        } catch (err) {
          setPhase("");
          reject(err);
        }
      });
    } catch (err) {
      setPhase("");
      throw err;
    }
  }, [locale, t, sttReady]);

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
        if (onError) onError(t("microphonePermissionDenied", locale));
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
              onError(t("pipelineConfigError", locale));
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
