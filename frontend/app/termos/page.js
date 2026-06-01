"use client";

import React from "react";
import { AppShell } from "../../components/shell";
import { getClientLocale, t } from "../../lib/i18n";

export default function TermosPage() {
  const locale = getClientLocale();
  return React.createElement(
    AppShell,
    null,
    React.createElement(
      "main",
      { className: "py-10 text-zinc-800" },
    React.createElement("h1", { className: "text-2xl font-bold text-zinc-900" }, t("termsPageTitle", locale)),
    React.createElement(
      "p",
      { className: "mt-4 text-sm leading-relaxed" },
      t("termsContent1", locale)
    ),
    React.createElement(
      "p",
      { className: "mt-3 text-sm leading-relaxed" },
      t("termsContent2", locale)
    )
  )
  );
}
