"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { getClientLocale, normalizeLocale } from "../lib/i18n";

const LanguageContext = createContext({
  locale: "pt-BR",
  setLocale: () => {},
});

export function LanguageProvider({ children, initialLocale }) {
  const [locale, setLocaleState] = useState(() => {
    if (initialLocale) return normalizeLocale(initialLocale);
    if (typeof window !== "undefined") {
      return getClientLocale();
    }
    return "pt-BR";
  });

  useEffect(() => {
    if (initialLocale) {
      setLocaleState(normalizeLocale(initialLocale));
    }
  }, [initialLocale]);

  const setLocale = (newLocale) => {
    const normalized = normalizeLocale(newLocale);
    try {
      window.localStorage.setItem("syntexa_locale", normalized);
      document.cookie = `syntexa_locale=${normalized}; path=/; max-age=${60*60*24*365}; SameSite=Lax`;
    } catch {}
    setLocaleState(normalized);
  };

  useEffect(() => {
    if (typeof window === "undefined") return;

    const handleStorageChange = (e) => {
      if (e.key === "syntexa_locale") {
        const newLocale = e.newValue || initialLocale || "pt-BR";
        setLocaleState(normalizeLocale(newLocale));
      }
    };

    window.addEventListener("storage", handleStorageChange);

    return () => {
      window.removeEventListener("storage", handleStorageChange);
    };
  }, [initialLocale]);

  return (
    <LanguageContext.Provider value={{ locale, setLocale }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used within LanguageProvider");
  }
  return context;
}
