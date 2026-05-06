"use client";

import React, { useEffect, useState } from "react";
import { AppShell } from "../../../components/shell";
import { getAdminAllowedIps, putAdminAllowedIps, getAdminSystemStatus, getAdminMe } from "../../../lib/api";
import { FuturisticIcon } from "../../../components/icons/futuristic-icons";

function AdminGuard({ children }) {
  const [state, setState] = useState("checking");
  useEffect(function () {
    (async function () {
      try {
        const token = typeof window !== "undefined" ? window.localStorage.getItem("syntexa_token") : "";
        if (!token) {
          setState("denied");
          return;
        }
        const me = await getAdminMe(token);
        setState(me && me.is_admin ? "ok" : "denied");
      } catch {
        setState("denied");
      }
    })();
  }, []);

  if (state === "checking") {
    return React.createElement("div", { className: "flex min-h-screen items-center justify-center text-sm text-zinc-500" }, "Verificando acesso...");
  }
  if (state !== "ok") {
    return React.createElement(
      AppShell,
      null,
      React.createElement(
        "div",
        { className: "flex min-h-[60vh] flex-col items-center justify-center gap-3 text-center" },
        React.createElement("h1", { className: "text-lg font-semibold text-zinc-900" }, "Acesso restrito"),
        React.createElement("a", { href: "/login", className: "rounded-xl bg-violet-600 px-5 py-2 text-sm font-medium text-white hover:bg-violet-500" }, "Fazer login")
      )
    );
  }
  return children;
}

function SecurityHubPage() {
  const [ipsText, setIpsText] = useState("");
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState(null);
  const [msg, setMsg] = useState("");

  useEffect(function () {
    (async function () {
      try {
        const token = window.localStorage.getItem("syntexa_token");
        if (!token) return;
        const [ips, sys] = await Promise.all([getAdminAllowedIps(token), getAdminSystemStatus(token)]);
        setIpsText(((ips && ips.ips) || []).join("\n"));
        setStatus(sys || null);
      } catch (_) {}
    })();
  }, []);

  async function save() {
    try {
      setSaving(true);
      setMsg("");
      const lines = ipsText
        .split(/\r?\n/)
        .map(function (s) { return s.trim(); })
        .filter(Boolean);
      const token = window.localStorage.getItem("syntexa_token");
      if (!token) throw new Error("Sessão admin não encontrada.");
      const out = await putAdminAllowedIps(token, lines);
      setIpsText(((out && out.ips) || []).join("\n"));
      setMsg("Configuração salva com sucesso.");
    } catch (e) {
      setMsg((e && e.message) || "Erro ao salvar.");
    } finally {
      setSaving(false);
    }
  }

  return React.createElement(
    AppShell,
    null,
    React.createElement(
      "div",
      { className: "mx-auto flex w-full max-w-5xl flex-col gap-5 px-4 py-8 sm:px-6" },
      React.createElement(
        "div",
        { className: "rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm" },
        React.createElement(
          "h1",
          { className: "inline-flex items-center gap-2 text-xl font-semibold text-zinc-900" },
          React.createElement(FuturisticIcon, { name: "shield", className: "h-5 w-5 text-violet-600" }),
          "Hub de Segurança"
        ),
        React.createElement(
          "p",
          { className: "mt-2 text-sm text-zinc-600" },
          "Centro administrativo para governança de acesso, postura operacional e controles de rede do ambiente institucional."
        )
      ),
      React.createElement(
        "section",
        { className: "rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm" },
        React.createElement("h2", { className: "text-base font-semibold text-zinc-900" }, "IP Allowlist administrativo"),
        React.createElement(
          "p",
          { className: "mt-1 text-xs text-zinc-500" },
          "Informe IPs ou redes permitidas para operações de backoffice (um por linha)."
        ),
        React.createElement("textarea", {
          rows: 10,
          value: ipsText,
          onChange: function (e) { setIpsText(e.target.value); },
          className: "mt-3 w-full rounded-xl border border-zinc-200 bg-zinc-50 p-3 text-xs font-mono text-zinc-700",
          placeholder: "203.0.113.10\n10.10.0.0/16\n2001:db8::/64",
        }),
        msg ? React.createElement("p", { className: "mt-2 text-xs text-zinc-600" }, msg) : null,
        React.createElement(
          "button",
          {
            type: "button",
            onClick: save,
            disabled: saving,
            className: "mt-3 rounded-xl bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-500 disabled:opacity-50",
          },
          saving ? "Salvando..." : "Salvar políticas de IP"
        )
      ),
      React.createElement(
        "section",
        { className: "rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm" },
        React.createElement("h2", { className: "text-base font-semibold text-zinc-900" }, "Snapshot operacional"),
        React.createElement(
          "p",
          { className: "mt-1 text-xs text-zinc-500" },
          "Visão rápida do backend para segurança operacional e disponibilidade."
        ),
        React.createElement(
          "pre",
          { className: "mt-3 max-h-80 overflow-auto rounded-xl bg-zinc-50 p-3 text-[11px] text-zinc-700" },
          JSON.stringify(status || { info: "sem dados" }, null, 2)
        )
      )
    )
  );
}

export default function Page() {
  return React.createElement(AdminGuard, null, React.createElement(SecurityHubPage));
}

