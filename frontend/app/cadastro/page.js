"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AppShell } from "../../components/shell";
import { encryptedPath } from "../../lib/routes";
import { Card } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Button } from "../../components/ui/button";
import { getApiBase } from "../../lib/api";
import { FuturisticIcon } from "../../components/icons/futuristic-icons";

var API_BASE = getApiBase();

var TURNSTILE_SITE_KEY =
  (typeof process !== "undefined" && process.env && process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY) ||
  "";

var ROLES = [
  {
    id: "user",
    iconName: "medal",
    label: "Estudante",
    desc: "Acesso ao chat e educação pública anônima (tutor, labs, concursos)",
    color: "border-[#cbd5e1] hover:border-[#94a3b8]",
    accent: "text-[#5A7A96]",
  },
  {
    id: "teacher",
    iconName: "userTie",
    label: "Professor / Pesquisador",
    desc: "Ferramentas acadêmicas avançadas: correção, geração de provas, pesquisa científica",
    color: "border-[#cbd5e1] hover:border-[#94a3b8]",
    accent: "text-[#5A7A96]",
  },
  {
    id: "enterprise",
    iconName: "building",
    label: "Empresa / Profissional",
    desc: "Planos business, integrações e suporte dedicado",
    color: "border-amber-500/40 hover:border-amber-400",
    accent: "text-amber-400",
  },
  {
    id: "researcher",
    iconName: "microscope",
    label: "Cientista / Engenheiro",
    desc: "Motor de cálculo exato, laboratórios científicos e assistente de pesquisa",
    color: "border-emerald-500/40 hover:border-emerald-400",
    accent: "text-emerald-400",
  },
];

function useTurnstile(siteKey) {
  var [token, setToken] = useState("");
  var [ready, setReady] = useState(false);
  var widgetRef = React.useRef(null);

  React.useEffect(function () {
    if (!siteKey) return;
    if (typeof window === "undefined") return;
    if (window.turnstile) { setReady(true); return; }
    var existing = document.querySelector('script[src*="challenges.cloudflare.com/turnstile/v0/api.js"]');
    if (!existing) {
      var script = document.createElement("script");
      script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js";
      script.async = true;
      script.defer = true;
      script.onload = function () { setReady(true); };
      document.body.appendChild(script);
    } else {
      setReady(true);
    }
  }, [siteKey]);

  React.useEffect(function () {
    if (!ready || !siteKey || !widgetRef.current || !window.turnstile) return;
    var id = window.turnstile.render(widgetRef.current, {
      sitekey: siteKey,
      callback: function (tok) { setToken(tok); },
      "expired-callback": function () { setToken(""); },
      "error-callback": function () { setToken(""); },
    });
    return function () {
      if (window.turnstile && id) window.turnstile.remove(id);
    };
  }, [ready, siteKey]);

  return { token: token, widgetRef: widgetRef };
}

export default function CadastroPage() {
  // Step 1 = role selector, Step 2 = form
  var [step, setStep] = useState(1);
  var [role, setRole] = useState(null);
  var [name, setName] = useState("");
  var [email, setEmail] = useState("");
  var [password, setPassword] = useState("");
  var [confirmPassword, setConfirmPassword] = useState("");
  var [documentId, setDocumentId] = useState("");
  var [cep, setCep] = useState("");
  var [state, setState] = useState("");
  var [city, setCity] = useState("");
  var [addressLine, setAddressLine] = useState("");
  var [addressNumber, setAddressNumber] = useState("");
  var [addressComplement, setAddressComplement] = useState("");
  var [acceptedTerms, setAcceptedTerms] = useState(false);
  var [loading, setLoading] = useState(false);
  var [error, setError] = useState(null);
  var [success, setSuccess] = useState(null);
  var { token: turnstileToken, widgetRef } = useTurnstile(TURNSTILE_SITE_KEY);

  function selectRole(r) {
    setRole(r);
    setStep(2);
  }

  async function handleSubmit(ev) {
    ev.preventDefault();
    setError(null);
    setSuccess(null);
    if (password !== confirmPassword) {
      setError("As senhas não coincidem.");
      return;
    }
    if (!acceptedTerms) {
      setError("Você precisa aceitar os Termos e Condições para continuar.");
      return;
    }
    if (TURNSTILE_SITE_KEY && !turnstileToken) {
      setError("Aguarde a verificação de segurança carregar.");
      return;
    }
    setLoading(true);
    try {
      var resp = await fetch(API_BASE + "/v1/auth/public-register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          full_name: name,
          password,
          role: role || "user",
          document: documentId,
          cep,
          state,
          city,
          address_line: addressLine,
          address_number: addressNumber,
          address_complement: addressComplement || null,
          turnstile_token: turnstileToken,
        }),
      });
      if (!resp.ok) {
        var txt = await resp.text();
        throw new Error(txt || "Falha ao criar conta.");
      }
      try { window.localStorage.setItem("syntexa_pending_email", email); } catch {}
      setSuccess("Conta criada! Enviamos um código de verificação para seu e-mail.");
      setTimeout(function () { window.location.href = encryptedPath("activate-signup"); }, 1200);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado ao criar conta.");
    } finally {
      setLoading(false);
    }
  }

  var selectedRoleInfo = ROLES.find(function(r) { return r.id === role; });

  return React.createElement(
    AppShell,
    null,
    React.createElement("div", { className: "flex min-h-[calc(100vh-5rem)] items-start justify-center py-8 px-4" },
      React.createElement(AnimatePresence, { mode: "wait" },
        step === 1
          ? React.createElement(motion.div, {
              key: "step1",
              className: "w-full max-w-xl",
              initial: { opacity: 0, y: 16 },
              animate: { opacity: 1, y: 0 },
              exit: { opacity: 0, y: -12 },
              transition: { duration: 0.25 },
            },
            React.createElement("div", { className: "mb-8 text-center" },
              React.createElement("h1", { className: "text-2xl font-bold text-zinc-100 mb-2" }, "Criar conta"),
              React.createElement("p", { className: "text-zinc-400 text-sm" }, "Escolha seu perfil para personalizar sua experiência")),
            React.createElement("div", { className: "grid grid-cols-1 sm:grid-cols-2 gap-4" },
              ROLES.map(function(r) {
                return React.createElement("button", {
                  key: r.id,
                  onClick: function() { selectRole(r.id); },
                  className: "syntexa-card text-left p-5 border rounded-xl transition-all duration-200 " + r.color + " bg-zinc-900 hover:bg-zinc-800",
                },
                  React.createElement("div", { className: "mb-3 flex h-12 w-12 items-center justify-center rounded-xl border border-zinc-200 bg-zinc-50" },
                    React.createElement(FuturisticIcon, { name: r.iconName, className: "h-7 w-7 " + r.accent })),
                  React.createElement("div", { className: "font-semibold text-zinc-900 mb-1 " + r.accent }, r.label),
                  React.createElement("div", { className: "text-xs text-zinc-400 leading-relaxed" }, r.desc));
              })),
            React.createElement("div", { className: "mt-6 text-center text-xs text-zinc-500" },
              "Já tem conta? ",
              React.createElement("button", {
                type: "button",
                onClick: function() { window.location.href = encryptedPath("login"); },
                className: "text-zinc-600 hover:text-zinc-900 hover:underline",
              }, "Fazer login")))

          : React.createElement(motion.div, {
              key: "step2",
              className: "w-full max-w-md",
              initial: { opacity: 0, y: 16 },
              animate: { opacity: 1, y: 0 },
              exit: { opacity: 0, y: -12 },
              transition: { duration: 0.25 },
            },
            selectedRoleInfo && React.createElement("div", {
              className: "flex items-center gap-3 mb-5 p-3 rounded-lg bg-zinc-50 border border-zinc-200",
            },
              React.createElement(FuturisticIcon, { name: selectedRoleInfo.iconName, className: "h-8 w-8 shrink-0 " + selectedRoleInfo.accent }),
              React.createElement("div", null,
                React.createElement("div", { className: "text-sm font-medium text-zinc-900" }, selectedRoleInfo.label),
                React.createElement("button", {
                  type: "button",
                  onClick: function() { setStep(1); },
                  className: "text-xs text-zinc-500 hover:text-zinc-800 underline",
                }, "Alterar perfil"))),
            React.createElement(Card, { title: "Dados da conta", description: "Preencha suas informações para continuar." },
              React.createElement("form", { onSubmit: handleSubmit, className: "space-y-5" },
                React.createElement("div", { className: "space-y-3" },
                  React.createElement(Input, { label: "Nome completo", value: name, onChange: function(e) { setName(e.target.value); }, required: true }),
                  React.createElement(Input, { label: "E-mail", type: "email", autoComplete: "email", value: email, onChange: function(e) { setEmail(e.target.value); }, required: true }),
                  React.createElement(Input, { label: "CPF/CNPJ", value: documentId, onChange: function(e) { setDocumentId(e.target.value); }, required: true }),
                  React.createElement(Input, { label: "CEP", value: cep, onChange: function(e) { setCep(e.target.value); }, required: true }),
                  React.createElement(Input, { label: "Estado (UF)", value: state, onChange: function(e) { setState(e.target.value); }, required: true }),
                  React.createElement(Input, { label: "Cidade", value: city, onChange: function(e) { setCity(e.target.value); }, required: true }),
                  React.createElement(Input, { label: "Endereço (rua/avenida)", value: addressLine, onChange: function(e) { setAddressLine(e.target.value); }, required: true }),
                  React.createElement(Input, { label: "Número", value: addressNumber, onChange: function(e) { setAddressNumber(e.target.value); }, required: true }),
                  React.createElement(Input, { label: "Complemento", value: addressComplement, onChange: function(e) { setAddressComplement(e.target.value); } }),
                  React.createElement(Input, { label: "Senha", type: "password", autoComplete: "new-password", value: password, onChange: function(e) { setPassword(e.target.value); }, required: true }),
                  React.createElement(Input, { label: "Confirmar senha", type: "password", autoComplete: "new-password", value: confirmPassword, onChange: function(e) { setConfirmPassword(e.target.value); }, required: true })),
                React.createElement("label", { className: "flex items-start gap-3 rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-xs text-zinc-700" },
                  React.createElement("input", {
                    type: "checkbox",
                    checked: acceptedTerms,
                    onChange: function(e) { setAcceptedTerms(e.target.checked); },
                    required: true,
                    className: "mt-0.5 h-4 w-4 rounded border-zinc-300 text-violet-600 focus:ring-violet-500",
                  }),
                  React.createElement("span", null,
                    "Li e aceito os ",
                    React.createElement("a", { href: "/termos", target: "_blank", rel: "noreferrer", className: "underline hover:text-zinc-900" }, "Termos e Condições"),
                    " e a ",
                    React.createElement("a", { href: "/privacidade", target: "_blank", rel: "noreferrer", className: "underline hover:text-zinc-900" }, "Política de Privacidade"),
                    "."))
                ,
                TURNSTILE_SITE_KEY ? React.createElement("div", { ref: widgetRef, className: "flex justify-center" }) : null,
                error ? React.createElement("p", { className: "text-sm text-rose-400" }, error) : null,
                success ? React.createElement("p", { className: "text-sm text-emerald-400" }, success) : null,
                React.createElement(Button, { type: "submit", className: "w-full justify-center", disabled: loading }, loading ? "Criando conta..." : "Criar conta"),
                React.createElement("div", { className: "mt-2 text-center text-xs text-zinc-500" },
                  "Já tem conta? ",
                  React.createElement("button", {
                    type: "button",
                    onClick: function() { window.location.href = encryptedPath("login"); },
                    className: "text-zinc-200 underline-offset-2 hover:underline",
                  }, "Voltar para login"))))))));
}
