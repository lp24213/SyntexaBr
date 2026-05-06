"use client";

import React, { useEffect, useState } from "react";
import { AppShell } from "../../../components/shell";
import { FuturisticIcon } from "../../../components/icons/futuristic-icons";
import { createIntegrationToken, getAdminMe, getIntegrationConfig, listIntegrationTokens, revokeIntegrationToken, rotateIntegrationToken, setIntegrationConfig } from "../../../lib/api";

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
  if (state === "checking") return React.createElement("div", { className: "flex min-h-screen items-center justify-center text-sm text-zinc-500" }, "Verificando acesso...");
  if (state !== "ok") return React.createElement(AppShell, null, React.createElement("div", { className: "py-16 text-center text-zinc-600" }, "Acesso restrito."));
  return children;
}

function IntegrationsPageInner() {
  const [token, setToken] = useState("");
  const [items, setItems] = useState([]);
  const [name, setName] = useState("");
  const [scopes, setScopes] = useState("chat:read,chat:write");
  const [days, setDays] = useState(365);
  const [status, setStatus] = useState("");
  const [createdToken, setCreatedToken] = useState("");
  const [rpmLimit, setRpmLimit] = useState(null);
  const [rpmEdit, setRpmEdit] = useState("");

  async function load() {
    if (!token) return;
    try {
      const [list, cfg] = await Promise.all([
        listIntegrationTokens(token),
        getIntegrationConfig(token),
      ]);
      setItems(Array.isArray(list) ? list : []);
      const rpm = cfg && typeof cfg.token_rpm === "number" ? cfg.token_rpm : null;
      setRpmLimit(rpm);
      setRpmEdit(rpm !== null ? String(rpm) : "");
    } catch (e) {
      setStatus((e && e.message) || "Erro ao carregar tokens.");
    }
  }

  useEffect(function () {
    try {
      const t = window.localStorage.getItem("syntexa_token") || "";
      setToken(t);
    } catch (_) {}
  }, []);

  useEffect(function () {
    if (token) load();
  }, [token]);

  async function createNow() {
    if (!token || !name.trim()) return;
    setStatus("");
    try {
      const out = await createIntegrationToken(token, {
        name: name.trim(),
        scopes: scopes.trim() || "chat:read,chat:write",
        expires_days: Number(days) || 365,
      });
      setCreatedToken(String((out && out.token) || ""));
      setName("");
      await load();
      setStatus("Token criado. Copie agora: ele aparece somente uma vez.");
    } catch (e) {
      setStatus((e && e.message) || "Erro ao criar token.");
    }
  }

  async function revokeNow(id) {
    if (!token) return;
    try {
      await revokeIntegrationToken(token, id);
      await load();
      setStatus("Token revogado.");
    } catch (e) {
      setStatus((e && e.message) || "Erro ao revogar token.");
    }
  }

  async function rotateNow(id) {
    if (!token) return;
    try {
      const out = await rotateIntegrationToken(token, id);
      setCreatedToken(String((out && out.token) || ""));
      await load();
      setStatus("Token rotacionado. Copie o novo valor agora.");
    } catch (e) {
      setStatus((e && e.message) || "Erro ao rotacionar token.");
    }
  }

  async function saveRpm() {
    if (!token || !rpmEdit.trim()) return;
    try {
      const out = await setIntegrationConfig(token, { token_rpm: Number(rpmEdit) });
      const rpm = out && typeof out.token_rpm === "number" ? out.token_rpm : null;
      setRpmLimit(rpm);
      setRpmEdit(rpm !== null ? String(rpm) : rpmEdit);
      setStatus("Rate limit atualizado com sucesso.");
    } catch (e) {
      setStatus((e && e.message) || "Erro ao salvar limite.");
    }
  }

  return React.createElement(
    AppShell,
    null,
    React.createElement(
      "div",
      { className: "mx-auto w-full max-w-5xl px-4 py-8 space-y-5" },
      React.createElement(
        "section",
        { className: "rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm" },
        React.createElement("h1", { className: "inline-flex items-center gap-2 text-xl font-semibold text-zinc-900" },
          React.createElement(FuturisticIcon, { name: "key", className: "h-5 w-5 text-violet-600" }),
          "API Tokens de Integração"),
        React.createElement("p", { className: "mt-1 text-sm text-zinc-600" }, "Crie tokens para conectar clientes, ERPs e outras IAs à sua API com controle por escopo e validade."),
        rpmLimit !== null &&
          React.createElement("div", { className: "mt-3 flex flex-wrap items-center gap-2 text-xs text-zinc-500" },
            React.createElement("span", null, "Rate limit por token: ", React.createElement("strong", { className: "text-zinc-700" }, String(rpmLimit), " req/min")),
            React.createElement("input", {
              type: "number",
              min: 1,
              max: 10000,
              value: rpmEdit,
              onChange: function (e) { setRpmEdit(e.target.value); },
              className: "w-24 rounded-lg border border-zinc-200 bg-white px-2 py-1 text-xs text-zinc-700",
            }),
            React.createElement("button", {
              type: "button",
              onClick: saveRpm,
              className: "rounded-lg border border-zinc-200 bg-white px-2 py-1 text-xs text-zinc-700 hover:bg-zinc-50",
            }, "Salvar"))
      ),
      React.createElement(
        "section",
        { className: "rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm space-y-3" },
        React.createElement("h2", { className: "text-sm font-semibold text-zinc-900" }, "Novo token"),
        React.createElement("input", { value: name, onChange: function (e) { setName(e.target.value); }, placeholder: "Nome do token (ex.: ERP Universidade Alfa)", className: "w-full rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-800" }),
        React.createElement("input", { value: scopes, onChange: function (e) { setScopes(e.target.value); }, placeholder: "Escopos (ex.: chat:read,chat:write)", className: "w-full rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-800" }),
        React.createElement("input", { type: "number", min: 1, max: 3650, value: days, onChange: function (e) { setDays(e.target.value); }, className: "w-48 rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-800" }),
        React.createElement("button", { type: "button", onClick: createNow, className: "rounded-xl bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-500" }, "Criar token")
      ),
      createdToken &&
        React.createElement("section", { className: "rounded-2xl border border-emerald-200 bg-emerald-50 p-4 shadow-sm" },
          React.createElement("p", { className: "text-xs font-semibold text-emerald-800" }, "Token gerado (copie agora)"),
          React.createElement("code", { className: "mt-1 block break-all text-[11px] text-emerald-900" }, createdToken)),
      status && React.createElement("p", { className: "text-xs text-zinc-600" }, status),
      React.createElement(
        "section",
        { className: "rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm" },
        React.createElement("h2", { className: "text-sm font-semibold text-zinc-900" }, "Tokens existentes"),
        items.length === 0
          ? React.createElement("p", { className: "mt-2 text-xs text-zinc-500" }, "Nenhum token criado.")
          : React.createElement("div", { className: "mt-3 space-y-2" },
              items.map(function (it) {
                return React.createElement("div", { key: it.id, className: "rounded-xl border border-zinc-200 bg-zinc-50 p-3 text-xs text-zinc-700" },
                  React.createElement("div", { className: "flex flex-wrap items-center justify-between gap-2" },
                    React.createElement("div", null,
                      React.createElement("p", { className: "font-semibold text-zinc-900" }, it.name),
                      React.createElement("p", null, "Prefixo: ", React.createElement("code", null, it.token_prefix), " • Escopos: ", it.scopes)),
                    React.createElement("div", { className: "flex gap-2" },
                      React.createElement("button", {
                        type: "button",
                        onClick: function () { if (confirm("Rotacionar este token? O antigo deixará de funcionar.")) rotateNow(it.id); },
                        className: "rounded-lg border border-amber-300 px-3 py-1 text-xs text-amber-700 hover:bg-amber-50",
                      }, "Rotacionar"),
                      React.createElement("button", {
                        type: "button",
                        onClick: function () { if (confirm("Revogar este token?")) revokeNow(it.id); },
                        className: "rounded-lg border border-rose-300 px-3 py-1 text-xs text-rose-700 hover:bg-rose-50",
                      }, it.active ? "Revogar" : "Revogado"))));
              }))
      ),
      React.createElement(
        "section",
        { className: "rounded-2xl border border-violet-200 bg-violet-50 p-5 shadow-sm" },
        React.createElement("h2", { className: "text-sm font-semibold text-zinc-900" }, "Exemplo de uso da API (cliente externo)"),
        React.createElement(
          "pre",
          { className: "mt-2 overflow-auto rounded-xl border border-zinc-200 bg-white p-3 text-[11px] text-zinc-700" },
          [
            "curl -X POST https://api.syntexabr.com.br/v1/integrations/chat/completions \\",
            "  -H \"Content-Type: application/json\" \\",
            "  -H \"X-API-Token: stx_...\" \\",
            "  -d '{",
            "    \"model\":\"syntexa-large\",",
            "    \"messages\":[{\"role\":\"user\",\"content\":\"Olá, API Syntexa\"}]",
            "  }'",
            "",
            "# introspecção do token",
            "curl https://api.syntexabr.com.br/v1/integrations/me \\",
            "  -H \"X-API-Token: stx_...\"",
          ].join("\n")
        )
      )
    )
  );
}

export default function Page() {
  return React.createElement(AdminGuard, null, React.createElement(IntegrationsPageInner));
}

