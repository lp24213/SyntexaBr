"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { t } from "../../../../lib/i18n";
import { useLanguage } from "../../../../components/language-provider";

export default function IntegrationsClient() {
  const { locale } = useLanguage();
  const [connected, setConnected] = useState(false);
  const [tiktokConnected, setTikTokConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("whatsapp");
  const [connectingWhatsApp, setConnectingWhatsApp] = useState(false);
  const [connectingTikTok, setConnectingTikTok] = useState(false);

  useEffect(() => {
    checkConnection();
  }, []);

  async function checkConnection() {
    try {
      const token = localStorage.getItem("syntexa_token");
      
      // Check WhatsApp
      const resWA = await fetch(`${process.env.NEXT_PUBLIC_WHATSAPP_API}/status`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resWA.ok) {
        const data = await resWA.json();
        setConnected(data.configured || false);
      }

      // Check TikTok
      const resTT = await fetch(`${process.env.NEXT_PUBLIC_TIKTOK_API}/status`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resTT.ok) {
        const data = await resTT.json();
        setTikTokConnected(data.configured || false);
      }
    } catch (e) {
      console.error("Failed to check integrations:", e);
    } finally {
      setLoading(false);
    }
  }

  // ✅ Handler para conectar ao WhatsApp
  const handleConnectWhatsApp = (e) => {
    e.preventDefault();
    setConnectingWhatsApp(true);

    const clientId = "1739539750737158";
    const redirectUri = `${window.location.origin}/whatsapp/callback`;
    const scope = "whatsapp_business_management,business_management";
    const authUrl = `https://www.facebook.com/v18.0/dialog/oauth?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=${encodeURIComponent(scope)}&response_type=code`;

    const popup = window.open(authUrl, "whatsapp_oauth", "width=600,height=700");

    const handleMessage = async (event) => {
      if (event.data?.type === "META_OAUTH_SUCCESS") {
        window.removeEventListener("message", handleMessage);
        const { code } = event.data;

        try {
          const token = localStorage.getItem("syntexa_token");
          const response = await fetch(`${process.env.NEXT_PUBLIC_WHATSAPP_API}/oauth/callback`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${token}`,
            },
            body: JSON.stringify({ code, locale }),
          });

          if (response.ok) {
            const data = await response.json();
            if (data.success) {
              setConnected(true);
              alert(`✅ WhatsApp conectado! Número: ${data.display_number}`);
              await checkConnection();
            }
          } else {
            throw new Error("Falha ao conectar");
          }
        } catch (err) {
          alert(`❌ Erro ao conectar: ${err.message}`);
          console.error("WhatsApp connection error:", err);
        } finally {
          setConnectingWhatsApp(false);
        }
      } else if (event.data?.type === "META_OAUTH_ERROR") {
        window.removeEventListener("message", handleMessage);
        setConnectingWhatsApp(false);
        alert("❌ Autorização negada ou cancelada");
      }
    };

    window.addEventListener("message", handleMessage);
  };

  // ✅ Handler para conectar ao TikTok
  const handleConnectTikTok = (e) => {
    e.preventDefault();
    setConnectingTikTok(true);

    const clientId = "7649256601374687233";
    const redirectUri = `${window.location.origin}/i18n/${locale}/integrations/tiktok/callback`;
    const scope = [
      "user.info.basic",
      "user.info.profile",
      "user.account.type",
      "user.insights",
      "video.list",
      "video.insights",
      "comment.list",
      "comment.list.manage",
      "video.publish",
      "video.upload"
    ].join(",");

    const state = Math.random().toString(36).substring(7);
    localStorage.setItem("tiktok_oauth_state", state);

    const authUrl = `https://www.tiktok.com/v2/auth/authorize?` +
      `client_key=${clientId}&` +
      `scope=${encodeURIComponent(scope)}&` +
      `response_type=code&` +
      `redirect_uri=${encodeURIComponent(redirectUri)}&` +
      `state=${state}`;

    const popup = window.open(authUrl, "tiktok_oauth", "width=600,height=700");

    // Monitor popup window for completion
    const checkPopup = setInterval(() => {
      if (popup?.closed) {
        clearInterval(checkPopup);
        setConnectingTikTok(false);
        // Recheck connection status after popup closes
        setTimeout(() => checkConnection(), 1000);
      }
    }, 500);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#25D366]" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-[#1a1c1e] mb-2">{t('integrations', locale)}</h1>
          <p className="text-[#64748b] text-sm">
            {t('integrationsDescription', locale)}
          </p>
        </div>

        <div className="flex gap-4 mb-8 border-b border-[rgba(15,23,42,0.08)] overflow-x-auto pb-2">
          {[
            { key: "whatsapp", labelKey: "whatsappPageTitle", color: "#25D366", icon: "whatsapp" },
            { key: "instagram", labelKey: "instagramPageTitle", color: "#E4405F", icon: "instagram" },
            { key: "facebook", labelKey: "facebookPageTitle", color: "#1877F2", icon: "facebook" },
            { key: "tiktok", labelKey: "tiktokPageTitle", color: "#000000", icon: "tiktok" },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 font-medium transition-colors inline-flex items-center gap-2 whitespace-nowrap ${
                activeTab === tab.key
                  ? "border-b-2"
                  : "text-[#64748b] hover:text-[#1a1c1e]"
              }`}
              style={activeTab === tab.key ? { color: tab.color, borderColor: tab.color } : {}}
            >
              {getIconSVG(tab.icon)}
              {t(tab.labelKey, locale)}
            </button>
          ))}
        </div>

        <div className="bg-white rounded-lg border border-[rgba(15,23,42,0.08)] p-6">
          {activeTab === "whatsapp" && (
            <div>
              <div className="flex items-center gap-3 mb-4">
                <h2 className="text-lg font-semibold">{t('whatsappPageTitle', locale)}</h2>
                {connected && (
                  <span className="text-xs font-semibold uppercase tracking-wide bg-[#dcfce7] text-[#166534] rounded-full px-3 py-1">
                    ✅ Conectado
                  </span>
                )}
              </div>
              <p className="text-[#64748b] mb-6">
                {t('whatsappDescription', locale)}
              </p>
              {connected ? (
                <div className="bg-[#f0fdf4] border border-[#86efac] rounded-lg p-4 flex items-center gap-3">
                  <svg className="h-5 w-5 text-[#16a34a]" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
                  </svg>
                  <p className="text-[#166534] font-medium">{t('connectedSuccess', locale) || 'Conectado com sucesso!'}</p>
                </div>
              ) : (
                <button 
                  onClick={handleConnectWhatsApp}
                  disabled={connectingWhatsApp}
                  className="bg-[#25D366] text-white px-8 py-3 rounded-lg hover:bg-[#20ba58] transition-colors disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-2 font-medium"
                >
                  {connectingWhatsApp ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                      Conectando...
                    </>
                  ) : (
                    <>
                      {getIconSVG("whatsapp", "w-5 h-5")}
                      {t('connectWhatsApp', locale)}
                    </>
                  )}
                </button>
              )}
            </div>
          )}

          {activeTab === "instagram" && (
            <div>
              <h2 className="text-lg font-semibold mb-4">{t('integrations', locale)} - Instagram</h2>
              <p className="text-[#64748b] mb-6">
                {t('instagramDescription', locale)}
              </p>
              <button className="bg-[#E4405F] text-white px-8 py-3 rounded-lg hover:bg-[#d63447] transition-colors inline-flex items-center gap-2 font-medium">
                {getIconSVG("instagram", "w-5 h-5")}
                {t('connectInstagram', locale)}
              </button>
            </div>
          )}

          {activeTab === "facebook" && (
            <div>
              <h2 className="text-lg font-semibold mb-4">{t('integrations', locale)} - Facebook</h2>
              <p className="text-[#64748b] mb-6">
                {t('facebookDescription', locale)}
              </p>
              <button className="bg-[#1877F2] text-white px-8 py-3 rounded-lg hover:bg-[#166fe5] transition-colors inline-flex items-center gap-2 font-medium">
                {getIconSVG("facebook", "w-5 h-5")}
                {t('connectFacebook', locale)}
              </button>
            </div>
          )}

          {activeTab === "tiktok" && (
            <div>
              <div className="flex items-center gap-3 mb-4">
                <h2 className="text-lg font-semibold">{t('tiktokPageTitle', locale)}</h2>
                {tiktokConnected && (
                  <span className="text-xs font-semibold uppercase tracking-wide bg-[#dcfce7] text-[#166534] rounded-full px-3 py-1">
                    ✅ Conectado
                  </span>
                )}
              </div>
              <p className="text-[#64748b] mb-6">
                {t('tiktokDescription', locale) || 'Integre seu TikTok Business para análise, automação de conteúdo e gerenciamento de campanhas.'}
              </p>
              {tiktokConnected ? (
                <div className="bg-[#f0fdf4] border border-[#86efac] rounded-lg p-4 flex items-center gap-3">
                  <svg className="h-5 w-5 text-[#16a34a]" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
                  </svg>
                  <p className="text-[#166534] font-medium">Conectado com sucesso!</p>
                </div>
              ) : (
                <button 
                  onClick={handleConnectTikTok}
                  disabled={connectingTikTok}
                  className="bg-[#000000] text-white px-8 py-3 rounded-lg hover:bg-[#1a1a1a] transition-colors disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-2 font-medium"
                >
                  {connectingTikTok ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                      Conectando...
                    </>
                  ) : (
                    <>
                      {getIconSVG("tiktok", "w-5 h-5")}
                      {t('connectTikTok', locale)}
                    </>
                  )}
                </button>
              )}

              {!tiktokConnected && (
                <div className="mt-8 pt-8 border-t border-[rgba(15,23,42,0.08)]">
                  <h3 className="font-semibold text-[#1a1c1e] mb-4">Recursos disponíveis:</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[
                      { title: "Análise de Vídeos", desc: "Acompanhe performance de seus vídeos" },
                      { title: "Gerenciamento de Campanhas", desc: "Crie e gerencie anúncios do TikTok" },
                      { title: "Insights da Conta", desc: "Dados detalhados de crescimento" },
                      { title: "Automação de Conteúdo", desc: "Automatize postagens e respostas" },
                    ].map((feature, idx) => (
                      <div key={idx} className="bg-[#f9f9f9] p-4 rounded-lg">
                        <p className="font-medium text-[#1a1c1e]">{feature.title}</p>
                        <p className="text-sm text-[#64748b]">{feature.desc}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}

// ✅ SVG Icons
function getIconSVG(platform, className = "w-4 h-4") {
  switch (platform) {
    case "whatsapp":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="currentColor">
          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.67-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421-7.403h-.004a9.87 9.87 0 00-5.031 1.378c-3.055 2.346-3.797 6.511-1.644 9.82 1.007 1.6 2.404 2.806 4.042 3.6 1.631.783 3.647.945 5.653.26l.007-.002a10.012 10.012 0 006.7-3.91c2.341-2.87 2.951-7.46.514-10.793-2.426-3.356-7.254-4.466-11.234-2.353M12.25 1.297C6.374 1.297 1.75 5.921 1.75 11.798c0 2.193.618 4.328 1.78 6.14L1.98 22.644l6.94-1.665c1.712.914 3.647 1.403 5.63 1.403 5.877 0 10.5-4.624 10.5-10.501C22.75 5.921 18.127 1.297 12.25 1.297z"/>
        </svg>
      );
    case "tiktok":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="currentColor">
          <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1V9.01a6.33 6.33 0 00-.79-.05 6.34 6.34 0 00-6.34 6.34 6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.33-6.34V8.69a8.18 8.18 0 004.79 1.54V6.79a4.85 4.85 0 01-1.02-.1z"/>
        </svg>
      );
    case "instagram":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zM5.838 12a6.162 6.162 0 1 1 12.324 0 6.162 6.162 0 0 1-12.324 0zM12 16a4 4 0 1 1 0-8 4 4 0 0 1 0 8zm4.965-10.322a1.44 1.44 0 1 1 2.881.001 1.44 1.44 0 0 1-2.881-.001z"/>
        </svg>
      );
    case "facebook":
      return (
        <svg className={className} viewBox="0 0 24 24" fill="currentColor">
          <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
        </svg>
      );
    default:
      return null;
  }
}
