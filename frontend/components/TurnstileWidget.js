"use client";

import React, { useEffect, useRef } from "react";

/**
 * TurnstileWidget - MINIMAL SEM LOOPS
 * O script é global e persistente. Uma única instância basta.
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

  // ─ Carregar script GLOBAL (uma única vez por aplicação)
  useEffect(() => {
    if (typeof window === "undefined") return;

    // Se script já existe globalmente, não fazer nada
    if (window.turnstileLoaded) {
      return;
    }

    const script = document.createElement("script");
    script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js";
    script.async = true;
    script.defer = true;
    script.crossOrigin = "anonymous";

    script.onload = () => {
      window.turnstileLoaded = true;
    };

    script.onerror = () => {
      console.error("[Turnstile] Failed to load script");
    };

    document.head.appendChild(script);
  }, []); // Executar apenas uma vez

  // ─ Renderizar widget quando estiver pronto
  useEffect(() => {
    if (!siteKey || !containerRef.current || typeof window === "undefined") {
      return;
    }

    // Se window.turnstile ainda não existe, aguardar um pouco
    if (!window.turnstile) {
      const timeout = setTimeout(() => {
        if (window.turnstile && containerRef.current && !widgetIdRef.current) {
          try {
            widgetIdRef.current = window.turnstile.render(containerRef.current, {
              sitekey: siteKey,
              theme: theme,
              size: size,
              callback: (token) => {
                if (onTokenReceived) onTokenReceived(token);
              },
              "error-callback": () => {
                if (onError) onError("Erro na verificação");
              },
              "expired-callback": () => {
                if (onError) onError("Expirou");
              },
              "timeout-callback": () => {
                if (onError) onError("Timeout");
              },
              retry: "auto",
              "retry-interval": 5000,
              appearance: "interaction-only",
            });
          } catch (err) {
            console.error("[Turnstile] Render error:", err);
          }
        }
      }, 500);

      return () => clearTimeout(timeout);
    }

    // window.turnstile já existe, renderizar imediatamente
    try {
      if (!widgetIdRef.current) {
        widgetIdRef.current = window.turnstile.render(containerRef.current, {
          sitekey: siteKey,
          theme: theme,
          size: size,
          callback: (token) => {
            if (onTokenReceived) onTokenReceived(token);
          },
          "error-callback": () => {
            if (onError) onError("Erro na verificação");
          },
          "expired-callback": () => {
            if (onError) onError("Expirou");
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
      console.error("[Turnstile] Render error:", err);
    }

    return () => {
      // Cleanup: remover widget quando componente desmontar
      try {
        if (widgetIdRef.current && window.turnstile) {
          window.turnstile.remove(widgetIdRef.current);
          widgetIdRef.current = null;
        }
      } catch (err) {
        // Ignorar erros de cleanup
      }
    };
  }, [siteKey]); // Só depender de siteKey

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
