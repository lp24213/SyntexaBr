"use client";

import React, { useEffect, useState } from "react";
import { AppShell } from "../../components/shell";
import { Card } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { encryptedPath } from "../../lib/routes";
import { getMe, updateMe } from "../../lib/api";

export default function PerfilPage() {
  const [token, setToken] = useState(null);
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [username, setUsername] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [documentId, setDocumentId] = useState("");
  const [cep, setCep] = useState("");
  const [stateUf, setStateUf] = useState("");
  const [city, setCity] = useState("");
  const [addressLine, setAddressLine] = useState("");
  const [addressNumber, setAddressNumber] = useState("");
  const [addressComplement, setAddressComplement] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState("");

  useEffect(() => {
    (async function () {
      try {
        const t = window.localStorage.getItem("syntexa_token");
        if (!t) {
          window.location.href = encryptedPath("login");
          return;
        }
        setToken(t);
        setIsAdmin(window.localStorage.getItem("syntexa_is_admin") === "1");
        const me = await getMe(t);
        if (me) {
          setEmail(String(me.email || ""));
          setFullName(String(me.full_name || ""));
          setUsername(String(me.username || ""));
          setAvatarUrl(String(me.avatar_url || ""));
          setDocumentId(String(me.document || ""));
          setCep(String(me.cep || ""));
          setStateUf(String(me.state || ""));
          setCity(String(me.city || ""));
          setAddressLine(String(me.address_line || ""));
          setAddressNumber(String(me.address_number || ""));
          setAddressComplement(String(me.address_complement || ""));
        }
      } catch {
        window.location.href = encryptedPath("login");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  function onPickAvatar(ev) {
    const file = ev.target.files && ev.target.files[0];
    if (!file) return;
    if (!/^image\//i.test(file.type)) {
      setStatus("Selecione um ficheiro de imagem.");
      return;
    }
    const reader = new FileReader();
    reader.onload = function () {
      setAvatarUrl(String(reader.result || ""));
    };
    reader.readAsDataURL(file);
  }

  async function saveProfile() {
    if (!token) return;
    setSaving(true);
    setStatus("");
    try {
      const out = await updateMe(token, {
        full_name: fullName,
        username: username,
        avatar_url: avatarUrl,
        document: documentId,
        cep: cep,
        state: stateUf,
        city: city,
        address_line: addressLine,
        address_number: addressNumber,
        address_complement: addressComplement,
      });
      setFullName(String(out.full_name || ""));
      setUsername(String(out.username || ""));
      setAvatarUrl(String(out.avatar_url || ""));
      setDocumentId(String(out.document || ""));
      setCep(String(out.cep || ""));
      setStateUf(String(out.state || ""));
      setCity(String(out.city || ""));
      setAddressLine(String(out.address_line || ""));
      setAddressNumber(String(out.address_number || ""));
      setAddressComplement(String(out.address_complement || ""));
      setStatus("Perfil atualizado com sucesso.");
    } catch (e) {
      setStatus((e && e.message) || "Não foi possível salvar perfil.");
    } finally {
      setSaving(false);
    }
  }

  return React.createElement(
    AppShell,
    null,
    React.createElement(
      "div",
      { className: "mx-auto flex max-w-3xl flex-col gap-6 py-10" },
      React.createElement(
        Card,
        {
          title: "Perfil do usuário",
          description: "Edite seus dados de conta e personalize sua identificação na Syntexa.",
        },
        loading
          ? React.createElement("p", { className: "text-sm text-zinc-500" }, "Carregando perfil...")
          : React.createElement(
              "div",
              { className: "space-y-4" },
              React.createElement("p", { className: "text-xs text-zinc-500" }, "E-mail: ", React.createElement("strong", null, email || "-")),
              React.createElement(
                "div",
                { className: "flex items-center gap-4" },
                avatarUrl
                  ? React.createElement("img", {
                      src: avatarUrl,
                      alt: "Avatar",
                      className: "h-16 w-16 rounded-full border border-zinc-200 object-cover",
                    })
                  : React.createElement("div", { className: "flex h-16 w-16 items-center justify-center rounded-full border border-zinc-200 bg-zinc-100 text-xs text-zinc-500" }, "Sem foto"),
                React.createElement("input", {
                  type: "file",
                  accept: "image/*",
                  onChange: onPickAvatar,
                  className: "text-xs",
                })
              ),
              React.createElement("label", { className: "block text-xs font-medium text-zinc-600" }, "Nome"),
              React.createElement("input", {
                value: fullName,
                onChange: function (e) { setFullName(e.target.value); },
                className: "w-full rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-800",
                placeholder: "Seu nome",
              }),
              React.createElement("label", { className: "block text-xs font-medium text-zinc-600" }, "Username"),
              React.createElement("input", {
                value: username,
                onChange: function (e) { setUsername(e.target.value); },
                className: "w-full rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-800",
                placeholder: "usuario.exemplo",
              }),
              React.createElement("label", { className: "block text-xs font-medium text-zinc-600" }, "CPF/CNPJ"),
              React.createElement("input", {
                value: documentId,
                onChange: function (e) { setDocumentId(e.target.value); },
                className: "w-full rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-800",
                placeholder: "000.000.000-00 ou 00.000.000/0000-00",
              }),
              React.createElement("div", { className: "grid grid-cols-1 gap-3 sm:grid-cols-3" },
                React.createElement("div", null,
                  React.createElement("label", { className: "mb-1 block text-xs font-medium text-zinc-600" }, "CEP"),
                  React.createElement("input", {
                    value: cep,
                    onChange: function (e) { setCep(e.target.value); },
                    className: "w-full rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-800",
                    placeholder: "00000-000",
                  })
                ),
                React.createElement("div", null,
                  React.createElement("label", { className: "mb-1 block text-xs font-medium text-zinc-600" }, "Estado"),
                  React.createElement("input", {
                    value: stateUf,
                    onChange: function (e) { setStateUf(e.target.value); },
                    className: "w-full rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-800",
                    placeholder: "SP",
                  })
                ),
                React.createElement("div", null,
                  React.createElement("label", { className: "mb-1 block text-xs font-medium text-zinc-600" }, "Cidade"),
                  React.createElement("input", {
                    value: city,
                    onChange: function (e) { setCity(e.target.value); },
                    className: "w-full rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-800",
                    placeholder: "São Paulo",
                  })
                )
              ),
              React.createElement("label", { className: "block text-xs font-medium text-zinc-600" }, "Endereço"),
              React.createElement("input", {
                value: addressLine,
                onChange: function (e) { setAddressLine(e.target.value); },
                className: "w-full rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-800",
                placeholder: "Rua / Avenida",
              }),
              React.createElement("div", { className: "grid grid-cols-1 gap-3 sm:grid-cols-2" },
                React.createElement("div", null,
                  React.createElement("label", { className: "mb-1 block text-xs font-medium text-zinc-600" }, "Número"),
                  React.createElement("input", {
                    value: addressNumber,
                    onChange: function (e) { setAddressNumber(e.target.value); },
                    className: "w-full rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-800",
                    placeholder: "123",
                  })
                ),
                React.createElement("div", null,
                  React.createElement("label", { className: "mb-1 block text-xs font-medium text-zinc-600" }, "Complemento"),
                  React.createElement("input", {
                    value: addressComplement,
                    onChange: function (e) { setAddressComplement(e.target.value); },
                    className: "w-full rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-800",
                    placeholder: "Apto, bloco, referência",
                  })
                )
              ),
              status ? React.createElement("p", { className: "text-xs text-zinc-600" }, status) : null,
              React.createElement(Button, { type: "button", onClick: saveProfile, disabled: saving || loading }, saving ? "Salvando..." : "Salvar perfil")
            )
      ),
      React.createElement(
        Card,
        {
          title: "Conta e configurações",
          description: "Acessos centralizados do seu painel de conta.",
        },
        React.createElement(
          "div",
          { className: "flex flex-wrap gap-2" },
          React.createElement("a", { href: encryptedPath("config"), className: "rounded-lg border border-zinc-200 bg-white px-3 py-2 text-xs text-zinc-700 hover:bg-zinc-50" }, "Configurações"),
          React.createElement("a", { href: encryptedPath("plans"), className: "rounded-lg border border-zinc-200 bg-white px-3 py-2 text-xs text-zinc-700 hover:bg-zinc-50" }, "Planos"),
          isAdmin ? React.createElement("a", { href: encryptedPath("download"), className: "rounded-lg border border-zinc-200 bg-white px-3 py-2 text-xs text-zinc-700 hover:bg-zinc-50" }, "Sistema Offline") : null,
          isAdmin ? React.createElement("a", { href: encryptedPath("admin-integrations"), className: "rounded-lg border border-zinc-200 bg-white px-3 py-2 text-xs text-zinc-700 hover:bg-zinc-50" }, "API Tokens") : null
        )
      )
    )
  );
}
