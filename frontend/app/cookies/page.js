"use client";

import React from "react";
import { AppShell } from "../../components/shell";
import { t } from "../../lib/i18n";
import { useLanguage } from "../../components/language-provider";

function CookiesContent() {
  const { locale } = useLanguage();
  return React.createElement(
    "main",
    { className: "py-10 text-zinc-800" },
    React.createElement("h1", { className: "text-2xl font-bold text-zinc-900" }, t('cookiesPolicyTitle', locale)),
    React.createElement(
      "p",
      { className: "mt-4 text-sm leading-relaxed" },
      t('cookiesPolicyContent1', locale)
    ),
    React.createElement(
      "p",
      { className: "mt-3 text-sm leading-relaxed" },
      t('cookiesPolicyContent2', locale)
    )
  );
}

export default function CookiesPage() {
  return React.createElement(
    AppShell,
    null,
    React.createElement(CookiesContent)
  );
}
