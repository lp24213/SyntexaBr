import React from "react";
import PlanosPage from "../../../../app/planos/page";
import { LanguageProvider } from "../../../../components/language-provider";

export async function generateStaticParams() {
  return [
    { locale: "pt-BR" },
    { locale: "en-US" },
    { locale: "es-ES" },
    { locale: "zh-CN" },
  ];
}

export default function LocalePlansPage({ params }) {
  const { locale } = params;
  return React.createElement(
    LanguageProvider,
    { initialLocale: locale },
    React.createElement(PlanosPage)
  );
}
