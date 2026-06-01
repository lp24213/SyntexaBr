import React from "react";

export default function LocaleHomePage({ params }) {
  const { locale } = params;
  
  return React.createElement(
    "div",
    { className: "text-center py-20" },
    React.createElement("h1", { className: "text-4xl font-bold mb-4" }, "Syntexa"),
    React.createElement("p", { className: "text-lg text-[#64748b]" }, "Infraestrutura de IA Soberana"),
    React.createElement(
      "a",
      { href: `/i18n/${locale}/chat`, className: "inline-block mt-8 bg-[#1a1c1e] text-white px-8 py-3 rounded-lg hover:bg-[#2a2c2e] transition-colors" },
      "Abrir Console"
    )
  );
}

export async function generateStaticParams() {
  return [
    { locale: 'pt-BR' },
    { locale: 'en-US' },
    { locale: 'es-ES' },
    { locale: 'zh-CN' }
  ];
}
