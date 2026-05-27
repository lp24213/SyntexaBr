"use client";

import React, { useEffect, useState, useRef } from "react";

/**
 * TurnstileWidget - Componente robusto para Cloudflare Turnstile
 * - Carregamento assíncrono seguro
 * - Retry automático
 * - Fallback visual
 */
export function TurnstileWidget({ 
  siteKey,
  onTokenReceived,
  onError,
  theme = "light",
  size = "normal",
  className = "",
  retryAttempts = 3,
}) {
  const [isReady, setIsReady] = useState(false);
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const containerRef = useRef(null);
  const widgetIdRef = useRef(null);

  // Carregar script do Turnstile com retry
  useEffect(() => {
    if (!siteKey || typeof window === "undefined") {
      setLoading(false);
      return;
    }

    const loadTurnstile = (attemptCount = 0) => {
      // Verificar se já existe
      if (window.turnstile) {
        setIsReady(true);
        setLoading(false);
        return;
      }

      // Verificar se o script já está no DOM (head ou body)
      const existing = document.querySelector('script[src*="challenges.cloudflare.com/turnstile"]');
      if (existing) {
        // Aguardar carregamento
        const checkInterval = setInterval(() => {
          if (window.turnstile) {
            clearInterval(checkInterval);
            setIsReady(true);
            setLoading(false);
          }
        }, 100);
        setTimeout(() => clearInterval(checkInterval), 10000);
        return;
      }

      // Criar e carregar script no HEAD
      const script = document.createElement("script");
      script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js";
      script.async = true;
      script.defer = true;
      script.crossOrigin = "anonymous";
      
      script.onload = () => {
        // Dar tempo para o Turnstile estar pronto
        setTimeout(() => {
          if (window.turnstile) {
            setIsReady(true);
            setLoading(false);
            setError(null);
          } else {
            // Se turnstile ainda não está pronto após 1s, falhar
            setError("Turnstile não carregou corretamente");
            setLoading(false);
          }
        }, 500);
      };

      script.onerror = () => {
        if (attemptCount < retryAttempts) {
          const newAttempt = attemptCount + 1;
          console.warn(`[Turnstile] Retry ${newAttempt}/${retryAttempts}`);
          setTimeout(() => loadTurnstile(newAttempt), 2000);
        } else {
          console.error("[Turnstile] Script load failed after retries");
          setError("Falha ao carregar verificação de segurança");
          setLoading(false);
          if (onError) onError("Script não carregou");
        }
      };

      // Injeta no HEAD (mais confiável que BODY)
      (document.head || document.documentElement).appendChild(script);
      console.log("[Turnstile] Script injected");
    };

    loadTurnstile();
  }, [siteKey, onError, retryAttempts]);

  // Renderizar widget quando pronto
  useEffect(() => {
    if (!isReady || !siteKey || !containerRef.current || !window.turnstile) {
      return;
    }

    try {
      // Limpar widget anterior se existe
      if (widgetIdRef.current) {
        try {
          window.turnstile.remove(widgetIdRef.current);
        } catch (_) {}
      }

      // Renderizar widget
      widgetIdRef.current = window.turnstile.render(containerRef.current, {
        sitekey: siteKey,
        theme: theme,
        size: size,
        callback: (token) => {
          setToken(token);
          if (onTokenReceived) onTokenReceived(token);
        },
        "error-callback": () => {
          setError("Erro ao verificar. Tente novamente.");
          if (onError) onError("Erro no widget");
        },
        "expired-callback": () => {
          setToken("");
          if (onError) onError("Verificação expirou");
        },
        "timeout-callback": () => {
          setError("Tempo limite excedido");
          if (onError) onError("Timeout");
        },
        retry: "auto",
        "retry-interval": 5000,
        appearance: "interaction-only",
      });
    } catch (err) {
      setError("Erro ao renderizar widget");
      if (onError) onError(err.message);
    }

    return () => {
      try {
        if (widgetIdRef.current && window.turnstile) {
          window.turnstile.remove(widgetIdRef.current);
        }
      } catch (_) {}
    };
  }, [isReady, siteKey, theme, size, onTokenReceived, onError]);

  if (!siteKey) {
    return null;
  }

  return (
    <div className={`flex justify-center ${className}`}>
      <div 
        ref={containerRef}
        className={`${loading ? "bg-gray-100 rounded-lg p-3 animate-pulse" : ""}`}
        style={{
          minHeight: loading ? "65px" : "auto",
          minWidth: loading ? "300px" : "auto",
        }}
      >
        {loading && (
          <div className="text-xs text-gray-400 text-center py-2">
            Carregando verificação de segurança...
          </div>
        )}
      </div>
      {error && (
        <div className="text-xs text-red-500 mt-2 text-center">
          {error}
        </div>
      )}
    </div>
  );
}

/**
 * Hook simples para usar Turnstile
 */
export function useTurnstileToken(siteKey) {
  const [token, setToken] = useState("");
  const [ready, setReady] = useState(false);
  const widgetRef = useRef(null);

  useEffect(() => {
    if (!siteKey || typeof window === "undefined") return;

    const loadScript = async () => {
      if (window.turnstile) {
        setReady(true);
        return;
      }

      return new Promise((resolve) => {
        const script = document.createElement("script");
        script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js";
        script.async = true;
        script.defer = true;
        script.onload = () => {
          setReady(true);
          resolve();
        };
        document.body.appendChild(script);
      });
    };

    loadScript();
  }, [siteKey]);

  useEffect(() => {
    if (!ready || !siteKey || !widgetRef.current || !window.turnstile) return;

    try {
      const id = window.turnstile.render(widgetRef.current, {
        sitekey: siteKey,
        callback: (tok) => setToken(tok),
        "expired-callback": () => setToken(""),
        "error-callback": () => setToken(""),
      });

      return () => {
        try {
          if (window.turnstile && id) window.turnstile.remove(id);
        } catch (_) {}
      };
    } catch (_) {}
  }, [ready, siteKey]);

  return { token, widgetRef, ready };
}
