"use client";

import React from "react";
import { AppShell } from "../../../components/shell";
import { LanguageProvider } from "../../../components/language-provider";

export default function LocaleLayout({ children, params }) {
  const { locale } = params;

  React.useEffect(() => {
    try {
      window.localStorage.setItem("syntexa_locale", locale);
    } catch {}
  }, [locale]);

  return React.createElement(
    LanguageProvider,
    { initialLocale: locale },
    React.createElement(AppShell, null, children)
  );
}
