"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { AppShell } from "../../components/shell";
import { encryptedPath } from "../../lib/routes";
import { Card } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Button } from "../../components/ui/button";

import { getApiBase } from "../../lib/api";

var API_BASE = getApiBase();

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [documentId, setDocumentId] = useState("");
  const [cep, setCep] = useState("");
  const [state, setState] = useState("");
  const [city, setCity] = useState("");
  const [addressLine, setAddressLine] = useState("");
  const [addressNumber, setAddressNumber] = useState("");
  const [addressComplement, setAddressComplement] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  async function handleSubmit(ev) {
    ev.preventDefault();
    setError(null);
    setSuccess(null);
    if (password !== confirmPassword) {
      setError("As senhas não coincidem.");
      return;
    }
    setLoading(true);
    try {
      const resp = await fetch(API_BASE + "/v1/auth/public-register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          full_name: name,
          password,
          document: documentId,
          cep,
          state,
          city,
          address_line: addressLine,
          address_number: addressNumber,
          address_complement: addressComplement || null,
        }),
      });
      if (!resp.ok) {
        const txt = await resp.text();
        throw new Error(txt || "Falha ao criar conta.");
      }
      try { window.localStorage.setItem("syntexa_pending_email", email); } catch {}
      setSuccess("Conta criada. Enviamos um código de verificação para seu e-mail.");
      setTimeout(function () { window.location.href = encryptedPath("activate-signup"); }, 1200);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado ao criar conta.");
    } finally {
      setLoading(false);
    }
  }

  const onName = function (ev) { setName(ev.target.value); };
  const onEmail = function (ev) { setEmail(ev.target.value); };
  const onPassword = function (ev) { setPassword(ev.target.value); };
  const onConfirm = function (ev) { setConfirmPassword(ev.target.value); };
  const goLogin = function () { window.location.href = encryptedPath("login"); };

  return React.createElement(
    AppShell,
    null,
    React.createElement("div", { className: "flex min-h-[calc(100vh-5rem)] items-center justify-center" },
      React.createElement(motion.div, {
        className: "w-full max-w-md",
        initial: { opacity: 0, y: 12 },
        animate: { opacity: 1, y: 0 },
        transition: { duration: 0.25 },
      },
        React.createElement(Card, { title: "Criar conta", description: "Comece a usar a plataforma de IA Syntexa em poucos segundos." },
          React.createElement("form", { onSubmit: handleSubmit, className: "space-y-5" },
            React.createElement("div", { className: "space-y-3" },
              React.createElement(Input, { label: "Nome completo", value: name, onChange: onName, required: true }),
              React.createElement(Input, { label: "E-mail", type: "email", autoComplete: "email", value: email, onChange: onEmail, required: true }),
              React.createElement(Input, { label: "CPF/CNPJ", value: documentId, onChange: function (e) { setDocumentId(e.target.value); }, required: true }),
              React.createElement(Input, { label: "CEP", value: cep, onChange: function (e) { setCep(e.target.value); }, required: true }),
              React.createElement(Input, { label: "Estado (UF)", value: state, onChange: function (e) { setState(e.target.value); }, required: true }),
              React.createElement(Input, { label: "Cidade", value: city, onChange: function (e) { setCity(e.target.value); }, required: true }),
              React.createElement(Input, { label: "Endereço (rua/avenida)", value: addressLine, onChange: function (e) { setAddressLine(e.target.value); }, required: true }),
              React.createElement(Input, { label: "Número", value: addressNumber, onChange: function (e) { setAddressNumber(e.target.value); }, required: true }),
              React.createElement(Input, { label: "Complemento", value: addressComplement, onChange: function (e) { setAddressComplement(e.target.value); } }),
              React.createElement(Input, { label: "Senha", type: "password", autoComplete: "new-password", value: password, onChange: onPassword, required: true }),
              React.createElement(Input, { label: "Confirmar senha", type: "password", autoComplete: "new-password", value: confirmPassword, onChange: onConfirm, required: true })),
            error ? React.createElement("p", { className: "text-sm text-rose-400" }, error) : null,
            success ? React.createElement("p", { className: "text-sm text-emerald-400" }, success) : null,
            React.createElement(Button, { type: "submit", className: "w-full justify-center", disabled: loading }, loading ? "Criando conta..." : "Criar conta"),
            React.createElement("div", { className: "mt-2 text-center text-xs text-zinc-500" },
              "Já tem conta? ",
              React.createElement("button", { type: "button", onClick: goLogin, className: "text-zinc-200 underline-offset-2 hover:underline" }, "Voltar para login")))))));
}
