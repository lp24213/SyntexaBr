"use client";

import React, { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

export default function TikTokCallbackClient({ locale }) {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState("processing");
  const [message, setMessage] = useState("Processando autorização do TikTok...");

  useEffect(() => {
    async function handleCallback() {
      try {
        const code = searchParams.get("code");
        const state = searchParams.get("state");

        if (!code) {
          setStatus("error");
          setMessage("Erro: Código de autorização não recebido");
          return;
        }

        const token = localStorage.getItem("syntexa_token");
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/v1/integrations/tiktok/callback`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ code, state }),
        });

        if (response.ok) {
          setStatus("success");
          setMessage("TikTok conectado com sucesso!");
          setTimeout(() => {
            window.location.href = `/i18n/${locale}/integrations`;
          }, 2000);
        } else {
          setStatus("error");
          setMessage("Erro ao conectar TikTok. Tente novamente.");
        }
      } catch (error) {
        setStatus("error");
        setMessage(`Erro: ${error.message}`);
      }
    }

    handleCallback();
  }, [searchParams, locale]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-[#fafbfc] to-[#f5f6f8]">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
        {status === "processing" && (
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#000000] mx-auto mb-4" />
            <p className="text-[#64748b]">{message}</p>
          </div>
        )}

        {status === "success" && (
          <div className="text-center">
            <svg className="h-12 w-12 text-[#16a34a] mx-auto mb-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
            </svg>
            <h2 className="text-xl font-semibold text-[#1a1c1e] mb-2">Sucesso!</h2>
            <p className="text-[#64748b]">{message}</p>
            <p className="text-sm text-[#64748b] mt-4">Redirecionando...</p>
          </div>
        )}

        {status === "error" && (
          <div className="text-center">
            <svg className="h-12 w-12 text-[#dc2626] mx-auto mb-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z" />
            </svg>
            <h2 className="text-xl font-semibold text-[#dc2626] mb-2">Erro</h2>
            <p className="text-[#64748b] mb-4">{message}</p>
            <a
              href={`/i18n/${locale}/integrations`}
              className="inline-block bg-[#000000] text-white px-6 py-2 rounded-lg hover:bg-[#1a1a1a] transition-colors"
            >
              Voltar para Integrações
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
