"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AppShell } from "../../components/shell";
import { Brand } from "../../components/brand";
import { Card } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Button } from "../../components/ui/button";
import { TurnstileWidget } from "../../components/TurnstileWidget";
import { login, getMe, verifyTwoFactor, githubLoginUrl } from "../../lib/api";
import { encryptedPath } from "../../lib/routes";
import { getClientLocale, t } from "../../lib/i18n";

const TURNSTILE_SITE_KEY = "0x4AAAAAADXPQoicsnfeZhcl";

export default function LoginPage() {
  const locale = getClientLocale();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [twoFactorToken, setTwoFactorToken] = useState("");
  const [twoFactorCode, setTwoFactorCode] = useState("");
  const [turnstileToken, setTurnstileToken] = useState("");

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
        setError(t("githubNoEmailError", locale));
      } else if (ghError === "oauth" || ghError) {
        setError(t("githubOAuthError", locale));
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
      setError(t("turnstileWaitMessage", locale));
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
      throw new Error(t("invalidLoginResponse", locale));
    } catch (err) {
      setError(err instanceof Error ? err.message : t("loginFailed", locale));
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
      throw new Error(t("twoFaValidationFailed", locale));
    } catch (err) {
      setError(err instanceof Error ? err.message : t("invalidTwoFaCode", locale));
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
    React.createElement("button", { type: "button", onClick: goRegister, className: "text-zinc-600 underline-offset-2 hover:text-zinc-900 hover:underline" }, t("createAccountLink", locale)),
    React.createElement("button", { type: "button", onClick: goForgot, className: "text-zinc-600 underline-offset-2 hover:text-zinc-900 hover:underline" }, t("forgotPassword", locale)));
  var formContent = twoFactorToken
    ? React.createElement("form", { onSubmit: handleTwoFactorSubmit, className: "space-y-5" },
      React.createElement("p", { className: "text-xs text-zinc-500" }, t("twoFaPrompt", locale)),
      React.createElement(Input, { label: t("twoFaCodeLabel", locale), type: "text", autoComplete: "one-time-code", value: twoFactorCode, onChange: setTwoFactorCodeFromEvent, required: true }),
      error ? React.createElement("p", { className: "text-sm text-red-400" }, error) : null,
      React.createElement(Button, { type: "submit", className: "w-full justify-center", disabled: loading }, loading ? t("validatingTwoFa", locale) : t("validateTwoFaButton", locale)),
      React.createElement("button", {
        type: "button",
        onClick: function () { setTwoFactorToken(""); setTwoFactorCode(""); setError(null); },
        className: "w-full rounded-xl border border-zinc-200 bg-white px-4 py-2 text-sm text-zinc-700 hover:bg-zinc-50"
      }, t("backToLogin", locale)))
    : React.createElement("form", { onSubmit: handleSubmit, className: "space-y-5" },
      React.createElement("div", { className: "space-y-3" },
        React.createElement(Input, { label: t("emailLabel", locale), type: "email", autoComplete: "email", value: email, onChange: setEmailFromEvent, required: true }),
        React.createElement(Input, { label: t("passwordLabel", locale), type: "password", autoComplete: "current-password", value: password, onChange: setPasswordFromEvent, required: true })),
      TURNSTILE_SITE_KEY ? React.createElement(TurnstileWidget, { 
        siteKey: TURNSTILE_SITE_KEY,
        onTokenReceived: setTurnstileToken,
        onError: (err) => setError(`${t("securityErrorPrefix", locale)} ${err}`),
        theme: "light",
        className: "my-3"
      }) : null,
      error ? React.createElement("p", { className: "text-sm text-red-400" }, error) : null,
      React.createElement(Button, { type: "submit", className: "w-full justify-center", disabled: loading }, loading ? t("enteringStatus", locale) : t("loginButton", locale)),
      React.createElement("button", {
        type: "button",
        onClick: goGithub,
        className: "w-full rounded-xl border border-zinc-200 bg-white px-4 py-2 text-sm text-zinc-700 hover:bg-zinc-50"
      }, t("loginWithGithub", locale)),
      linksDiv);
  var cardContent = React.createElement(Card, { title: t("loginTitle", locale), description: t("loginDescription", locale) }, formContent);
  var brandSpan = React.createElement("span", { className: "flex h-16 min-h-[64px] w-[240px] items-center justify-center" }, React.createElement(Brand, { className: "h-14 w-full max-w-[220px] object-contain" }));
  var innerMotion = React.createElement(motion.div, { className: "mb-10 flex justify-center", initial: { opacity: 0, scale: 0.96 }, animate: { opacity: 1, scale: 1 }, transition: { duration: 0.35, delay: 0.1 } }, brandSpan);
  var outerMotion = React.createElement(motion.div, { className: "w-full max-w-md", initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.4, ease: "easeOut" } }, innerMotion, cardContent);
  var wrap = React.createElement("div", { className: "flex min-h-[calc(100vh-6rem)] items-start justify-center py-8" }, outerMotion);
  return React.createElement(AppShell, null, wrap);
}
