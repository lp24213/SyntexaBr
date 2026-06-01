"use client";

import React from "react";
import { AppShell } from "../../../components/shell";

export default function LocaleLayout({ children, params }) {
  const { locale } = params;

  // Armazenar locale no localStorage
  React.useEffect(() => {
    try {
      window.localStorage.setItem("syntexa_locale", locale);
    } catch {}
  }, [locale]);

  return React.createElement(AppShell, null, children);
}
