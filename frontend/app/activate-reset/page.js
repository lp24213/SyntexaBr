"use client";

import React, { useState } from "react";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { AppShell } from "../../components/shell";
import { Card } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Button } from "../../components/ui/button";
import { encryptedPath } from "../../lib/routes";
import { getApiBase } from "../../lib/api";

var API_BASE = getApiBase();

export default function ActivateResetPage() {
  const pathname = usePathname();
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");

  React.useEffect(function () {
    try {
      var saved = window.localStorage.getItem("syntexa_pending_email");
      if (saved) setEmail(saved);
    } catch {}
  }, []);

  React.useEffect(function () {
    var path = (pathname || "").replace(/\/+$/, "");
    var target = (encryptedPath("activate-reset") || "").replace(/\/+$/, "");
    if (path === "/activate-reset" && target && target !== path) {
      window.location.replace(target);
    }
  }, [pathname]);
  const [newPassword, setNewPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    if (newPassword !== confirm) {
      setError("As senhas não coincidem.");
      return;
    }
    setLoading(true);
    try {
      const resp = await fetch(API_BASE + "/v1/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          code,
          new_password: newPassword,
        }),
      });
      if (!resp.ok) {
        const txt = await resp.text();
        throw new Error(txt || "Falha ao redefinir senha.");
      }
      setSuccess("Senha redefinida com sucesso. Você já pode fazer login.");
      setTimeout(function () {
        window.location.href = encryptedPath("login");
      }, 1500);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Erro ao redefinir senha."
      );
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
        {
          className: "w-full max-w-md",
          initial: { opacity: 0, y: 12 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: 0.25 },
        },
        React.createElement(
          Card,
          {
            title: "Ativar redefinição de senha",
            description: "Digite o código recebido e a nova senha para concluir a recuperação.",
          },
          React.createElement(
            "form",
            { onSubmit: handleSubmit, className: "space-y-5" },
            React.createElement(Input, {
              label: "Código recebido",
              value: code,
              onChange: function (e) {
                setCode(e.target.value);
              },
              required: true,
            }),
            React.createElement(Input, {
              label: "Nova senha",
              type: "password",
              value: newPassword,
              onChange: function (e) {
                setNewPassword(e.target.value);
              },
              required: true,
            }),
            React.createElement(Input, {
              label: "Confirmar nova senha",
              type: "password",
              value: confirm,
              onChange: function (e) {
                setConfirm(e.target.value);
              },
              required: true,
            }),
            error
              ? React.createElement(
                  "p",
                  { className: "text-sm text-rose-400" },
                  error
                )
              : null,
            success
              ? React.createElement(
                  "p",
                  { className: "text-sm text-emerald-400" },
                  success
                )
              : null,
            React.createElement(
              Button,
              {
                type: "submit",
                className: "w-full justify-center",
                disabled: loading,
              },
              loading ? "Redefinindo..." : "Redefinir senha"
            )
          )
        )
      )
    )
  );
}

