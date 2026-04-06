"use client";

import React, { useEffect, useState } from "react";
import { AppShell } from "../../components/shell";
import { Card } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { encryptedPath } from "../../lib/routes";
import { getAdminAllowedIps, putAdminAllowedIps } from "../../lib/api";
import { FuturisticIcon } from "../../components/icons/futuristic-icons";

export default function ConfigPage() {
  const [token, setToken] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [ipText, setIpText] = useState("");
  const [ipStatus, setIpStatus] = useState("");
  const [ipLoading, setIpLoading] = useState(false);

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

  return React.createElement(
    AppShell,
    null,
    React.createElement(
      "div",
      { className: "mx-auto flex max-w-3xl flex-col gap-8 py-10" },
      React.createElement(
        Card,
        {
          title: "Configurações da conta",
          description: "Preferências e dados da sua conta Syntexa.",
        },
        React.createElement(
          "p",
          { className: "text-sm text-white/70" },
          "Use Planos para assinatura, Perfil para dados pessoais e o painel Admin (se aplicável) para gestão da plataforma."
        )
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
            { className: "flex items-start gap-3 rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-3 mb-4" },
            React.createElement(FuturisticIcon, { name: "shield", className: "h-5 w-5 text-cyan-400/90 shrink-0 mt-0.5" }),
            React.createElement(
              "p",
              { className: "text-xs text-white/60 leading-relaxed" },
              "A lista é armazenada no servidor. Para bloquear acesso por IP na prática, configure também o proxy (Cloudflare) ou o nginx na VPS — esta tela não substitui firewall."
            )
          ),
          React.createElement("label", { className: "mb-2 block text-xs font-medium text-white/50" }, "IPs (IPv4 ou IPv6, um por linha)"),
          React.createElement("textarea", {
            className:
              "mb-3 min-h-[140px] w-full rounded-xl border border-white/10 bg-[rgba(8,15,30,0.85)] px-3 py-2 font-mono text-sm text-white placeholder:text-white/25 focus:outline-none focus:border-cyan-500/35",
            placeholder: "203.0.113.10\n2001:db8::1",
            value: ipText,
            disabled: ipLoading,
            onChange: function (e) {
              setIpText(e.target.value);
            },
          }),
          ipStatus &&
            React.createElement("p", { className: "mb-3 text-xs text-amber-200/90" }, ipStatus),
          React.createElement(
            Button,
            { type: "button", variant: "primary", onClick: saveIps, disabled: ipLoading || !token },
            ipLoading ? "Carregando…" : "Salvar IPs"
          )
        )
    )
  );
}
