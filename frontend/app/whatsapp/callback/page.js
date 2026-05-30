"use client";

import React, { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { AppShell } from "../../../components/shell";
import { motion } from "framer-motion";

export default function WhatsAppCallbackPage() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState("processing");
  const [error, setError] = useState("");

  useEffect(() => {
    const code = searchParams.get("code");
    const errorParam = searchParams.get("error");

    if (errorParam) {
      setStatus("error");
      setError("Autorização negada ou cancelada.");
      // Notifica a janela principal
      if (window.opener) {
        window.opener.postMessage({ type: "META_OAUTH_ERROR" }, "*");
      }
      return;
    }

    if (!code) {
      setStatus("error");
      setError("Código de autorização não recebido.");
      return;
    }

    // Notifica a janela principal com sucesso
    if (window.opener) {
      window.opener.postMessage({ type: "META_OAUTH_SUCCESS", code }, "*");
      setStatus("success");
      setTimeout(() => window.close(), 2000);
    } else {
      // Se abriu direto, redireciona para /whatsapp
      setStatus("redirecting");
      window.location.href = "/whatsapp";
    }
  }, [searchParams]);

  return (
    <AppShell>
      <div className="flex items-center justify-center min-h-[60vh]">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center max-w-md"
        >
          {status === "processing" && (
            <>
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#25D366] mx-auto mb-4" />
              <h2 className="text-lg font-semibold text-[#1a1c1e]">Conectando ao Meta...</h2>
              <p className="text-sm text-[#64748b] mt-2">Aguarde enquanto finalizamos a integração.</p>
            </>
          )}

          {status === "success" && (
            <>
              <div className="w-12 h-12 rounded-full bg-[#25D366]/10 flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-[#25D366]" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-[#1a1c1e]">Conectado com sucesso!</h2>
              <p className="text-sm text-[#64748b] mt-2">Esta janela fechará automaticamente.</p>
            </>
          )}

          {status === "redirecting" && (
            <>
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#25D366] mx-auto mb-4" />
              <h2 className="text-lg font-semibold text-[#1a1c1e]">Redirecionando...</h2>
            </>
          )}

          {status === "error" && (
            <>
              <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-red-500" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-[#1a1c1e]">Falha na conexão</h2>
              <p className="text-sm text-red-500 mt-2">{error}</p>
              <a href="/whatsapp" className="mt-4 inline-block text-sm text-[#25D366] hover:underline">
                Voltar para WhatsApp
              </a>
            </>
          )}
        </motion.div>
      </div>
    </AppShell>
  );
}
