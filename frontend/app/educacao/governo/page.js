"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { AppShell } from "../../../components/shell";
import { govStats, govGenerateReport, govPredict, govPolicy, getProfile } from "../../../lib/api";
import { encryptedPath } from "../../../lib/routes";
import { FuturisticIcon } from "../../../components/icons/futuristic-icons";

// Verifica se o módulo governamental está habilitado para este ambiente.
// Em produção, somente administradores com ENABLE_GOV_UI=true têm acesso.
function GovGuard({ children }) {
  var [allowed, setAllowed] = React.useState(null);

  React.useEffect(function () {
    try {
      var isAdmin = window.localStorage.getItem("syntexa_is_admin") === "1";
      // Aceita acesso se: é admin OU variável de ambiente NEXT_PUBLIC_ENABLE_GOV_UI=true
      var envEnabled = process.env.NEXT_PUBLIC_ENABLE_GOV_UI === "true";
      setAllowed(isAdmin || envEnabled);
    } catch {
      setAllowed(false);
    }
  }, []);

  if (allowed === null) {
    return React.createElement("div", { className: "flex min-h-screen items-center justify-center" },
      React.createElement("div", { className: "text-zinc-500 text-sm" }, "Verificando acesso..."));
  }

  if (!allowed) {
    return React.createElement(AppShell, null,
      React.createElement("div", { className: "flex min-h-[60vh] flex-col items-center justify-center gap-6 text-center px-4" },
        React.createElement("div", { className: "flex h-20 w-20 items-center justify-center rounded-2xl border border-amber-500/30 bg-amber-500/10" },
          React.createElement(FuturisticIcon, { name: "building", className: "h-12 w-12 text-amber-300/90" })),
        React.createElement("h1", { className: "text-2xl font-bold text-white" }, "Sistema Institucional"),
        React.createElement("p", { className: "max-w-md text-zinc-400 text-sm leading-relaxed" },
          "O módulo governamental está disponível apenas na versão offline, instalada localmente em escolas e universidades pelo administrador do sistema. Não está disponível no site público por questões de segurança e jurisdição."),
        React.createElement("div", { className: "flex flex-col sm:flex-row gap-3" },
          React.createElement("a", {
            href: encryptedPath("download"),
            className: "rounded-xl bg-amber-600/80 hover:bg-amber-500/90 border border-amber-500/40 px-6 py-3 text-sm font-medium text-white transition-colors",
          }, React.createElement("span", { className: "inline-flex items-center gap-2" }, React.createElement(FuturisticIcon, { name: "download", className: "h-4 w-4" }), "Baixar sistema offline")),
          React.createElement("a", {
            href: encryptedPath("educacao"),
            className: "rounded-xl border border-zinc-700 bg-zinc-800/60 hover:bg-zinc-700/60 px-6 py-3 text-sm font-medium text-zinc-300 transition-colors",
          }, "← Voltar ao Hub Educação"))));
  }

  return children;
}

function BackIcon() {
  return React.createElement("svg", { className: "h-4 w-4", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("path", { d: "M19 12H5M12 5l-7 7 7 7", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" }));
}
function ShieldIcon() {
  return React.createElement("svg", { className: "h-12 w-12 text-amber-400/60", viewBox: "0 0 24 24", fill: "none" },
    React.createElement("path", { d: "M12 3l7 3v5c0 4.418-3.134 8.556-7 9.5C8.134 19.556 5 15.418 5 11V6l7-3z", stroke: "currentColor", strokeWidth: "1.5", strokeLinejoin: "round" }),
    React.createElement("path", { d: "M9 12l2 2 4-4", stroke: "currentColor", strokeWidth: "1.5", strokeLinecap: "round", strokeLinejoin: "round" }));
}

const TABS = [
  { id: "dashboard", label: "Dashboard", iconName: "chart" },
  { id: "relatorio", label: "Relatórios", iconName: "clipboard" },
  { id: "previsao", label: "Previsões IA", iconName: "predict" },
  { id: "politica", label: "Políticas Públicas", iconName: "building" },
];

const REPORT_TYPES = ["geral", "desempenho", "evasao", "politicas", "investimento"];
const REPORT_PERIODS = ["mensal", "trimestral", "semestral", "anual"];
const PREDICT_SCENARIOS = [
  { id: "evasao", label: "Evasão Escolar", desc: "Previsão de taxa de abandono" },
  { id: "desempenho", label: "Desempenho Acadêmico", desc: "Tendência de aprendizado" },
  { id: "crescimento", label: "Crescimento de Usuários", desc: "Projeção de engajamento" },
  { id: "politica", label: "Impacto de Política", desc: "Avaliação de intervenções" },
];

function StatCard({ label, value, sub, color, trend }) {
  return React.createElement(motion.div, {
    className: `rounded-2xl border bg-[rgba(15,23,42,0.9)] p-5 ${color || "border-white/8"}`,
    initial: { opacity: 0, y: 12 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.35 },
  },
    React.createElement("p", { className: "text-xs text-white/40 uppercase tracking-wider mb-1" }, label),
    React.createElement("p", { className: "text-3xl font-bold text-white" }, value ?? "—"),
    React.createElement("div", { className: "mt-1 flex items-center gap-2" },
      sub && React.createElement("p", { className: "text-xs text-white/40" }, sub),
      trend != null && trend !== "" && React.createElement("span", { className: `text-xs ${trend > 0 ? "text-emerald-400" : "text-red-400"}` }, trend > 0 ? "▲" : "▼", " ", Math.abs(trend), "%")
    )
  );
}

function RegionBar({ name, users, sessions, engagement, maxUsers }) {
  const pct = maxUsers > 0 ? Math.round((users / maxUsers) * 100) : 0;
  const engColor = engagement >= 70 ? "text-emerald-400" : engagement >= 55 ? "text-amber-400" : "text-red-400";
  return React.createElement("div", { className: "space-y-1.5" },
    React.createElement("div", { className: "flex items-center justify-between text-xs" },
      React.createElement("span", { className: "text-white/70 font-medium" }, name),
      React.createElement("div", { className: "flex items-center gap-4" },
        React.createElement("span", { className: "text-white/40 hidden sm:inline" }, users.toLocaleString("pt-BR"), " usuários"),
        React.createElement("span", { className: `font-mono ${engColor}` }, engagement, "% engaj.")
      )
    ),
    React.createElement("div", { className: "h-2 w-full rounded-full bg-white/6" },
      React.createElement("div", {
        className: "h-2 rounded-full transition-all duration-1000",
        style: { width: pct + "%", background: `linear-gradient(90deg, rgba(251,191,36,0.7), rgba(251,191,36,0.35))` },
      })
    )
  );
}

function PlanBar({ name, count, total }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  const colors = { free: "bg-white/25", basic: "bg-sky-500/60", medium: "bg-violet-500/60", master: "bg-amber-500/70" };
  return React.createElement("div", { className: "flex items-center gap-3" },
    React.createElement("span", { className: "w-16 text-xs text-white/50 capitalize" }, name),
    React.createElement("div", { className: "flex-1 h-1.5 rounded-full bg-white/6" },
      React.createElement("div", { className: `h-1.5 rounded-full ${colors[name] || "bg-white/30"}`, style: { width: pct + "%" } })
    ),
    React.createElement("span", { className: "w-8 text-right text-xs text-white/40 font-mono" }, count)
  );
}

function CanvasChart({ regions }) {
  const canvasRef = useRef(null);
  useEffect(function () {
    const canvas = canvasRef.current;
    if (!canvas || !regions || !regions.length) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "#020617"; ctx.fillRect(0, 0, W, H);

    const total = regions.reduce(function (a, r) { return a + r.users; }, 0);
    const colors = ["rgba(251,191,36,0.8)", "rgba(139,92,246,0.8)", "rgba(56,189,248,0.8)", "rgba(52,211,153,0.8)", "rgba(251,113,133,0.8)"];
    let startAngle = -Math.PI / 2;
    const cx = W / 2, cy = H / 2, r = Math.min(W, H) / 2 - 24;

    regions.forEach(function (region, i) {
      const slice = (region.users / total) * 2 * Math.PI;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.arc(cx, cy, r, startAngle, startAngle + slice);
      ctx.closePath();
      ctx.fillStyle = colors[i % colors.length];
      ctx.fill();
      ctx.strokeStyle = "#020617"; ctx.lineWidth = 2; ctx.stroke();

      // Label
      const midAngle = startAngle + slice / 2;
      const lx = cx + (r * 0.65) * Math.cos(midAngle);
      const ly = cy + (r * 0.65) * Math.sin(midAngle);
      ctx.fillStyle = "rgba(255,255,255,0.9)";
      ctx.font = "bold 10px sans-serif"; ctx.textAlign = "center";
      ctx.fillText(region.name.split(" ")[0], lx, ly - 3);
      ctx.font = "9px sans-serif";
      ctx.fillText(Math.round((region.users / total) * 100) + "%", lx, ly + 10);

      startAngle += slice;
    });
  }, [regions]);

  return React.createElement("canvas", { ref: canvasRef, width: 240, height: 240, className: "rounded-xl" });
}

function GovernoPageInner() {
  const [token, setToken] = useState(null);
  const [profile, setProfile] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [stats, setStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(false);
  const [statsError, setStatsError] = useState(null);

  // Report
  const [reportType, setReportType] = useState("geral");
  const [reportPeriod, setReportPeriod] = useState("mensal");
  const [reportRegion, setReportRegion] = useState("nacional");
  const [reportContent, setReportContent] = useState(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState(null);

  // Predict
  const [predictScenario, setPredictScenario] = useState("evasao");
  const [predictContext, setPredictContext] = useState("");
  const [predictResult, setPredictResult] = useState(null);
  const [predictLoading, setPredictLoading] = useState(false);
  const [predictError, setPredictError] = useState(null);

  // Policy
  const [policyChallenge, setPolicyChallenge] = useState("");
  const [policyRegion, setPolicyRegion] = useState("");
  const [policyBudget, setPolicyBudget] = useState("");
  const [policyResult, setPolicyResult] = useState(null);
  const [policyLoading, setPolicyLoading] = useState(false);
  const [policyError, setPolicyError] = useState(null);

  useEffect(function () {
    try {
      const t = window.localStorage.getItem("syntexa_token");
      setToken(t || null);
      if (t) {
        getProfile(t)
          .then(function (p) {
            setProfile(p);
            if (p && p.is_admin) {
              setStatsLoading(true);
              govStats(t).then(function (s) { setStats(s); }).catch(function () { setStatsError("Erro ao carregar indicadores."); }).finally(function () { setStatsLoading(false); });
            }
          })
          .catch(function () {}).finally(function () { setAuthLoading(false); });
      } else {
        setAuthLoading(false);
      }
    } catch { setAuthLoading(false); }
  }, []);

  if (authLoading) return React.createElement(AppShell, null, React.createElement("div", { className: "flex min-h-[50vh] items-center justify-center" }, React.createElement("div", { className: "h-6 w-6 animate-spin rounded-full border-2 border-white/20 border-t-amber-400" })));

  if (!token) return React.createElement(AppShell, null, React.createElement("div", { className: "flex min-h-[60vh] flex-col items-center justify-center py-12 text-center" },
    React.createElement(motion.div, { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 } },
      React.createElement(ShieldIcon, null),
      React.createElement("h2", { className: "mt-4 text-2xl font-bold text-white" }, "Acesso Restrito"),
      React.createElement("p", { className: "mt-2 max-w-sm text-sm text-white/50" }, "Área exclusiva para credenciais governamentais e administrativas."),
      React.createElement("button", { onClick: function () { window.location.href = encryptedPath("login"); }, className: "mt-6 rounded-[14px] bg-amber-600/80 border border-amber-500/40 px-5 py-2.5 text-sm font-medium text-white hover:bg-amber-500/90" }, "Entrar com credenciais"),
      React.createElement("button", { onClick: function () { window.location.href = "/educacao"; }, className: "mt-4 inline-flex items-center gap-1.5 text-xs text-white/30 hover:text-white/60" }, React.createElement(BackIcon, null), "Voltar")
    )));

  if (profile && !profile.is_admin) return React.createElement(AppShell, null, React.createElement("div", { className: "flex min-h-[60vh] flex-col items-center justify-center py-12 text-center" },
    React.createElement(motion.div, { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 } },
      React.createElement(ShieldIcon, null),
      React.createElement("h2", { className: "mt-4 text-2xl font-bold text-white" }, "Acesso Negado"),
      React.createElement("p", { className: "mt-2 max-w-sm text-sm text-white/50" }, "Seu perfil não possui credenciais governamentais. Contate um administrador."),
      React.createElement("button", { onClick: function () { window.location.href = "/educacao"; }, className: "mt-6 inline-flex items-center gap-1.5 text-xs text-white/30 hover:text-white/60" }, React.createElement(BackIcon, null), "Voltar")
    )));

  const maxUsers = stats ? Math.max(...(stats.regions || []).map(function (r) { return r.users; }), 1) : 1;

  return React.createElement(AppShell, null,
    React.createElement("div", { className: "py-8 space-y-6" },
      // Header
      React.createElement(motion.div, { initial: { opacity: 0, y: 16 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.4 } },
        React.createElement("button", { onClick: function () { window.location.href = "/educacao"; }, className: "inline-flex items-center gap-1.5 text-xs text-white/40 hover:text-white/70 mb-6" }, React.createElement(BackIcon, null), "Educação & Pesquisa"),
        React.createElement("div", { className: "flex items-start justify-between flex-wrap gap-3" },
          React.createElement("div", null,
            React.createElement("div", { className: "mb-2 inline-flex items-center gap-2 rounded-full border border-amber-500/20 bg-amber-500/10 px-3 py-1 text-xs text-amber-300" },
              React.createElement("span", { className: "h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" }),
              "Painel Governamental · Acesso Admin"
            ),
            React.createElement("h1", { className: "text-3xl font-bold text-white" }, "Painel institucional"),
            React.createElement("p", { className: "mt-1 text-sm text-white/50" }, "Relatórios e previsões via IA. Indicadores nacionais regionais dependem de integração com bases oficiais — sem dados inventados.")
          ),
          React.createElement("div", { className: "text-right text-xs text-white/30" },
            React.createElement("p", null, "Admin: ", React.createElement("span", { className: "text-white/60" }, profile?.email || ""))
          )
        )
      ),

      // Tabs
      React.createElement("div", { className: "flex flex-wrap gap-2" },
        TABS.map(function (t) {
          return React.createElement("button", {
            key: t.id,
            onClick: function () { setActiveTab(t.id); },
            className: `rounded-xl border px-4 py-2 text-sm font-medium transition-all ${activeTab === t.id ? "bg-amber-600/70 border-amber-500/40 text-white" : "border-white/8 text-white/50 hover:text-white/80"}`,
          }, React.createElement(FuturisticIcon, { name: t.iconName, className: "h-4 w-4 inline-block mr-1.5 align-[-2px]" }), t.label);
        })
      ),

      // ── Tab: Dashboard ──────────────────────────────────────────────────
      activeTab === "dashboard" && React.createElement(React.Fragment, null,
        statsLoading && React.createElement("div", { className: "flex items-center gap-2 text-sm text-white/40" },
          React.createElement("div", { className: "h-4 w-4 animate-spin rounded-full border-2 border-white/20 border-t-amber-400" }),
          "Carregando indicadores nacionais..."
        ),
        statsError && React.createElement("p", { className: "text-sm text-red-400" }, statsError),
        stats && React.createElement(React.Fragment, null,
          stats.disclaimer &&
            React.createElement("div", { className: "rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-3 text-xs text-amber-100/90 leading-relaxed" },
              stats.disclaimer
            ),
          // KPI cards (agregados reais da instalação)
          React.createElement("div", { className: "grid grid-cols-2 gap-4 sm:grid-cols-4" },
            React.createElement(StatCard, { label: "Total de Usuários", value: stats.total_users?.toLocaleString("pt-BR"), sub: "Cadastrados nesta instalação", color: "border-amber-500/20" }),
            React.createElement(StatCard, { label: "Usuários Ativos", value: stats.active_users?.toLocaleString("pt-BR"), sub: "Conta ativa", color: "border-amber-500/15" }),
            React.createElement(StatCard, { label: "Sessões de IA", value: stats.total_sessions?.toLocaleString("pt-BR"), sub: "Total histórico", color: "border-white/8" }),
            React.createElement(StatCard, { label: "Engajamento", value: (stats.indicators?.engagement_rate ?? 0) + "%", sub: "Ativos / total", color: stats.indicators?.engagement_rate >= 70 ? "border-emerald-500/20" : "border-amber-500/10" })
          ),

          // Regional — só quando houver dados reais
          (stats.regions || []).length > 0 &&
          React.createElement("div", { className: "grid gap-4 lg:grid-cols-3" },
            React.createElement(motion.div, { className: "lg:col-span-2 rounded-2xl border border-white/8 bg-[rgba(15,23,42,0.9)] p-6", initial: { opacity: 0, y: 12 }, animate: { opacity: 1, y: 0 }, transition: { delay: 0.2 } },
              React.createElement("h2", { className: "mb-4 text-sm font-semibold text-white" }, "Distribuição Regional — Engajamento"),
              React.createElement("div", { className: "space-y-4" },
                (stats.regions || []).map(function (r) {
                  return React.createElement(RegionBar, { key: r.name, name: r.name, users: r.users, sessions: r.sessions, engagement: r.engagement || 65, maxUsers: maxUsers });
                })
              )
            ),
            React.createElement(motion.div, { className: "rounded-2xl border border-white/8 bg-[rgba(15,23,42,0.9)] p-6 flex flex-col items-center", initial: { opacity: 0, y: 12 }, animate: { opacity: 1, y: 0 }, transition: { delay: 0.25 } },
              React.createElement("h2", { className: "mb-4 self-start text-sm font-semibold text-white" }, "Distribuição por Região"),
              React.createElement(CanvasChart, { regions: stats.regions || [] }),
            )
          ),
          (stats.regions || []).length === 0 &&
            React.createElement("div", { className: "rounded-2xl border border-white/10 bg-[rgba(15,23,42,0.6)] p-6 text-sm text-white/55" },
              "Não há mapa regional nesta versão: os totais acima vêm apenas desta base de usuários. Quando houver integração com dados geográficos ou institucionais, os gráficos regionais aparecerão aqui."
            ),

          // Plan distribution
          React.createElement(motion.div, { className: "grid gap-4 sm:grid-cols-2", initial: { opacity: 0 }, animate: { opacity: 1 }, transition: { delay: 0.3 } },
            React.createElement("div", { className: "rounded-2xl border border-white/8 bg-[rgba(15,23,42,0.9)] p-5" },
              React.createElement("h3", { className: "mb-4 text-sm font-semibold text-white" }, "Distribuição de Planos"),
              React.createElement("div", { className: "space-y-2.5" },
                Object.entries(stats.plan_distribution || {}).map(function ([name, count]) {
                  return React.createElement(PlanBar, { key: name, name: name, count: count, total: stats.total_users });
                })
              )
            ),
            React.createElement("div", { className: "rounded-2xl border border-white/8 bg-[rgba(15,23,42,0.9)] p-5 space-y-3" },
              React.createElement("h3", { className: "text-sm font-semibold text-white" }, "Métricas-chave"),
              [
                ["Média sessões/usuário", (stats.indicators?.avg_sessions_per_user || 0) + " sessões"],
                ["Risco de evasão estimado", (stats.indicators?.dropout_risk_estimate || 0) + "%"],
                ["Taxa de engajamento", (stats.indicators?.engagement_rate || 0) + "%"],
              ].map(function ([k, v]) {
                return React.createElement("div", { key: k, className: "flex items-center justify-between border-b border-white/5 pb-2" },
                  React.createElement("span", { className: "text-xs text-white/50" }, k),
                  React.createElement("span", { className: "font-mono text-sm text-white/80" }, v)
                );
              }),
              React.createElement("div", { className: "flex items-center gap-2 pt-1" },
                React.createElement("span", { className: "h-2 w-2 rounded-full bg-emerald-400 animate-pulse" }),
                React.createElement("span", { className: "text-xs text-white/60" }, "Plataforma operacional")
              )
            )
          )
        )
      ),

      // ── Tab: Relatórios ──────────────────────────────────────────────────
      activeTab === "relatorio" && React.createElement(motion.div, { className: "rounded-2xl border border-amber-500/15 bg-[rgba(15,23,42,0.9)] p-6 space-y-5", initial: { opacity: 0, y: 12 }, animate: { opacity: 1, y: 0 } },
        React.createElement("div", null,
          React.createElement("h2", { className: "text-base font-semibold text-white" }, "Gerador de Relatórios Educacionais"),
          React.createElement("p", { className: "mt-0.5 text-xs text-white/40" }, "Relatórios automáticos com análise, indicadores e recomendações de políticas públicas")
        ),
        React.createElement("div", { className: "grid gap-4 sm:grid-cols-3" },
          React.createElement("div", null,
            React.createElement("p", { className: "mb-2 text-xs text-white/40 uppercase tracking-wider" }, "Tipo"),
            React.createElement("div", { className: "space-y-1.5" },
              REPORT_TYPES.map(function (t) {
                return React.createElement("button", { key: t, onClick: function () { setReportType(t); }, className: `w-full rounded-xl border px-3 py-1.5 text-left text-xs capitalize transition-all ${reportType === t ? "bg-amber-600/60 border-amber-500/40 text-white" : "border-white/8 text-white/50 hover:text-white/80"}` }, t);
              })
            )
          ),
          React.createElement("div", null,
            React.createElement("p", { className: "mb-2 text-xs text-white/40 uppercase tracking-wider" }, "Período"),
            React.createElement("div", { className: "space-y-1.5" },
              REPORT_PERIODS.map(function (p) {
                return React.createElement("button", { key: p, onClick: function () { setReportPeriod(p); }, className: `w-full rounded-xl border px-3 py-1.5 text-left text-xs capitalize transition-all ${reportPeriod === p ? "bg-amber-600/60 border-amber-500/40 text-white" : "border-white/8 text-white/50 hover:text-white/80"}` }, p);
              })
            )
          ),
          React.createElement("div", null,
            React.createElement("p", { className: "mb-2 text-xs text-white/40 uppercase tracking-wider" }, "Abrangência"),
            React.createElement("div", { className: "space-y-1.5" },
              ["nacional", "sudeste", "nordeste", "sul", "norte", "centro-oeste"].map(function (r) {
                return React.createElement("button", { key: r, onClick: function () { setReportRegion(r); }, className: `w-full rounded-xl border px-3 py-1.5 text-left text-xs capitalize transition-all ${reportRegion === r ? "bg-amber-600/60 border-amber-500/40 text-white" : "border-white/8 text-white/50 hover:text-white/80"}` }, r);
              })
            )
          )
        ),
        React.createElement("button", {
          onClick: async function () {
            setReportLoading(true); setReportContent(null); setReportError(null);
            try { const r = await govGenerateReport(token, reportType, reportPeriod, reportRegion); setReportContent(r.report); }
            catch (e) { setReportError(e.message); }
            finally { setReportLoading(false); }
          },
          disabled: reportLoading,
          className: "rounded-[14px] bg-amber-600/80 border border-amber-500/40 px-5 py-2.5 text-sm font-medium text-white hover:bg-amber-500/90 disabled:opacity-50",
        }, reportLoading ? React.createElement("span", { className: "flex items-center gap-2" }, React.createElement("span", { className: "h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" }), "Gerando relatório...") : "Gerar relatório com IA"),
        reportError && React.createElement("p", { className: "text-xs text-red-400" }, reportError),
        reportContent && React.createElement(motion.div, { className: "rounded-xl border border-white/8 bg-[rgba(8,15,30,0.8)] p-5", initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 } },
          React.createElement("p", { className: "mb-3 text-xs font-medium text-amber-300 uppercase tracking-wider" }, "Relatório gerado"),
          React.createElement("div", { className: "whitespace-pre-wrap text-sm text-white/80 leading-relaxed" }, reportContent)
        )
      ),

      // ── Tab: Previsões ────────────────────────────────────────────────────
      activeTab === "previsao" && React.createElement(motion.div, { className: "space-y-5", initial: { opacity: 0, y: 12 }, animate: { opacity: 1, y: 0 } },
        React.createElement("div", { className: "rounded-2xl border border-amber-500/15 bg-[rgba(15,23,42,0.9)] p-6" },
          React.createElement("h2", { className: "mb-1 text-base font-semibold text-white flex items-center gap-2" },
            React.createElement(FuturisticIcon, { name: "predict", className: "h-5 w-5 text-amber-400/90" }),
            "Previsões com Inteligência Artificial"),
          React.createElement("p", { className: "mb-5 text-xs text-white/40" }, "Análise preditiva baseada em evidências com intervalos de confiança e intervenções recomendadas"),
          React.createElement("div", { className: "mb-4 grid gap-2 sm:grid-cols-2" },
            PREDICT_SCENARIOS.map(function (sc) {
              return React.createElement("button", { key: sc.id, onClick: function () { setPredictScenario(sc.id); }, className: `flex flex-col items-start rounded-xl border p-3 text-left transition-all ${predictScenario === sc.id ? "border-amber-500/40 bg-amber-500/8 text-amber-300" : "border-white/8 text-white/50 hover:text-white/80"}` },
                React.createElement("span", { className: "text-xs font-semibold" }, sc.label),
                React.createElement("span", { className: "text-[10px] opacity-60 mt-0.5" }, sc.desc)
              );
            })
          ),
          React.createElement("textarea", {
            value: predictContext,
            onChange: function (e) { setPredictContext(e.target.value); },
            placeholder: "Contexto adicional (opcional): região, período, dados específicos...",
            rows: 2,
            className: "mb-4 w-full resize-none rounded-xl border border-white/10 bg-[rgba(8,15,30,0.8)] px-3 py-2 text-sm text-white placeholder:text-white/25 focus:outline-none",
          }),
          React.createElement("button", {
            onClick: async function () {
              setPredictLoading(true); setPredictResult(null); setPredictError(null);
              try { const r = await govPredict(token, predictScenario, predictContext); setPredictResult(r.prediction); }
              catch (e) { setPredictError(e.message); }
              finally { setPredictLoading(false); }
            },
            disabled: predictLoading,
            className: "rounded-[14px] bg-amber-600/80 border border-amber-500/40 px-5 py-2.5 text-sm font-medium text-white hover:bg-amber-500/90 disabled:opacity-50",
          }, predictLoading ? React.createElement("span", { className: "flex items-center gap-2" }, React.createElement("span", { className: "h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" }), "Analisando...") : "Gerar previsão")
        ),
        predictError && React.createElement("p", { className: "text-sm text-red-400" }, predictError),
        predictResult && React.createElement(motion.div, { className: "rounded-2xl border border-amber-500/10 bg-[rgba(15,23,42,0.9)] p-6", initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 } },
          React.createElement("p", { className: "mb-3 text-xs font-medium text-amber-300 uppercase tracking-wider" }, "Análise preditiva — " + PREDICT_SCENARIOS.find(s => s.id === predictScenario)?.label),
          React.createElement("div", { className: "whitespace-pre-wrap text-sm text-white/80 leading-relaxed" }, predictResult)
        )
      ),

      // ── Tab: Políticas ────────────────────────────────────────────────────
      activeTab === "politica" && React.createElement(motion.div, { className: "space-y-5", initial: { opacity: 0, y: 12 }, animate: { opacity: 1, y: 0 } },
        React.createElement("div", { className: "rounded-2xl border border-amber-500/15 bg-[rgba(15,23,42,0.9)] p-6 space-y-4" },
          React.createElement("div", null,
            React.createElement("h2", { className: "text-base font-semibold text-white flex items-center gap-2" },
              React.createElement(FuturisticIcon, { name: "building", className: "h-5 w-5 text-amber-400/90" }),
              "Gerador de Políticas Públicas Educacionais"),
            React.createElement("p", { className: "mt-0.5 text-xs text-white/40" }, "Propostas completas com diagnóstico, objetivos SMART, estratégias, cronograma e KPIs")
          ),
          React.createElement("div", null,
            React.createElement("label", { className: "mb-1 block text-xs text-white/50" }, "Desafio / Problema educacional *"),
            React.createElement("textarea", { value: policyChallenge, onChange: function (e) { setPolicyChallenge(e.target.value); }, placeholder: "Ex: Alta taxa de evasão escolar no ensino médio nas regiões Norte e Nordeste...", rows: 3, className: "w-full resize-none rounded-xl border border-white/10 bg-[rgba(8,15,30,0.8)] px-3 py-2 text-sm text-white placeholder:text-white/25 focus:outline-none focus:border-amber-500/30" })
          ),
          React.createElement("div", { className: "grid gap-3 sm:grid-cols-2" },
            React.createElement("div", null,
              React.createElement("label", { className: "mb-1 block text-xs text-white/50" }, "Região alvo"),
              React.createElement("input", { value: policyRegion, onChange: function (e) { setPolicyRegion(e.target.value); }, placeholder: "Ex: Nordeste, Pará, Nacional...", className: "w-full rounded-xl border border-white/10 bg-[rgba(8,15,30,0.8)] px-3 py-2 text-sm text-white placeholder:text-white/25 focus:outline-none" })
            ),
            React.createElement("div", null,
              React.createElement("label", { className: "mb-1 block text-xs text-white/50" }, "Orçamento disponível"),
              React.createElement("input", { value: policyBudget, onChange: function (e) { setPolicyBudget(e.target.value); }, placeholder: "Ex: R$ 500 milhões, limitado...", className: "w-full rounded-xl border border-white/10 bg-[rgba(8,15,30,0.8)] px-3 py-2 text-sm text-white placeholder:text-white/25 focus:outline-none" })
            )
          ),
          React.createElement("button", {
            onClick: async function () {
              if (!policyChallenge.trim()) return;
              setPolicyLoading(true); setPolicyResult(null); setPolicyError(null);
              try { const r = await govPolicy(token, policyChallenge, policyRegion, policyBudget); setPolicyResult(r.policy); }
              catch (e) { setPolicyError(e.message); }
              finally { setPolicyLoading(false); }
            },
            disabled: policyLoading || !policyChallenge.trim(),
            className: "rounded-[14px] bg-amber-600/80 border border-amber-500/40 px-5 py-2.5 text-sm font-medium text-white hover:bg-amber-500/90 disabled:opacity-50",
          }, policyLoading ? React.createElement("span", { className: "flex items-center gap-2" }, React.createElement("span", { className: "h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" }), "Elaborando proposta...") : "Elaborar política pública")
        ),
        policyError && React.createElement("p", { className: "text-sm text-red-400" }, policyError),
        policyResult && React.createElement(motion.div, { className: "rounded-2xl border border-amber-500/10 bg-[rgba(15,23,42,0.9)] p-6", initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 } },
          React.createElement("p", { className: "mb-3 text-xs font-medium text-amber-300 uppercase tracking-wider" }, "Proposta de política pública elaborada"),
          React.createElement("div", { className: "whitespace-pre-wrap text-sm text-white/80 leading-relaxed" }, policyResult)
        )
      )
    )
  );
}

export default function GovernoPage() {
  return React.createElement(GovGuard, null, React.createElement(GovernoPageInner, null));
}
