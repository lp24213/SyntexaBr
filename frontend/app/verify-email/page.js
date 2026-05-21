"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { AppShell } from "../../components/shell";
import { Card } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Button } from "../../components/ui/button";
import { getApiBase } from "../../lib/api";
import { encryptedPath } from "../../lib/routes";

var API_BASE = getApiBase();

export default function VerifyEmailPage() {
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  async function handleSubmit(ev) {
    ev.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);
    try {
      const resp = await fetch(API_BASE + "/v1/auth/verify-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, code }),
      });
      if (!resp.ok) {
        const txt = await resp.text();
        throw new Error(txt || "Falha ao verificar e-mail.");
      }
      setSuccess("E-mail verificado com sucesso. Você já pode fazer login.");
      setTimeout(function () { window.location.href = encryptedPath("login"); }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado ao verificar e-mail.");
    } finally {
      setLoading(false);
    }
  }

  return React.createElement(
    AppShell,
    null,
    React.createElement(
      "div",
      { className: "flex min-h-[calc(100vh-5rem)] items-start justify-center py-8" },
      React.createElement(
        motion.div,
        {
          className: "w-full max-w-md",
          initial: { opacity: 0, y: 12 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: 0.25 },
        },
        React.createElement(
          Card,
          {
            title: "Verificar e-mail",
            description: "Informe seu e-mail e o código que recebeu para ativar sua conta.",
          },
          React.createElement(
            "form",
            { onSubmit: handleSubmit, className: "space-y-5" },
            React.createElement(Input, {
              label: "E-mail",
              type: "email",
              autoComplete: "off",
              value: email,
              onChange: function (e) { setEmail(e.target.value); },
              required: true,
            }),
            React.createElement(Input, {
              label: "Código de verificação",
              type: "text",
              autoComplete: "off",
              inputMode: "numeric",
              value: code,
              onChange: function (e) { setCode(e.target.value); },
              required: true,
            }),
            error ? React.createElement("p", { className: "text-sm text-rose-400" }, error) : null,
            success ? React.createElement("p", { className: "text-sm text-emerald-400" }, success) : null,
            React.createElement(Button, { type: "submit", className: "w-full justify-center", disabled: loading }, loading ? "Verificando..." : "Verificar")
          )
        )
      )
    )
  );
}

