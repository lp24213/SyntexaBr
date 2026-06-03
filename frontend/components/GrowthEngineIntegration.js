"use client";

/**
 * Growth Engine Frontend Integration
 * Conecta o Growth Engine com a UI React
 */

import React, { useEffect, useRef, useState } from "react";
import GrowthEngine from "../../../growth-engine/index.js";
import { t } from "../lib/i18n";
import { useLanguage } from "./language-provider";

/**
 * Hook para usar Growth Engine
 */
export function useGrowthEngine(config = {}) {
  const engineRef = useRef(null);
  const [ready, setReady] = useState(false);
  const [status, setStatus] = useState(null);
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    const initEngine = async () => {
      try {
        engineRef.current = new GrowthEngine(config);
        const status = await engineRef.current.initialize();
        setStatus(status);
        setReady(true);

        // Atualizar métricas a cada 30 segundos
        const interval = setInterval(() => {
          const dashboard = engineRef.current.getDashboard();
          setMetrics(dashboard);
        }, 30000);

        return () => clearInterval(interval);
      } catch (err) {
        console.error("Erro ao inicializar Growth Engine:", err);
      }
    };

    initEngine();
  }, []);

  return {
    engine: engineRef.current,
    ready,
    status,
    metrics,
  };
}

/**
 * Componente de Popup Inteligente
 */
export function SmartPopup({ config, onLeadCaptured }) {
  const [visible, setVisible] = useState(false);
  const [formData, setFormData] = useState({});
  const popupRef = useRef(null);

  useEffect(() => {
    if (!config) return;

    const trigger = config.trigger || {};

    const handleScrollTrigger = () => {
      if (trigger.event === "scroll") {
        const scrollPercent = (window.scrollY / document.documentElement.scrollHeight) * 100;
        if (scrollPercent >= trigger.value) {
          setVisible(true);
          document.removeEventListener("scroll", handleScrollTrigger);
        }
      }
    };

    const handleExitIntent = (e) => {
      if (trigger.event === "exit-intent" && e.clientY <= 0) {
        setVisible(true);
        document.removeEventListener("mouseleave", handleExitIntent);
      }
    };

    if (trigger.event === "scroll") {
      document.addEventListener("scroll", handleScrollTrigger);
      return () => document.removeEventListener("scroll", handleScrollTrigger);
    }

    if (trigger.event === "exit-intent") {
      document.addEventListener("mouseleave", handleExitIntent);
      return () => document.removeEventListener("mouseleave", handleExitIntent);
    }

    if (trigger.event === "time") {
      const timeout = setTimeout(() => setVisible(true), trigger.delay || 5000);
      return () => clearTimeout(timeout);
    }
  }, [config]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (onLeadCaptured) {
      onLeadCaptured(formData);
    }
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div
        ref={popupRef}
        className="relative bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 overflow-hidden animate-in fade-in zoom-in"
      >
        {/* Close button */}
        <button
          onClick={() => setVisible(false)}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 z-10"
        >
          ✕
        </button>

        {/* Content */}
        <div className="p-8">
          {config.image && (
            <img
              src={config.image}
              alt={config.headline}
              className="w-full h-48 object-cover rounded-lg mb-6"
            />
          )}

          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            {config.headline}
          </h2>
          <p className="text-gray-600 mb-6">{config.subheadline}</p>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {config.fields?.map((field) => (
              <div key={field.name}>
                <input
                  type={field.type}
                  name={field.name}
                  placeholder={field.placeholder}
                  required={field.required}
                  onChange={(e) =>
                    setFormData({ ...formData, [field.name]: e.target.value })
                  }
                  className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            ))}

            <button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition"
            >
              {config.cta || "Enviar"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

/**
 * Componente de Dashboard de Growth
 */
export function GrowthDashboard({ engine }) {
  const { locale } = useLanguage();
  const [dashboard, setDashboard] = useState(null);

  useEffect(() => {
    if (!engine) return;
    const dash = engine.getDashboard();
    setDashboard(dash);

    // Atualizar a cada 1 minuto
    const interval = setInterval(() => {
      setDashboard(engine.getDashboard());
    }, 60000);

    return () => clearInterval(interval);
  }, [engine]);

  if (!dashboard) return <div className="p-4">{t("loadingDashboard", locale)}</div>;

  return (
    <div className="p-8 bg-gradient-to-br from-gray-50 to-gray-100 min-h-screen">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            {dashboard.header.title}
          </h1>
          <p className="text-gray-600">
            Última atualização: {new Date(dashboard.header.lastUpdated).toLocaleTimeString()}
          </p>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: "Leads Totais", value: dashboard.overview.totalLeads, icon: "👥" },
            { label: "Leads Quentes", value: dashboard.overview.hotLeads, icon: "🔥" },
            { label: "Taxa Conversão", value: dashboard.overview.conversionRate, icon: "📈" },
            { label: "Automações", value: dashboard.overview.activeAutomations, icon: "⚙️" },
          ].map((kpi) => (
            <div
              key={kpi.label}
              className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500"
            >
              <p className="text-gray-600 text-sm">{kpi.label}</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {kpi.icon} {kpi.value}
              </p>
            </div>
          ))}
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {[
            { title: "Trend de Leads", value: dashboard.charts.leadTrend },
            { title: "Engajamento", value: dashboard.charts.engagementTrend },
            { title: "Conversão", value: dashboard.charts.conversionTrend },
          ].map((chart) => (
            <div key={chart.title} className="bg-white rounded-lg shadow p-6">
              <h3 className="font-semibold text-gray-900 mb-4">{chart.title}</h3>
              <p className="text-2xl font-bold text-green-600">{chart.value}</p>
            </div>
          ))}
        </div>

        {/* Alerts */}
        {dashboard.alerts.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-8">
            <h3 className="font-semibold text-yellow-900 mb-3">{t("alerts", locale)}</h3>
            <ul className="space-y-2">
              {dashboard.alerts.map((alert) => (
                <li key={alert} className="text-yellow-800">
                  {alert}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Best Performers */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-4">{t("topPerformers", locale)}</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-gray-600">{t("bestSegment", locale)}</p>
              <p className="text-xl font-bold text-gray-900">
                {dashboard.bestPerformers.topSegment}
              </p>
            </div>
            <div>
              <p className="text-gray-600">{t("bestSource", locale)}</p>
              <p className="text-xl font-bold text-gray-900">
                {dashboard.bestPerformers.topSource}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Componente de Analytics de Leads
 */
export function LeadsAnalytics({ engine }) {
  const { locale } = useLanguage();
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    if (!engine) return;
    setAnalytics(engine.leads.getLeadAnalytics());
  }, [engine]);

  if (!analytics) return <div>{t("loading", locale)}</div>;

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-6">{t("leadsAnalysis", locale)}</h2>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg">
          <p className="text-gray-600 text-sm">{t("totalLeads", locale)}</p>
          <p className="text-3xl font-bold text-blue-600">{analytics.totalLeads}</p>
        </div>
        <div className="bg-red-50 p-4 rounded-lg">
          <p className="text-gray-600 text-sm">{t("hotLeads", locale)}</p>
          <p className="text-3xl font-bold text-red-600">{analytics.byScore.hot}</p>
        </div>
        <div className="bg-yellow-50 p-4 rounded-lg">
          <p className="text-gray-600 text-sm">{t("warmLeads", locale)}</p>
          <p className="text-3xl font-bold text-yellow-600">{analytics.byScore.warm}</p>
        </div>
        <div className="bg-blue-50 p-4 rounded-lg">
          <p className="text-gray-600 text-sm">{t("coldLeads", locale)}</p>
          <p className="text-3xl font-bold text-blue-400">{analytics.byScore.cold}</p>
        </div>
      </div>

      {/* Segments */}
      <div className="mt-8">
        <h3 className="text-lg font-bold mb-4">{t("bySegment", locale)}</h3>
        <div className="space-y-2">
          {Object.entries(analytics.bySegment).map(([segment, count]) => (
            <div key={segment} className="flex justify-between items-center bg-white p-3 rounded border">
              <span className="capitalize">{segment}</span>
              <span className="font-bold text-gray-900">{count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default {
  useGrowthEngine,
  SmartPopup,
  GrowthDashboard,
  LeadsAnalytics,
};
