"use client";

import React, { useEffect, useRef } from "react";

/**
 * TurnstileWidget - Componente simples para Cloudflare Turnstile
 * Abordagem minimalista para evitar loops de re-render.
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
  const mountedRef = useRef(false);

  useEffect(() => {
    // Executar apenas uma vez quando montar
    if (mountedRef.current || !siteKey || typeof window === "undefined") {
      return;
    }

    mountedRef.current = true;

    const initTurnstile = async () => {
      try {
        // 1. Carregar script se não existe
        if (!window.turnstile) {
          const script = document.createElement("script");
          script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js";
          script.async = true;
          script.defer = true;
          script.crossOrigin = "anonymous";

          await new Promise((resolve, reject) => {
            script.onload = resolve;
            script.onerror = reject;
            (document.head || document.documentElement).appendChild(script);
          });
        }

        // 2. Aguardar window.turnstile estar disponível
        let retries = 0;
        while (!window.turnstile && retries < 20) {
          await new Promise(resolve => setTimeout(resolve, 100));
          retries++;
        }

        if (!window.turnstile) {
          throw new Error("Turnstile não carregou");
        }

        // 3. Renderizar widget
        if (containerRef.current && !widgetIdRef.current) {
          widgetIdRef.current = window.turnstile.render(containerRef.current, {
            sitekey: siteKey,
            theme: theme,
            size: size,
            callback: (token) => {
              if (onTokenReceived) onTokenReceived(token);
            },
            "error-callback": (errorCode) => {
              console.warn("[Turnstile] Error:", errorCode);
              if (onError) onError(`Código ${errorCode}`);
            },
            "expired-callback": () => {
              if (onError) onError("Verificação expirou");
            },
            "timeout-callback": () => {
              if (onError) onError("Timeout");
            },
            retry: "auto",
            "retry-interval": 5000,
            appearance: "interaction-only",
          });
        }
      } catch (err) {
        console.error("[Turnstile] Error during initialization:", err);
        if (onError) onError(err.message || "Falha ao carregar Turnstile");
      }
    };

    initTurnstile();

    // Cleanup
    return () => {
      try {
        if (widgetIdRef.current && window.turnstile) {
          window.turnstile.remove(widgetIdRef.current);
          widgetIdRef.current = null;
        }
      } catch (err) {
        console.warn("[Turnstile] Error during cleanup:", err);
      }
    };
  }, []); // Dependências vazias: executar apenas uma vez

  if (!siteKey) {
    return null;
  }

  return (
    <div className={`flex justify-center ${className}`}>
      <div ref={containerRef} />
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
