"use client";

import React, { useEffect, useState } from "react";
import { AppShell } from "../../components/shell";
import { Card } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { encryptedPath } from "../../lib/routes";
import { enableTwoFactor, getAdminAllowedIps, putAdminAllowedIps, setupTwoFactor } from "../../lib/api";
import { FuturisticIcon } from "../../components/icons/futuristic-icons";

export default function ConfigPage() {
  const [token, setToken] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [ipText, setIpText] = useState("");
  const [ipStatus, setIpStatus] = useState("");
  const [ipLoading, setIpLoading] = useState(false);
  const [twoFaSecret, setTwoFaSecret] = useState("");
  const [twoFaUri, setTwoFaUri] = useState("");
  const [twoFaCode, setTwoFaCode] = useState("");
  const [twoFaStatus, setTwoFaStatus] = useState("");
  const [twoFaBusy, setTwoFaBusy] = useState(false);

  useEffect(() => {
    try {
      const t = window.localStorage.getItem("syntexa_token");
      if (!t) {
        window.location.href = encryptedPath("login");
        return;
      }
      setToken(t);
      setIsAdmin(window.localStorage.getItem("syntexa_is_admin") === "1");
    } catch {
      window.location.href = encryptedPath("login");
    }
  }, []);

  useEffect(() => {
    if (!token || !isAdmin) return;
    setIpLoading(true);
    getAdminAllowedIps(token)
      .then((d) => {
        if (d && Array.isArray(d.ips)) setIpText(d.ips.join("\n"));
      })
      .catch(() => setIpStatus("Não foi possível carregar a lista (verifique login admin e API)."))
      .finally(() => setIpLoading(false));
  }, [token, isAdmin]);

  function saveIps() {
    if (!token || !isAdmin) return;
    setIpStatus("");
    var lines = ipText
      .split(/\r?\n/)
      .map((s) => s.trim())
      .filter(Boolean);
    putAdminAllowedIps(token, lines)
      .then((r) => {
        setIpStatus("Salvo. " + (r.ips ? r.ips.length + " IP(s)." : ""));
        if (r.ips) setIpText(r.ips.join("\n"));
      })
      .catch((e) => setIpStatus(e.message || "Erro ao salvar."));
  }

  async function startTwoFactorSetup() {
    if (!token) return;
    setTwoFaBusy(true);
    setTwoFaStatus("");
    try {
      const data = await setupTwoFactor(token);
      setTwoFaSecret(String((data && data.secret) || ""));
      setTwoFaUri(String((data && data.otpauth_uri) || ""));
      setTwoFaStatus("Setup 2FA gerado. Cadastre no app autenticador e confirme o código abaixo.");
    } catch (e) {
      setTwoFaStatus((e && e.message) || "Não foi possível iniciar o setup 2FA.");
    } finally {
      setTwoFaBusy(false);
    }
  }

  async function confirmTwoFactor() {
    if (!token || !twoFaCode.trim()) return;
    setTwoFaBusy(true);
    setTwoFaStatus("");
    try {
      const out = await enableTwoFactor(token, twoFaCode.trim());
      setTwoFaStatus(String((out && out.detail) || "2FA ativado com sucesso."));
      setTwoFaCode("");
    } catch (e) {
      setTwoFaStatus((e && e.message) || "Falha ao ativar 2FA.");
    } finally {
      setTwoFaBusy(false);
    }
  }

  return React.createElement(
    AppShell,
    null,
    React.createElement(
      "div",
      { className: "mx-auto flex max-w-3xl flex-col gap-6 py-8 sm:py-10" },
      React.createElement(
        Card,
        {
          title: "Configurações da conta",
          description: "Preferências e dados da sua conta Syntexa.",
        },
        React.createElement(
          "p",
          { className: "text-sm text-zinc-600" },
          "Use Planos para assinatura e Perfil para dados pessoais e segurança."
        )
      ),
      React.createElement(
        Card,
        {
          title: "Segurança de conta (2FA)",
          description:
            "Ative autenticação em dois fatores (TOTP) para reforçar o acesso. Use apps como Google Authenticator, Authy ou Microsoft Authenticator.",
        },
        React.createElement(
          "div",
          { className: "mb-4 flex items-start gap-3 rounded-xl border border-violet-200 bg-violet-50 p-3" },
          React.createElement(FuturisticIcon, { name: "shield", className: "h-5 w-5 text-violet-500 shrink-0 mt-0.5" }),
          React.createElement(
            "p",
            { className: "text-xs leading-relaxed text-zinc-600" },
            "Para sua conta, a disponibilidade do 2FA depende da política do backend (admin/governo). Se não estiver habilitado, a API retorna mensagem de permissão."
          )
        ),
        React.createElement(
          "div",
          { className: "flex flex-wrap gap-2" },
          React.createElement(
            Button,
            { type: "button", variant: "primary", onClick: startTwoFactorSetup, disabled: twoFaBusy || !token },
            twoFaBusy ? "Gerando..." : "Gerar setup 2FA"
          )
        ),
        twoFaSecret &&
          React.createElement(
            "div",
            { className: "mt-4 rounded-xl border border-zinc-200 bg-white p-3" },
            React.createElement("p", { className: "text-xs font-semibold text-zinc-700" }, "Chave secreta"),
            React.createElement("code", { className: "mt-1 block break-all text-[11px] text-zinc-600" }, twoFaSecret),
            twoFaUri &&
              React.createElement(
                React.Fragment,
                null,
                React.createElement("p", { className: "mt-3 text-xs font-semibold text-zinc-700" }, "URI otpauth"),
                React.createElement("code", { className: "mt-1 block break-all text-[11px] text-zinc-600" }, twoFaUri)
              )
          ),
        React.createElement("label", { className: "mt-4 mb-2 block text-xs font-medium text-zinc-500" }, "Código do autenticador"),
        React.createElement("input", {
          type: "text",
          value: twoFaCode,
          onChange: function (e) {
            setTwoFaCode(e.target.value);
          },
          className:
            "mb-3 w-full rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-violet-300 focus:outline-none",
          placeholder: "Ex.: 123456",
          disabled: twoFaBusy || !token,
        }),
        React.createElement(
          Button,
          { type: "button", variant: "primary", onClick: confirmTwoFactor, disabled: twoFaBusy || !token || !twoFaCode.trim() },
          twoFaBusy ? "Validando..." : "Ativar 2FA"
        ),
        twoFaStatus &&
          React.createElement("p", { className: "mt-3 text-xs text-zinc-600" }, twoFaStatus)
      ),
      isAdmin &&
        React.createElement(
          Card,
          {
            title: "Rede e acessos (admin)",
            description:
              "Cadastre endereços IP de referência para equipes e instituições (um por linha). Serve para documentação e para você replicar regras no firewall ou nginx do servidor.",
          },
          React.createElement(
            "div",
            { className: "mb-4 flex items-start gap-3 rounded-xl border border-[#e2e8f0] bg-[#f1f5f9] p-3" },
            React.createElement(FuturisticIcon, { name: "shield", className: "h-5 w-5 text-[#5A7A96] shrink-0 mt-0.5" }),
            React.createElement(
              "p",
              { className: "text-xs leading-relaxed text-zinc-600" },
              "A lista é armazenada no servidor. Para bloquear acesso por IP na prática, configure também o proxy (Cloudflare) ou o nginx na VPS — esta tela não substitui firewall."
            )
          ),
          React.createElement("label", { className: "mb-2 block text-xs font-medium text-zinc-500" }, "IPs (IPv4 ou IPv6, um por linha)"),
          React.createElement("textarea", {
            className:
              "mb-3 min-h-[140px] w-full rounded-xl border border-zinc-200 bg-white px-3 py-2 font-mono text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-[#cbd5e1] focus:outline-none",
            placeholder: "203.0.113.10\n2001:db8::1",
            value: ipText,
            disabled: ipLoading,
            onChange: function (e) {
              setIpText(e.target.value);
            },
          }),
          ipStatus &&
            React.createElement("p", { className: "mb-3 text-xs text-zinc-600" }, ipStatus),
          React.createElement(
            Button,
            { type: "button", variant: "primary", onClick: saveIps, disabled: ipLoading || !token },
            ipLoading ? "Carregando…" : "Salvar IPs"
          )
        )
    )
  );
}
