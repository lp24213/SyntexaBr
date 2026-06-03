import React from "react";
import HomePage from "../../page";
import { LanguageProvider } from "../../../components/language-provider";

export async function generateStaticParams() {
  return [
    { locale: 'pt-BR' },
    { locale: 'en-US' },
    { locale: 'es-ES' },
    { locale: 'zh-CN' }
  ];
}

export default function LocaleHomePage({ params }) {
  const { locale } = params;

  return React.createElement(
    LanguageProvider,
    { initialLocale: locale },
    React.createElement(HomePage)
  );
}
