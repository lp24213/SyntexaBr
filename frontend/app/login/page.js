"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { AppShell } from "../../components/shell";
import { Brand } from "../../components/brand";
import { Card } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Button } from "../../components/ui/button";
import { login, getMe } from "../../lib/api";
import { encryptedPath } from "../../lib/routes";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(ev) {
    ev.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const token = await login(email, password);
      window.localStorage.setItem("syntexa_token", token);
      // Busca papel do usuário para navegação role-based
      try {
        const me = await getMe(token);
        if (me) {
          window.localStorage.setItem("syntexa_role", me.role || "user");
          window.localStorage.setItem("syntexa_is_admin", me.is_admin ? "1" : "0");
          window.localStorage.setItem("syntexa_email", me.email || email);
          // Admin vai direto para o painel administrativo
          if (me.is_admin) {
            window.location.href = encryptedPath("admin");
            return;
          }
          // Professor/pesquisador vai para área educacional
          if (me.role === "teacher" || me.role === "researcher") {
            window.location.href = encryptedPath("educacao-professor");
            return;
          }
        }
      } catch (_) {}
      window.location.href = encryptedPath("chat");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao entrar. Tente novamente.");
    } finally {
      setLoading(false);
    }
  }

  const setEmailFromEvent = (ev) => setEmail(ev.target.value);
  const setPasswordFromEvent = (ev) => setPassword(ev.target.value);
  const goRegister = () => { window.location.href = encryptedPath("register"); };
  const goForgot = () => { window.location.href = encryptedPath("forgot-password"); };

  var linksDiv = React.createElement("div", { className: "mt-2 flex items-center justify-between text-xs text-zinc-500" },
    React.createElement("button", { type: "button", onClick: goRegister, className: "text-zinc-300 underline-offset-2 hover:text-zinc-100 hover:underline" }, "Criar conta"),
    React.createElement("button", { type: "button", onClick: goForgot, className: "text-zinc-300 underline-offset-2 hover:text-zinc-100 hover:underline" }, "Esqueci minha senha"));
  var formContent = React.createElement("form", { onSubmit: handleSubmit, className: "space-y-5" },
    React.createElement("div", { className: "space-y-3" },
      React.createElement(Input, { label: "E-mail", type: "email", autoComplete: "email", value: email, onChange: setEmailFromEvent, required: true }),
      React.createElement(Input, { label: "Senha", type: "password", autoComplete: "current-password", value: password, onChange: setPasswordFromEvent, required: true })),
    error ? React.createElement("p", { className: "text-sm text-red-400" }, error) : null,
    React.createElement(Button, { type: "submit", className: "w-full justify-center", disabled: loading }, loading ? "Entrando..." : "Entrar"),
    linksDiv);
  var cardContent = React.createElement(Card, { title: "Entrar", description: "Acesse sua conta para o chat e as ferramentas." }, formContent);
  var brandSpan = React.createElement("span", { className: "flex h-16 min-h-[64px] w-[240px] items-center justify-center" }, React.createElement(Brand, { className: "h-14 w-full max-w-[220px] object-contain" }));
  var innerMotion = React.createElement(motion.div, { className: "mb-10 flex justify-center", initial: { opacity: 0, scale: 0.96 }, animate: { opacity: 1, scale: 1 }, transition: { duration: 0.35, delay: 0.1 } }, brandSpan);
  var outerMotion = React.createElement(motion.div, { className: "w-full max-w-md", initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.4, ease: "easeOut" } }, innerMotion, cardContent);
  var wrap = React.createElement("div", { className: "flex min-h-[calc(100vh-6rem)] items-center justify-center py-8" }, outerMotion);
  return React.createElement(AppShell, null, wrap);
}
