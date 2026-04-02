"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { AppShell } from "../../components/shell";
import { Card } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Button } from "../../components/ui/button";
import { encryptedPath } from "../../lib/routes";
import { getApiBase } from "../../lib/api";

var API_BASE = getApiBase();

export default function RecuperarSenhaPage() {
  const [step, setStep] = useState(1);
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  async function handleRequest(e) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);
    try {
      await fetch(API_BASE + "/v1/auth/request-password-reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      try { window.localStorage.setItem("syntexa_pending_email", email); } catch {}
      setSuccess("Se o e-mail existir, um código de redefinição será enviado.");
      setTimeout(function () { window.location.href = encryptedPath("activate-reset"); }, 1200);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao solicitar redefinição.");
    } finally {
      setLoading(false);
    }
  }

  async function handleReset(e) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);
    try {
      const resp = await fetch(API_BASE + "/v1/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, code, new_password: newPassword }),
      });
      if (!resp.ok) {
        const txt = await resp.text();
        throw new Error(txt || "Falha ao redefinir senha.");
      }
      setSuccess("Senha redefinida com sucesso. Você já pode fazer login.");
      setTimeout(function () { window.location.href = encryptedPath("login"); }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao redefinir senha.");
    } finally {
      setLoading(false);
    }
  }

  return React.createElement(
    AppShell,
    null,
    React.createElement(
      "div",
      { className: "flex min-h-[calc(100vh-5rem)] items-center justify-center" },
      React.createElement(
        motion.div,
        { className: "w-full max-w-md", initial: { opacity: 0, y: 12 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.25 } },
        React.createElement(
          Card,
          { title: "Recuperar senha", description: "Use seu e-mail e o código recebido para redefinir sua senha." },
          step === 1
            ? React.createElement(
                "form",
                { onSubmit: handleRequest, className: "space-y-5" },
                React.createElement(Input, { label: "E-mail", type: "email", value: email, onChange: (e) => setEmail(e.target.value), required: true }),
                error ? React.createElement("p", { className: "text-sm text-rose-400" }, error) : null,
                success ? React.createElement("p", { className: "text-sm text-emerald-400" }, success) : null,
                React.createElement(Button, { type: "submit", className: "w-full justify-center", disabled: loading }, loading ? "Enviando..." : "Enviar código de redefinição")
              )
            : React.createElement(
                "form",
                { onSubmit: handleReset, className: "space-y-5" },
                React.createElement(Input, { label: "E-mail", type: "email", value: email, onChange: (e) => setEmail(e.target.value), required: true }),
                React.createElement(Input, { label: "Código recebido", value: code, onChange: (e) => setCode(e.target.value), required: true }),
                React.createElement(Input, { label: "Nova senha", type: "password", value: newPassword, onChange: (e) => setNewPassword(e.target.value), required: true }),
                error ? React.createElement("p", { className: "text-sm text-rose-400" }, error) : null,
                success ? React.createElement("p", { className: "text-sm text-emerald-400" }, success) : null,
                React.createElement(Button, { type: "submit", className: "w-full justify-center", disabled: loading }, loading ? "Redefinindo..." : "Redefinir senha")
              ),
          React.createElement(
            "div",
            { className: "mt-2 text-center text-xs text-zinc-500" },
            "Lembrou da senha? ",
            React.createElement("button", { type: "button", onClick: () => { window.location.href = encryptedPath("login"); }, className: "text-zinc-200 underline-offset-2 hover:underline" }, "Voltar para login")
          )
        )
      )
    )
  );
}
