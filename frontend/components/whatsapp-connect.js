"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Button } from "./ui/button";

export function WhatsAppConnect({ onConnect }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    // Carrega script do Meta Embedded Signup
    if (document.getElementById("meta-embedded-signup")) return;
    const script = document.createElement("script");
    script.id = "meta-embedded-signup";
    script.src = "https://connect.facebook.net/en_US/sdk.js";
    script.async = true;
    script.defer = true;
    script.crossOrigin = "anonymous";
    document.body.appendChild(script);

    window.fbAsyncInit = function () {
      window.FB.init({
        appId: "1739539750737158",
        autoLogAppEvents: true,
        xfbml: true,
        version: "v18.0",
      });
    };
  }, []);

  async function launchMetaSignup() {
    setLoading(true);
    setError("");
    try {
      // Abre popup de autorização Meta
      const clientId = "1739539750737158";
      const redirectUri = `${window.location.origin}/whatsapp/callback`;
      const scope = "whatsapp_business_management,business_management";
      const authUrl = `https://www.facebook.com/v18.0/dialog/oauth?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=${encodeURIComponent(scope)}&response_type=code`;

      const popup = window.open(authUrl, "meta_oauth", "width=600,height=700");

      // Escuta a mensagem do callback
      const handleMessage = async (event) => {
        if (event.data?.type === "META_OAUTH_SUCCESS") {
          window.removeEventListener("message", handleMessage);
          const { code } = event.data;
          // Envia para o backend trocar o code por token
          const token = localStorage.getItem("syntexa_token");
          const res = await fetch(`${process.env.NEXT_PUBLIC_WHATSAPP_API}/auth/meta/callback`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ code, redirectUri }),
          });
          if (!res.ok) throw new Error("Falha na integração");
          onConnect();
        }
        if (event.data?.type === "META_OAUTH_ERROR") {
          window.removeEventListener("message", handleMessage);
          setError("Autorização cancelada ou negada.");
        }
      };
      window.addEventListener("message", handleMessage);

      // Timeout de 5 minutos
      setTimeout(() => {
        window.removeEventListener("message", handleMessage);
        if (popup && !popup.closed) popup.close();
        setLoading(false);
      }, 300000);
    } catch (e) {
      setError(e.message);
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="syntexa-card rounded-2xl border border-[rgba(15,23,42,0.06)] bg-white p-8 text-center"
      >
        <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#25D366]/10">
          <svg className="h-7 w-7 text-[#25D366]" viewBox="0 0 24 24" fill="currentColor">
            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.004 5.45-4.439 9.884-9.887 9.884m8.413-18.3A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z" />
          </svg>
        </div>

        <h2 className="text-xl font-semibold text-[#0f172a]">
          Conecte seu WhatsApp Business
        </h2>
        <p className="mt-2 text-sm text-[#64748b] leading-relaxed">
          Automatize atendimento, respostas e operações com IA integrada ao WhatsApp Business.
        </p>

        <div className="mt-6 space-y-3">
          <Button
            onClick={launchMetaSignup}
            disabled={loading}
            variant="primary"
            className="w-full"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Conectando...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2.163c3.204 0 3.584.012 4.85.072 3.252.148 4.771 1.691 4.919 4.919.06 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.072 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
                </svg>
                Continuar com Meta
              </span>
            )}
          </Button>
        </div>

        {error && (
          <p className="mt-4 text-sm text-red-500">{error}</p>
        )}

        <p className="mt-4 text-xs text-[#94a3b8]">
          Ao conectar, você autoriza a Syntexa a gerenciar seu WhatsApp Business API em seu nome.
        </p>
      </motion.div>
    </div>
  );
}
