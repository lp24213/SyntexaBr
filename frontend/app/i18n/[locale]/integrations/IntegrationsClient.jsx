"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { t } from "../../../../lib/i18n";
import { useLanguage } from "../../../../components/language-provider";

export default function IntegrationsClient() {
  const { locale } = useLanguage();
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("whatsapp");

  useEffect(() => {
    checkConnection();
  }, []);

  async function checkConnection() {
    try {
      const token = localStorage.getItem("syntexa_token");
      const res = await fetch(`${process.env.NEXT_PUBLIC_WHATSAPP_API}/companies`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setConnected(data.length > 0);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

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

        <div className="flex gap-4 mb-8 border-b border-[rgba(15,23,42,0.08)]">
          {[
            { key: "whatsapp", labelKey: "whatsappPageTitle", color: "#25D366" },
            { key: "instagram", labelKey: "instagramPageTitle", color: "#E4405F" },
            { key: "facebook", labelKey: "facebookPageTitle", color: "#1877F2" },
            { key: "tiktok", labelKey: "tiktokPageTitle", color: "#000000" },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === tab.key
                  ? "border-b-2"
                  : "text-[#64748b] hover:text-[#1a1c1e]"
              }`}
              style={activeTab === tab.key ? { color: tab.color, borderColor: tab.color } : {}}
            >
              {t(tab.labelKey, locale)}
            </button>
          ))}
        </div>

        <div className="bg-white rounded-lg border border-[rgba(15,23,42,0.08)] p-6">
          {activeTab === "whatsapp" && (
            <div>
              <h2 className="text-lg font-semibold mb-4">{t('whatsappPageTitle', locale)}</h2>
              <p className="text-[#64748b] mb-4">
                {t('whatsappDescription', locale)}
              </p>
              {connected ? (
                <div className="bg-[#f0fdf4] border border-[#86efac] rounded-lg p-4">
                  <p className="text-[#166534] font-medium flex items-center gap-2">
                    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
                    </svg>
                    {t('connectedSuccess', locale)}
                  </p>
                </div>
              ) : (
                <button className="bg-[#25D366] text-white px-6 py-2 rounded-lg hover:bg-[#20ba58] transition-colors">
                  {t('connectWhatsApp', locale)}
                </button>
              )}
            </div>
          )}

          {activeTab === "instagram" && (
            <div>
              <h2 className="text-lg font-semibold mb-4">{t('integrations', locale)} - Instagram</h2>
              <p className="text-[#64748b] mb-4">
                {t('instagramDescription', locale)}
              </p>
              <button className="bg-[#E4405F] text-white px-6 py-2 rounded-lg hover:bg-[#d63447] transition-colors">
                {t('connectInstagram', locale)}
              </button>
            </div>
          )}

          {activeTab === "facebook" && (
            <div>
              <h2 className="text-lg font-semibold mb-4">{t('integrations', locale)} - Facebook</h2>
              <p className="text-[#64748b] mb-4">
                {t('facebookDescription', locale)}
              </p>
              <button className="bg-[#1877F2] text-white px-6 py-2 rounded-lg hover:bg-[#166fe5] transition-colors">
                {t('connectFacebook', locale)}
              </button>
            </div>
          )}

          {activeTab === "tiktok" && (
            <div>
              <h2 className="text-lg font-semibold mb-4">{t('integrations', locale)} - TikTok</h2>
              <p className="text-[#64748b] mb-4">
                {t('tiktokDescription', locale)}
              </p>
              <div className="bg-[#f9f9f9] border border-[rgba(15,23,42,0.08)] rounded-lg p-4 mb-4">
                <p className="text-sm text-[#64748b] mb-2">
                  <strong>{t('oauthRedirectUrl', locale)}</strong>
                </p>
                <code className="bg-white border border-[rgba(15,23,42,0.08)] rounded px-3 py-2 text-sm block overflow-x-auto">
                  https://syntexabr.com.br/i18n/{locale}/integrations/tiktok/callback
                </code>
              </div>
              <div className="bg-[#f9f9f9] border border-[rgba(15,23,42,0.08)] rounded-lg p-4 mb-4">
                <p className="text-sm text-[#64748b] mb-1"><strong>{t('supportedLocales', locale)}</strong></p>
                {["pt-BR", "en-US", "es-ES", "zh-CN"].map((l) => (
                  <code key={l} className="bg-white border border-[rgba(15,23,42,0.08)] rounded px-3 py-1 text-xs block overflow-x-auto mb-1">
                    https://syntexabr.com.br/i18n/{l}/integrations/tiktok/callback
                  </code>
                ))}
              </div>
              <a
                href={`https://business-api.tiktok.com/portal/auth?app_id=YOUR_APP_ID&redirect_uri=https%3A%2F%2Fsyntexabr.com.br%2Fi18n%2F${locale}%2Fintegrations%2Ftiktok%2Fcallback&response_type=code`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 bg-[#000000] text-white px-6 py-2 rounded-lg hover:bg-[#1a1a1a] transition-colors"
              >
                <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor" aria-hidden="true">
                  <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1V9.01a6.33 6.33 0 00-.79-.05 6.34 6.34 0 00-6.34 6.34 6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.33-6.34V8.69a8.18 8.18 0 004.79 1.54V6.79a4.85 4.85 0 01-1.02-.1z"/>
                </svg>
                {t('connectTikTok', locale)}
              </a>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}
