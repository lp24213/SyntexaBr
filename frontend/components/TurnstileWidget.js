"use client";

import React, { useEffect, useRef } from "react";

/**
 * TurnstileWidget - Simples, robusto e otimizado para produção
 * - Sem loops de re-render
 * - Polling controlado para window.turnstile
 * - Callbacks corretos
 * - Melhor tratamento de erros
 * - Logging para debug
 */
export function TurnstileWidget({ 
  siteKey,
  onTokenReceived,
  onError,
  theme = "light",
  size = "normal",
  className = "",
}) {
  const containerRef = useRef(null);
  const widgetIdRef = useRef(null);
  const pollCountRef = useRef(0);
  const scriptLoadedRef = useRef(false);

  // 1. Carregar script uma única vez globalmente
  useEffect(() => {
    if (typeof window === "undefined" || window.turnstile || scriptLoadedRef.current) return;
    
    scriptLoadedRef.current = true;
    const script = document.createElement("script");
    script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js";
    script.async = true;
    script.crossOrigin = "anonymous";
    script.defer = true;
    
    script.onload = () => {
      console.log("[Turnstile] Script loaded successfully");
    };
    
    script.onerror = () => {
      console.error("[Turnstile] Script failed to load");
      onError?.("Turnstile script failed to load");
    };
    
    // Set timeout for script loading
    const loadTimeout = setTimeout(() => {
      if (!window.turnstile) {
        console.error("[Turnstile] Script loading timeout");
        onError?.("Turnstile loading timeout");
      }
    }, 5000);
    
    document.head.appendChild(script);
    
    return () => clearTimeout(loadTimeout);
  }, [onError]);

  // 2. Renderizar widget quando pronto
  useEffect(() => {
    if (!siteKey || !containerRef.current) return;

    const render = () => {
      // Já renderizado? Não fazer nada
      if (widgetIdRef.current !== null) return;
      
      // Turnstile não pronto? Aguardar
      if (!window.turnstile) {
        pollCountRef.current++;
        if (pollCountRef.current > 100) {
          // Máximo 100 tentativas (10 segundos com 100ms cada)
          console.error("[Turnstile] Max poll attempts reached");
          if (onError) onError("Turnstile não carregou após tempo limite");
          return;
        }
        setTimeout(render, 100);
        return;
      }

      // Renderizar widget
      try {
        console.log("[Turnstile] Rendering widget with siteKey:", siteKey);
        widgetIdRef.current = window.turnstile.render(containerRef.current, {
          sitekey: siteKey,
          theme: theme,
          size: size,
          callback: (token) => {
            console.log("[Turnstile] Token received successfully");
            onTokenReceived?.(token);
          },
          "error-callback": () => {
            console.error("[Turnstile] Error callback triggered");
            onError?.("Erro na verificação do Turnstile");
          },
          "expired-callback": () => {
            console.warn("[Turnstile] Token expired");
            onError?.("Verificação do Turnstile expirou");
          },
          "timeout-callback": () => {
            console.error("[Turnstile] Timeout callback triggered");
            onError?.("Timeout na verificação do Turnstile");
          },
          "before-interactive-callback": () => {
            console.log("[Turnstile] Before interactive callback");
          },
          retry: "auto",
          "retry-interval": 5000,
          appearance: "interaction-only",
        });
        console.log("[Turnstile] Widget rendered successfully with ID:", widgetIdRef.current);
        pollCountRef.current = 0;
      } catch (err) {
        console.error("[Turnstile] Render failed:", err);
        onError?.("Falha ao renderizar widget Turnstile");
      }
    };

    render();

    return () => {
      // Cleanup
      if (widgetIdRef.current !== null && window.turnstile) {
        try {
          window.turnstile.remove(widgetIdRef.current);
          widgetIdRef.current = null;
          console.log("[Turnstile] Widget cleaned up");
        } catch (err) {
          console.warn("[Turnstile] Cleanup error:", err);
        }
      }
    };
  }, [siteKey, theme, size, onTokenReceived, onError]);

  if (!siteKey) return null;

  return (
    <div className={`flex justify-center ${className}`}>
      <div ref={containerRef} data-testid="turnstile-container" />
    </div>
  );
}
