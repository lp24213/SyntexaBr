"use client";

import React from "react";
import { CookieConsent } from "./cookie-consent";
import { LanguageProvider } from "./language-provider";
import { getClientLocale } from "../lib/i18n";

export function AppWrapper(props) {
  const { children } = props;
  const [initialLocale, setInitialLocale] = React.useState("pt-BR");

  React.useEffect(() => {
    setInitialLocale(getClientLocale());
  }, []);
  
  return React.createElement(
    LanguageProvider,
    { initialLocale },
    React.createElement(
      React.Fragment,
      null,
      React.createElement("div", { id: "root", className: "syntexa-os-shell relative z-10 min-h-[100dvh] w-full overflow-x-hidden text-[#0f172a] bg-white" }, children),
      React.createElement(CookieConsent, null)
    )
  );
}
