"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { AppShell } from "../../components/shell";
import { encryptedPath } from "../../lib/routes";
import { Card } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Button } from "../../components/ui/button";

import { getApiBase } from "../../lib/api";
import { getClientLocale, t } from "../../lib/i18n";

var API_BASE = getApiBase();

export default function RegisterPage() {
  const locale = getClientLocale();
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
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  async function handleSubmit(ev) {
    ev.preventDefault();
    setError(null);
    setSuccess(null);
    if (password !== confirmPassword) {
      setError(t("passwordsMismatch", locale));
      return;
    }
    if (!acceptedTerms) {
      setError(t("termsNotAccepted", locale));
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
        throw new Error(txt || t("accountCreationFailed", locale));
      }
      try { window.localStorage.setItem("syntexa_pending_email", email); } catch {}
      setSuccess(t("accountCreatedVerificationSent", locale));
      setTimeout(function () { window.location.href = encryptedPath("activate-signup"); }, 1200);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("unexpectedAccountError", locale));
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
    React.createElement("div", { className: "flex min-h-[calc(100vh-5rem)] items-start justify-center py-8" },
      React.createElement(motion.div, {
        className: "w-full max-w-md",
        initial: { opacity: 0, y: 12 },
        animate: { opacity: 1, y: 0 },
        transition: { duration: 0.25 },
      },
        React.createElement(Card, { title: t("createAccountTitle", locale), description: t("createAccountDescription", locale) },
          React.createElement("form", { onSubmit: handleSubmit, className: "space-y-5" },
            React.createElement("div", { className: "space-y-3" },
              React.createElement(Input, { label: t("fullNameLabel", locale), value: name, onChange: onName, required: true }),
              React.createElement(Input, { label: t("emailLabel", locale), type: "email", autoComplete: "email", value: email, onChange: onEmail, required: true }),
              React.createElement(Input, { label: t("documentLabel", locale), value: documentId, onChange: function (e) { setDocumentId(e.target.value); }, required: true }),
              React.createElement(Input, { label: t("cepLabel", locale), value: cep, onChange: function (e) { setCep(e.target.value); }, required: true }),
              React.createElement(Input, { label: t("stateLabel", locale), value: state, onChange: function (e) { setState(e.target.value); }, required: true }),
              React.createElement(Input, { label: t("cityLabel", locale), value: city, onChange: function (e) { setCity(e.target.value); }, required: true }),
              React.createElement(Input, { label: t("addressLabel", locale), value: addressLine, onChange: function (e) { setAddressLine(e.target.value); }, required: true }),
              React.createElement(Input, { label: t("numberLabel", locale), value: addressNumber, onChange: function (e) { setAddressNumber(e.target.value); }, required: true }),
              React.createElement(Input, { label: t("complementLabel", locale), value: addressComplement, onChange: function (e) { setAddressComplement(e.target.value); } }),
              React.createElement(Input, { label: t("passwordLabel", locale), type: "password", autoComplete: "new-password", value: password, onChange: onPassword, required: true }),
              React.createElement(Input, { label: t("confirmPasswordLabel", locale), type: "password", autoComplete: "new-password", value: confirmPassword, onChange: onConfirm, required: true })),
            React.createElement("label", { className: "flex items-start gap-3 rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-xs text-zinc-700" },
              React.createElement("input", {
                type: "checkbox",
                checked: acceptedTerms,
                onChange: function (e) { setAcceptedTerms(e.target.checked); },
                required: true,
                className: "mt-0.5 h-4 w-4 rounded border-zinc-300 text-violet-600 focus:ring-violet-500",
              }),
              React.createElement("span", null,
                t("termsAcceptanceText", locale),
                " ")
            ),
            error ? React.createElement("p", { className: "text-sm text-rose-400" }, error) : null,
            success ? React.createElement("p", { className: "text-sm text-emerald-400" }, success) : null,
            React.createElement(Button, { type: "submit", className: "w-full justify-center", disabled: loading }, loading ? t("creatingAccount", locale) : t("registerButton", locale)),
            React.createElement("div", { className: "mt-2 text-center text-xs text-zinc-500" },
              t("alreadyHaveAccount", locale),
              " ",
              React.createElement("button", { type: "button", onClick: goLogin, className: "text-zinc-200 underline-offset-2 hover:underline" }, t("backToLogin", locale))))))));
}
