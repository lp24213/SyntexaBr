"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AppShell } from "../../components/shell";
import { Brand } from "../../components/brand";
import { Card } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Button } from "../../components/ui/button";
import { login, getMe, verifyTwoFactor, githubLoginUrl } from "../../lib/api";
import { encryptedPath } from "../../lib/routes";

const TURNSTILE_SITE_KEY =
  (typeof process !== "undefined" && process.env && process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY) ||
  "";

function useTurnstile(siteKey) {
  const [token, setToken] = useState("");
  const [ready, setReady] = useState(false);
  const widgetRef = React.useRef(null);

  React.useEffect(function () {
    if (!siteKey) return;
    if (typeof window === "undefined") return;
    if (window.turnstile) {
      setReady(true);
      return;
    }
    const existing = document.querySelector('script[src*="challenges.cloudflare.com/turnstile/v0/api.js"]');
    if (!existing) {
      const script = document.createElement("script");
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
    const id = window.turnstile.render(widgetRef.current, {
      sitekey: siteKey,
      callback: function (tok) { setToken(tok); },
      "expired-callback": function () { setToken(""); },
      "error-callback": function () { setToken(""); },
    });
    return function () {
      if (window.turnstile && id) window.turnstile.remove(id);
    };
  }, [ready, siteKey]);

  return { token, widgetRef };
}

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [twoFactorToken, setTwoFactorToken] = useState("");
  const [twoFactorCode, setTwoFactorCode] = useState("");
  const { token: turnstileToken, widgetRef } = useTurnstile(TURNSTILE_SITE_KEY);

  async function finishLogin(accessToken, fallbackEmail, refreshToken) {
    window.localStorage.setItem("syntexa_token", accessToken);
    if (refreshToken) window.localStorage.setItem("syntexa_refresh_token", refreshToken);
    try {
      const me = await getMe(accessToken);
      if (me) {
        window.localStorage.setItem("syntexa_role", me.role || "user");
        window.localStorage.setItem("syntexa_is_admin", me.is_admin ? "1" : "0");
        window.localStorage.setItem("syntexa_email", me.email || fallbackEmail || "");
        if (me.is_admin) {
          window.location.href = encryptedPath("admin");
          return;
        }
        if (me.role === "teacher" || me.role === "researcher") {
          window.location.href = encryptedPath("educacao-professor");
          return;
        }
      }
    } catch (_) {}
    window.location.href = encryptedPath("chat");
  }

  useEffect(function () {
    if (typeof window === "undefined") return;
    try {
      const url = new URL(window.location.href);
      const ghToken = (url.searchParams.get("gh_token") || "").trim();
      const ghRefresh = (url.searchParams.get("gh_refresh") || "").trim();
      const twoToken = (url.searchParams.get("two_factor_token") || "").trim();
      const ghError = (url.searchParams.get("gh_error") || "").trim();
      if (ghError === "no_email") {
        setError("Entre com e-mail e senha ou deixe um e-mail visível na sua conta do GitHub.");
      } else if (ghError === "oauth" || ghError) {
        setError("GitHub não respondeu de primeira — tente de novo.");
      }
      if (ghError) {
        try {
          url.searchParams.delete("gh_error");
          const qs = url.searchParams.toString();
          window.history.replaceState({}, "", url.pathname + (qs ? "?" + qs : "") + url.hash);
        } catch (_) {}
      }
      if (twoToken) {
        setTwoFactorToken(twoToken);
      }
      if (ghToken) {
        finishLogin(ghToken, email, ghRefresh || undefined);
      }
    } catch (_) {}
  }, []);

  async function handleSubmit(ev) {
    ev.preventDefault();
    setError(null);
    if (TURNSTILE_SITE_KEY && !turnstileToken) {
      setError("Aguarde a verificação de segurança carregar.");
      return;
    }
    setLoading(true);
    try {
      const data = await login(email, password, turnstileToken);
      if (data && data.requires_2fa && data.two_factor_token) {
        setTwoFactorToken(String(data.two_factor_token));
        setError(null);
        return;
      }
      if (data && data.access_token) {
        await finishLogin(data.access_token, email, data.refresh_token);
        return;
      }
      throw new Error("Resposta de login inválida.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao entrar. Tente novamente.");
    } finally {
      setLoading(false);
    }
  }

  async function handleTwoFactorSubmit(ev) {
    ev.preventDefault();
    if (!twoFactorToken || !twoFactorCode.trim()) return;
    setError(null);
    setLoading(true);
    try {
      const data = await verifyTwoFactor(twoFactorToken, twoFactorCode.trim());
      if (data && data.access_token) {
        await finishLogin(data.access_token, email, data.refresh_token);
        return;
      }
      throw new Error("Não foi possível validar o código 2FA.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Código 2FA inválido.");
    } finally {
      setLoading(false);
    }
  }

  const setEmailFromEvent = (ev) => setEmail(ev.target.value);
  const setPasswordFromEvent = (ev) => setPassword(ev.target.value);
  const setTwoFactorCodeFromEvent = (ev) => setTwoFactorCode(ev.target.value);
  const goRegister = () => { window.location.href = encryptedPath("register"); };
  const goForgot = () => { window.location.href = encryptedPath("forgot-password"); };
  const goGithub = () => { window.location.href = githubLoginUrl(); };

  var linksDiv = React.createElement("div", { className: "mt-2 flex items-center justify-between text-xs text-zinc-500" },
    React.createElement("button", { type: "button", onClick: goRegister, className: "text-zinc-600 underline-offset-2 hover:text-zinc-900 hover:underline" }, "Criar conta"),
    React.createElement("button", { type: "button", onClick: goForgot, className: "text-zinc-600 underline-offset-2 hover:text-zinc-900 hover:underline" }, "Esqueci minha senha"));
  var formContent = twoFactorToken
    ? React.createElement("form", { onSubmit: handleTwoFactorSubmit, className: "space-y-5" },
      React.createElement("p", { className: "text-xs text-zinc-500" }, "Digite o código do autenticador (2FA) para concluir o login."),
      React.createElement(Input, { label: "Código 2FA", type: "text", autoComplete: "one-time-code", value: twoFactorCode, onChange: setTwoFactorCodeFromEvent, required: true }),
      error ? React.createElement("p", { className: "text-sm text-red-400" }, error) : null,
      React.createElement(Button, { type: "submit", className: "w-full justify-center", disabled: loading }, loading ? "Validando..." : "Validar 2FA"),
      React.createElement("button", {
        type: "button",
        onClick: function () { setTwoFactorToken(""); setTwoFactorCode(""); setError(null); },
        className: "w-full rounded-xl border border-zinc-200 bg-white px-4 py-2 text-sm text-zinc-700 hover:bg-zinc-50"
      }, "Voltar para login"))
    : React.createElement("form", { onSubmit: handleSubmit, className: "space-y-5" },
      React.createElement("div", { className: "space-y-3" },
        React.createElement(Input, { label: "E-mail", type: "email", autoComplete: "email", value: email, onChange: setEmailFromEvent, required: true }),
        React.createElement(Input, { label: "Senha", type: "password", autoComplete: "current-password", value: password, onChange: setPasswordFromEvent, required: true })),
      TURNSTILE_SITE_KEY ? React.createElement("div", { ref: widgetRef, className: "flex justify-center" }) : null,
      error ? React.createElement("p", { className: "text-sm text-red-400" }, error) : null,
      React.createElement(Button, { type: "submit", className: "w-full justify-center", disabled: loading }, loading ? "Entrando..." : "Entrar"),
      React.createElement("button", {
        type: "button",
        onClick: goGithub,
        className: "w-full rounded-xl border border-zinc-200 bg-white px-4 py-2 text-sm text-zinc-700 hover:bg-zinc-50"
      }, "Entrar com GitHub"),
      linksDiv);
  var cardContent = React.createElement(Card, { title: "Entrar", description: "Acesse sua conta para o chat e as ferramentas." }, formContent);
  var brandSpan = React.createElement("span", { className: "flex h-16 min-h-[64px] w-[240px] items-center justify-center" }, React.createElement(Brand, { className: "h-14 w-full max-w-[220px] object-contain" }));
  var innerMotion = React.createElement(motion.div, { className: "mb-10 flex justify-center", initial: { opacity: 0, scale: 0.96 }, animate: { opacity: 1, scale: 1 }, transition: { duration: 0.35, delay: 0.1 } }, brandSpan);
  var outerMotion = React.createElement(motion.div, { className: "w-full max-w-md", initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.4, ease: "easeOut" } }, innerMotion, cardContent);
  var wrap = React.createElement("div", { className: "flex min-h-[calc(100vh-6rem)] items-start justify-center py-8" }, outerMotion);
  return React.createElement(AppShell, null, wrap);
}
