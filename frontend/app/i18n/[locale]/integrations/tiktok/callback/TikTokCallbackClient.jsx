"use client";

import React, { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";

export default function TikTokCallbackClient({ locale }) {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState("processing");
  const [message, setMessage] = useState("Processando autorização do TikTok...");

  useEffect(() => {
    async function handleCallback() {
      try {
        const code = searchParams.get("code");
        const state = searchParams.get("state");

        // Validate state
        const storedState = localStorage.getItem("tiktok_oauth_state");
        if (state && storedState !== state) {
          throw new Error("Estado de segurança inválido");
        }

        if (!code) {
          setStatus("error");
          setMessage("Erro: Código de autorização não recebido");
          return;
        }

        const token = localStorage.getItem("syntexa_token");
        if (!token) {
          setStatus("error");
          setMessage("Erro: Sessão expirada. Faça login novamente.");
          return;
        }

        const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/v1/tiktok/oauth/callback`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ code, state }),
        });

        if (response.ok) {
          const data = await response.json();
          if (data.success) {
            setStatus("success");
            setMessage(`TikTok conectado com sucesso! Bem-vindo, ${data.user_name || 'Creator'}!`);
            localStorage.removeItem("tiktok_oauth_state");
            setTimeout(() => {
              window.location.href = `/i18n/${locale}/integrations`;
            }, 2500);
          } else {
            throw new Error(data.detail || "Falha ao conectar");
          }
        } else {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Erro ao conectar TikTok");
        }
      } catch (error) {
        setStatus("error");
        setMessage(`Erro: ${error.message}`);
      }
    }

    handleCallback();
  }, [searchParams, locale]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#fafbfc] via-white to-[#f5f6f8] flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        className="w-full max-w-md"
      >
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-[rgba(15,23,42,0.08)]">
          {status === "processing" && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center"
            >
              <div className="mb-6 flex justify-center">
                <div className="relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-[#000000] to-[#1a1a1a] rounded-full blur opacity-25 animate-pulse" />
                  <div className="relative bg-white rounded-full p-4">
                    <svg 
                      className="h-8 w-8 text-[#000000] animate-spin" 
                      viewBox="0 0 24 24" 
                      fill="none" 
                      stroke="currentColor" 
                      strokeWidth="2"
                    >
                      <circle cx="12" cy="12" r="10" opacity="0.3" />
                      <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round" />
                    </svg>
                  </div>
                </div>
              </div>
              <h2 className="text-xl font-semibold text-[#1a1c1e] mb-2">Conectando ao TikTok...</h2>
              <p className="text-[#64748b] text-sm">Aguarde enquanto finalizamos a integração</p>
              <div className="mt-4 flex justify-center gap-1">
                <div className="h-2 w-2 rounded-full bg-[#000000] animate-bounce" style={{ animationDelay: "0ms" }} />
                <div className="h-2 w-2 rounded-full bg-[#000000] animate-bounce" style={{ animationDelay: "150ms" }} />
                <div className="h-2 w-2 rounded-full bg-[#000000] animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </motion.div>
          )}

          {status === "success" && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="text-center"
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2, duration: 0.4, type: "spring", stiffness: 100 }}
                className="mb-6 flex justify-center"
              >
                <div className="relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-[#16a34a] to-[#22c55e] rounded-full blur opacity-30" />
                  <div className="relative bg-gradient-to-br from-[#dcfce7] to-[#bbf7d0] rounded-full p-4">
                    <svg className="h-8 w-8 text-[#16a34a]" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
                    </svg>
                  </div>
                </div>
              </motion.div>
              <h2 className="text-2xl font-bold text-[#16a34a] mb-2">Sucesso!</h2>
              <p className="text-[#1a1c1e] font-medium mb-1">{message}</p>
              <p className="text-sm text-[#64748b]">Redirecionando para integrações...</p>
              <div className="mt-6 w-full bg-gradient-to-r from-[#dcfce7] to-[#bbf7d0] rounded-lg p-3 border border-[#86efac]">
                <p className="text-sm text-[#166534] font-medium">✅ Sua conta TikTok está pronta para automação e análise!</p>
              </div>
            </motion.div>
          )}

          {status === "error" && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="text-center"
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2, duration: 0.4, type: "spring", stiffness: 100 }}
                className="mb-6 flex justify-center"
              >
                <div className="relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-[#ef4444] to-[#f87171] rounded-full blur opacity-30" />
                  <div className="relative bg-gradient-to-br from-[#fee2e2] to-[#fecaca] rounded-full p-4">
                    <svg className="h-8 w-8 text-[#dc2626]" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z" />
                    </svg>
                  </div>
                </div>
              </motion.div>
              <h2 className="text-2xl font-bold text-[#dc2626] mb-2">Erro na Conexão</h2>
              <p className="text-[#1a1c1e] font-medium mb-1">{message}</p>
              <p className="text-sm text-[#64748b] mb-6">Por favor, tente novamente ou entre em contato com o suporte.</p>
              
              <div className="space-y-3">
                <a
                  href={`/i18n/${locale}/integrations`}
                  className="block w-full bg-[#000000] text-white px-6 py-3 rounded-lg hover:bg-[#1a1a1a] transition-colors font-medium"
                >
                  Voltar para Integrações
                </a>
                <a
                  href={`/i18n/${locale}/fale-conosco`}
                  className="block w-full bg-[#f1f5f9] text-[#1a1c1e] px-6 py-3 rounded-lg hover:bg-[#e2e8f0] transition-colors font-medium border border-[#e2e8f0]"
                >
                  Contatar Suporte
                </a>
              </div>
            </motion.div>
          )}
        </div>

        {/* Footer Info */}
        <div className="mt-6 text-center">
          <p className="text-xs text-[#64748b]">
            Powered by SynTexaBR • Integração TikTok v1.0
          </p>
        </div>
      </motion.div>
    </div>
  );
}
